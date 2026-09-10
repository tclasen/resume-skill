from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/resume/scripts"))
from assessment import assess, snapshot, validate_plan
from workspace import create_bundle, init_workspace


def document(kind, title, claim, subject="person", verified=True):
    metadata = {"type": kind, "title": title,
                "generated": {"by": "synthetic-test/1", "at": "2026-01-01T00:00:00Z"},
                "sources": [{"id": "interview", "resource": "https://example.invalid/synthetic-interview"}]}
    if verified:
        metadata["verified"] = {"by": "human:synthetic-applicant", "at": "2026-01-02T00:00:00Z"}
    body = f"# Claim\n{claim}[^interview]\n\n# Subject\n[Subject](/{subject}.md)\n\n"
    body += "# Role or event\nNot applicable to this synthetic claim.\n\n# Time\nAs of January 2026.\n\n"
    body += "# Measurement\nNo quantitative claim.\n\n# Evidence assessment\n"
    body += "Synthetic applicant confirmed this claim on 2026-01-02; no dispute or independent corroboration.\n\n"
    if kind == "Requirement":
        body += "# Requirement basis\nExplicit: the synthetic posting states this requirement.[^interview]\n\n"
    return "---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n" + body + "[^interview]: Synthetic test evidence only.\n"


def make_workspace(base):
    root = init_workspace(Path(base).resolve() / "private")
    applicant = create_bundle(root, "applicant", "solo")
    position = create_bundle(root, "position", "engineer")
    (applicant / "person.md").write_text(document("Person", "Synthetic person", "Test identity"))
    claims = {"name": "Alex Example", "skill": "Built a reporting service during an internship."}
    for name, claim in claims.items():
        (applicant / f"{name}.md").write_text(document("Assertion", name, claim))
    (position / "person.md").write_text(document("JobPosting", "Synthetic posting", "Test posting"))
    (position / "reporting.md").write_text(document("Requirement", "Reporting experience", "Reporting experience required"))
    (position / "language.md").write_text(document("Requirement", "Second language", "A second language is preferred"))
    plan = {"version": 1, "applicant": "solo", "position": "engineer",
            "applicant_snapshot": snapshot(root, "applicant", "solo")["sha256"],
            "position_snapshot": snapshot(root, "position", "engineer")["sha256"],
            "generated": {"by": "synthetic-test/1", "at": "2026-01-03T00:00:00Z"},
            "reviews": {}, "requirements": [
                {"requirement": "positions/engineer/reporting.md", "outcome": "supported",
                 "evidence": ["applicants/solo/skill.md"], "rationale": "The internship provides direct relevant experience.", "follow_up": ""},
                {"requirement": "positions/engineer/language.md", "outcome": "missing-evidence",
                 "evidence": [], "rationale": "No language evidence has been supplied; ability is unknown.",
                 "follow_up": "Which languages do you use, and at what level?"}],
            "resume": {"name": {"text": claims["name"], "evidence": ["applicants/solo/name.md"]},
                       "contact": [], "sections": [{"heading": "Experience", "items": [
                           {"text": claims["skill"], "evidence": ["applicants/solo/skill.md"]}]}]}}
    for name in claims:
        ref = f"applicants/solo/{name}.md"
        plan["reviews"][ref] = {"sha256": hashlib.sha256((root / ref).read_bytes()).hexdigest(),
                                "disputed": False, "basis": "applicant-attested", "by": "human:synthetic-applicant",
                                "at": "2026-01-02T00:00:00Z", "evidence": ["interview"],
                                "rationale": "Applicant explicitly confirmed the personal claim in the recorded interview."}
    return root, plan


class AssessmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root, self.plan = make_workspace(self.temp.name)

    def refresh(self, ref):
        self.plan["applicant_snapshot"] = snapshot(self.root, "applicant", "solo")["sha256"]
        self.plan["reviews"][ref]["sha256"] = hashlib.sha256((self.root / ref).read_bytes()).hexdigest()

    def test_report_covers_requirements_and_traces_resume(self):
        report = assess(self.root, self.plan, "first")
        text = report.read_text()
        for expected in ("supported", "missing-evidence", "Explicit:", "applicant-attested", "human-reviewed",
                         "applicants/solo/skill.md", "synthetic-interview", "Resume claim trace"):
            self.assertIn(expected, text)
        self.assertTrue(report.with_suffix(".json").exists())
        with self.assertRaisesRegex(ValueError, "already exists"):
            assess(self.root, self.plan, "first")

    def test_missing_evidence_is_not_a_gap(self):
        self.plan["requirements"][1]["outcome"] = "demonstrated-gap"
        with self.assertRaisesRegex(ValueError, "require evidence"):
            validate_plan(self.root, self.plan)

    def test_complete_coverage_and_no_scores(self):
        for mutate in (lambda p: p["requirements"].pop(),
                       lambda p: p["requirements"].append(p["requirements"][0]),
                       lambda p: p["requirements"][0].update(outcome=0.9),
                       lambda p: p["requirements"][0].update(score=90)):
            plan = deepcopy(self.plan)
            mutate(plan)
            with self.assertRaises(ValueError):
                validate_plan(self.root, plan)

    def test_snapshot_detects_changed_or_new_evidence(self):
        (self.root / "applicants/solo/person.md").write_text(document("Person", "Changed", "Changed context"))
        with self.assertRaisesRegex(ValueError, "Stale applicant snapshot"):
            validate_plan(self.root, self.plan)

    def test_ineligible_claims_and_review_identity(self):
        for changes in ({"disputed": True}, {"basis": "unverified"}, {"by": "human:someone-else"},
                        {"evidence": []}, {"sha256": "0" * 64}):
            plan = deepcopy(self.plan)
            plan["reviews"]["applicants/solo/skill.md"].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_plan(self.root, plan)

    def test_deprecated_and_stale_claims_are_excluded(self):
        ref = "applicants/solo/skill.md"
        original = (self.root / ref).read_text()
        for field in ("status: deprecated", "status: draft", 'stale_after: "2026-01-04T00:00:00Z"'):
            (self.root / ref).write_text(original.replace("---\n", "---\n" + field + "\n", 1))
            self.refresh(ref)
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_plan(self.root, self.plan, now=datetime(2026, 9, 1, tzinfo=timezone.utc))

    def test_wrong_person_and_unsupported_resume_line(self):
        self.plan["resume"]["name"]["evidence"] = ["applicants/another/name.md"]
        with self.assertRaisesRegex(ValueError, "Unknown canonical"):
            validate_plan(self.root, self.plan)
        self.plan["resume"]["name"]["evidence"] = []
        with self.assertRaisesRegex(ValueError, "Every personal resume line"):
            validate_plan(self.root, self.plan)

    def test_derivation_does_not_inherit_review(self):
        ref = "applicants/solo/skill.md"
        text = (self.root / ref).read_text().replace("type: Assertion", "type: Derived assertion")
        text += "\n# Derivation\nBased on [input](/name.md); synthetic method and assumptions.\n"
        (self.root / ref).write_text(text)
        self.refresh(ref)
        del self.plan["reviews"][ref]
        with self.assertRaisesRegex(ValueError, "unconfirmed"):
            validate_plan(self.root, self.plan)

    def test_disputed_derived_input_excluded(self):
        ref = "applicants/solo/skill.md"
        text = (self.root / ref).read_text().replace("type: Assertion", "type: Derived assertion")
        text += "\n# Derivation\nBased on [input](/name.md); synthetic method and assumptions.\n"
        (self.root / ref).write_text(text)
        self.refresh(ref)
        self.plan["reviews"]["applicants/solo/name.md"]["disputed"] = True
        with self.assertRaisesRegex(ValueError, "Disputed"):
            validate_plan(self.root, self.plan)


if __name__ == "__main__":
    unittest.main()
