"""Validate reference-only assessment plans and write separate evidence reports.

Review decisions are operational inputs, not new semantic graph properties or
proof of truth. Their authors must check the cited source material.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import quote

from knowledge import (actor, bundle_path, local_link, read_concept, sections,
                       timestamp, trust_tier, validate_bundle, verification_events)
from workspace import exclusive_write, identifier, load_workspace

OUTCOMES = {"supported", "partial", "missing-evidence", "demonstrated-gap"}
HEADINGS = {"Summary", "Experience", "Education", "Skills", "Certifications", "Projects",
            "Publications", "Awards", "Volunteering", "Training", "Languages"}


def fields(value, names, label):
    if not isinstance(value, dict) or set(value) != set(names.split()):
        raise ValueError(f"{label} requires exactly these fields: {names}")


def nonempty(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonempty text")
    return value


def text_line(value, label):
    nonempty(value, label)
    if any(ord(char) < 32 for char in value) or "\u2028" in value or "\u2029" in value:
        raise ValueError(f"{label} must be one plain text line")
    return value


def digest(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(workspace, kind, name):
    bundle = bundle_path(workspace, kind, name)
    validate_bundle(workspace, kind, name)
    files = {}
    for path in sorted(bundle.rglob("*")):
        if path.is_symlink():
            raise ValueError("Snapshots cannot contain symlinks")
        if path.is_file():
            files[path.relative_to(bundle).as_posix()] = digest(path.read_bytes())
    return {"sha256": digest(json.dumps(files, sort_keys=True).encode()), "files": files}


def load_plan(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate plan field: {key}")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique)


def validate_plan(workspace, plan, now=None):
    fields(plan, "version applicant position applicant_snapshot position_snapshot generated reviews requirements resume", "Plan")
    if type(plan["version"]) is not int or plan["version"] != 1:
        raise ValueError("Unsupported assessment plan version")
    root = load_workspace(workspace)
    now = now or datetime.now(timezone.utc)
    fields(plan["generated"], "by at", "Plan authorship")
    actor(plan["generated"]["by"])
    timestamp(plan["generated"]["at"])
    bundles = {}
    for kind in ("applicant", "position"):
        name = identifier(plan[kind])
        bundles[kind] = bundle_path(root, kind, name)
        if snapshot(root, kind, name)["sha256"] != plan[kind + "_snapshot"]:
            raise ValueError(f"Stale {kind} snapshot; reread evidence and rebuild the assessment")
    concepts = {}
    for kind, bundle in bundles.items():
        for path in bundle.rglob("*.md"):
            if path.name not in {"index.md", "log.md"}:
                metadata, body = read_concept(path.read_text(encoding="utf-8"))
                ref = path.relative_to(root).as_posix()
                concepts[ref] = {"metadata": metadata, "body": body, "kind": kind, "path": path,
                                 "sha256": digest(path.read_bytes())}

    def concept(ref, kind=None):
        if not isinstance(ref, str) or ref not in concepts:
            raise ValueError(f"Unknown canonical assertion reference: {ref}")
        item = concepts[ref]
        if kind and item["kind"] != kind:
            raise ValueError(f"Evidence belongs to the wrong bundle: {ref}")
        return item

    def current(item):
        metadata = item["metadata"]
        if metadata.get("status", "stable") != "stable":
            raise ValueError("Draft or deprecated claims cannot establish qualification or appear on resumes")
        if "stale_after" in metadata and timestamp(metadata["stale_after"]) <= now:
            raise ValueError("Stale claims require a fresh evidence assessment")

    reviews = plan["reviews"]
    if not isinstance(reviews, dict):
        raise ValueError("reviews must map canonical applicant assertion paths to review decisions")
    for ref, review in reviews.items():
        item = concept(ref, "applicant")
        fields(review, "sha256 disputed basis by at evidence rationale", "Review")
        if review["sha256"] != item["sha256"]:
            raise ValueError(f"Review no longer matches assertion content: {ref}")
        if type(review["disputed"]) is not bool:
            raise ValueError("Review disputed must be a boolean")
        if review["basis"] not in {"unverified", "applicant-attested", "independent"}:
            raise ValueError("Review basis must distinguish unverified, applicant-attested, and independent")
        actor(review["by"])
        reviewed_at = timestamp(review["at"])
        nonempty(review["rationale"], "Review rationale")
        evidence = review["evidence"]
        source_ids = {source["id"] for source in item["metadata"]["sources"]}
        if not isinstance(evidence, list) or not all(isinstance(e, str) and e in source_ids for e in evidence):
            raise ValueError("Review evidence must reference source ids on the canonical concept")
        if review["basis"] != "unverified":
            if not evidence:
                raise ValueError("Attestation/corroboration requires a recorded source basis")
            events = verification_events(item["metadata"])
            if not any(e["by"] == review["by"] and timestamp(e["at"]) == reviewed_at for e in events):
                raise ValueError("Review must match an actual OKF verification event")
            if reviewed_at < timestamp(item["metadata"]["generated"]["at"]):
                raise ValueError("Review predates the current claim's authorship")
            if review["basis"] == "applicant-attested" and not review["by"].startswith("human:"):
                raise ValueError("Applicant attestation must identify a human applicant")

    checked = set()

    def eligible(ref, visiting=None):
        item = concept(ref, "applicant")
        if ref in checked:
            return
        visiting = set() if visiting is None else visiting
        if ref in visiting:
            raise ValueError("Cyclic derivation cannot establish independent support")
        current(item)
        if item["metadata"]["type"] not in {"Assertion", "Derived assertion"}:
            raise ValueError("Resume and qualification evidence must reference atomic applicant assertions")
        review = reviews.get(ref)
        if not review or review["disputed"] or review["basis"] == "unverified":
            raise ValueError(f"Disputed or unconfirmed claim is ineligible: {ref}")
        bundle = bundles["applicant"]
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", item["body"]):
            resolved = local_link(bundle, item["path"], target)
            if resolved is not None and not resolved.exists():
                raise ValueError(f"Resolve broken context links before using {ref}")
        if item["metadata"]["type"] == "Derived assertion":
            derivation = sections(item["body"])["Derivation"]
            inputs = []
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", derivation):
                path = local_link(bundle, item["path"], target)
                if path is not None and path.suffix == ".md":
                    inputs.append(path.relative_to(root).as_posix())
            if not inputs:
                raise ValueError("Derived assertion must link its canonical assertion inputs")
            for dependency in inputs:
                eligible(dependency, visiting | {ref})
        checked.add(ref)

    expected = {ref for ref, item in concepts.items() if item["kind"] == "position"
                and item["metadata"]["type"] == "Requirement"
                and item["metadata"].get("status", "stable") != "deprecated"}
    if not isinstance(plan["requirements"], list):
        raise ValueError("requirements must be a list")
    seen = set()
    for finding in plan["requirements"]:
        fields(finding, "requirement outcome evidence rationale follow_up", "Requirement finding")
        ref = finding["requirement"]
        if not isinstance(ref, str) or ref not in expected or ref in seen:
            raise ValueError("Findings must cover each current requirement exactly once")
        seen.add(ref)
        current(concepts[ref])
        if finding["outcome"] not in OUTCOMES:
            raise ValueError("Invalid qualitative outcome; numeric scoring is not supported")
        nonempty(finding["rationale"], "Requirement reasoning")
        if not isinstance(finding["follow_up"], str):
            raise ValueError("follow_up must be text")
        evidence = finding["evidence"]
        if not isinstance(evidence, list):
            raise ValueError("Finding evidence must be canonical assertion references")
        if finding["outcome"] == "missing-evidence":
            if evidence or not finding["follow_up"].strip():
                raise ValueError("Missing evidence has no qualifying facts and requires a follow-up question")
        elif not evidence:
            raise ValueError("Support, partial support, and demonstrated gaps require evidence")
        if finding["outcome"] == "partial" and not finding["follow_up"].strip():
            raise ValueError("Partial support requires a follow-up question")
        for evidence_ref in evidence:
            eligible(evidence_ref)
    if seen != expected:
        raise ValueError("Assessment omits current position requirements")

    resume = plan["resume"]
    if resume is not None:
        fields(resume, "name contact sections", "Resume")

        def check_line(line):
            fields(line, "text evidence", "Resume line")
            text_line(line["text"], "Resume text")
            if not isinstance(line["evidence"], list) or not line["evidence"]:
                raise ValueError("Every personal resume line needs canonical assertion evidence")
            for ref in line["evidence"]:
                eligible(ref)

        check_line(resume["name"])
        if not isinstance(resume["contact"], list) or not isinstance(resume["sections"], list) or not resume["sections"]:
            raise ValueError("Resume requires contact and nonempty sections lists")
        for line in resume["contact"]:
            check_line(line)
        for section in resume["sections"]:
            fields(section, "heading items", "Resume section")
            if section["heading"] not in HEADINGS:
                raise ValueError("Use a standard resume section heading; factual headings belong in evidence-backed items")
            if not isinstance(section["items"], list) or not section["items"]:
                raise ValueError("Resume sections must contain items")
            for line in section["items"]:
                check_line(line)
    for kind in ("applicant", "position"):
        if snapshot(root, kind, plan[kind])["sha256"] != plan[kind + "_snapshot"]:
            raise ValueError("Evidence changed during validation; retry after reviewing the change")
    return concepts


def markdown(value):
    return re.sub(r"([\\`*_{}\[\]<>()#+.!|~-])", r"\\\1", str(value))


def code_span(value):
    runs = re.findall(r"`+", str(value))
    fence = "`" * (1 + max((len(run) for run in runs), default=0))
    return f"{fence} {value} {fence}"


def evidence_report(plan, concepts, link_prefix="../"):
    def link(ref):
        return f"[{markdown(ref)}]({link_prefix}{quote(ref, safe='/')})"

    lines = ["# Qualification and resume evidence report", "",
             f"Applicant bundle: `{plan['applicant']}`; position bundle: `{plan['position']}`.", "",
             f"Prepared by {markdown(plan['generated']['by'])} at {markdown(plan['generated']['at'])}.", "",
             "This report records evidence judgments; it is not a numeric ranking or a guarantee of qualification.", "",
             "## Requirement assessment", ""]
    for finding in plan["requirements"]:
        ref = finding["requirement"]
        item = concepts[ref]
        basis = sections(item["body"])["Requirement basis"]
        lines += [f"### {markdown(item['metadata']['title'])}", "",
                  f"Canonical requirement: {link(ref)}", "",
                  f"Basis: {markdown(basis)}", "",
                  f"Finding: **{finding['outcome']}**", "", markdown(finding["rationale"]), ""]
        for evidence in finding["evidence"]:
            lines += [f"- {link(evidence)}"]
        lines += ["", f"Follow-up: {markdown(finding['follow_up']) or 'None recorded.'}", ""]
    if plan["resume"] is not None:
        resume = plan["resume"]
        lines += ["## Resume claim trace", ""]
        entries = [resume["name"], *resume["contact"]]
        entries += [line for section in resume["sections"] for line in section["items"]]
        for line in entries:
            lines += [f"### {markdown(line['text'])}", ""]
            lines += [f"- {link(ref)}" for ref in line["evidence"]]
            lines += [""]
    lines += ["## Source and review ledger", ""]
    selected = set(plan["reviews"]) | {f["requirement"] for f in plan["requirements"]}
    for ref in sorted(selected):
        item = concepts[ref]
        lines += [f"### {link(ref)}", "", f"SHA-256: `{item['sha256']}`", "",
                  f"OKF verification tier: **{trust_tier(item['metadata'])}**", "",
                  f"Authorship: {markdown(json.dumps(item['metadata']['generated'], default=str))}", "",
                  f"Verification events: {markdown(json.dumps(item['metadata'].get('verified', []), default=str))}", ""]
        if ref in plan["reviews"]:
            review = plan["reviews"][ref]
            lines += [f"Evidence basis: **{review['basis']}**; disputed: **{review['disputed']}**.", "",
                      f"Review: {markdown(review['by'])} at {markdown(review['at'])}.", "",
                      f"Review source IDs: {markdown(', '.join(review['evidence']))}", "",
                      markdown(review["rationale"]), ""]
        lines += ["Recorded evidence assessment:", "", markdown(sections(item["body"])["Evidence assessment"]), ""]
        if item["metadata"]["type"] == "Derived assertion":
            lines += ["Derivation:", "", markdown(sections(item["body"])["Derivation"]), ""]
        for source in item["metadata"]["sources"]:
            lines += [f"- {markdown(source['id'])}: {markdown(source.get('title', ''))} — {code_span(source['resource'])}"]
        lines += [""]
    lines += ["## Reproducibility", "", f"Applicant snapshot: `{plan['applicant_snapshot']}`", "",
              f"Position snapshot: `{plan['position_snapshot']}`", "",
              "Refresh source research and review after evidence or requirements change. Review decisions do not modify canonical verification.", ""]
    return "\n".join(lines)


def assess(workspace, plan, name):
    root = load_workspace(workspace)
    name = identifier(name)
    concepts = validate_plan(root, plan)
    report = root / "analyses" / f"{name}.md"
    saved_plan = root / "analyses" / f"{name}.json"
    if report.exists() or report.is_symlink() or saved_plan.exists() or saved_plan.is_symlink():
        raise ValueError("Analysis id already exists; use a new id to preserve history")
    exclusive_write(saved_plan, json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    try:
        exclusive_write(report, evidence_report(plan, concepts))
    except Exception:
        saved_plan.unlink()
        raise
    return report
