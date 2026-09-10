"""OKF reading and strict resume-authoring profile validation.

The reader preserves unknown metadata. The authoring profile applies the
additional attribution and approved-ontology requirements of this project.
"""

from datetime import datetime
import json
from pathlib import Path
import re
from urllib.parse import unquote, urljoin, urlsplit
import xml.etree.ElementTree as ET

import yaml

from pins import VENDOR, validate_pins
from workspace import exclusive_write, identifier, load_workspace

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
PROPERTY_TYPES = {RDF + "Property", OWL + "ObjectProperty", OWL + "DatatypeProperty", OWL + "AnnotationProperty"}
FORMAT_FIELDS = {
    "type", "title", "description", "resource", "tags", "sources", "generated", "verified",
    "usage_window", "status", "stale_after", "runtime", "parameters", "computation", "executor", "attester",
}
ASSERTION_TYPES = {"Assertion", "Derived assertion", "Requirement"}


class UniqueSafeLoader(yaml.SafeLoader):
    """Reject ambiguous duplicate keys instead of silently discarding data."""


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str) or key in result:
            raise ValueError("YAML mapping keys must be unique strings")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def read_concept(text):
    """Read any OKF concept without imposing the resume authoring profile."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("Concept must start with YAML frontmatter")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise ValueError("Unclosed YAML frontmatter")
    try:
        metadata = yaml.load("".join(lines[1:end]), Loader=UniqueSafeLoader)
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid YAML: {error}") from error
    if not isinstance(metadata, dict) or not isinstance(metadata.get("type"), str) or not metadata["type"].strip():
        raise ValueError("OKF concepts require a nonempty type string")
    return metadata, "".join(lines[end + 1:])


def timestamp(value):
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("Timestamps require ISO 8601 datetimes with explicit timezone") from error
    if parsed.tzinfo is None:
        raise ValueError("Timestamps require an explicit timezone")
    return parsed


def actor(value):
    if not isinstance(value, str) or not re.fullmatch(r"(?:human:[^\s:]+|process:[^\s:]+|[^\s/:]+/[^\s/]+)", value):
        raise ValueError("Actor must be human:<id>, process:<id>, or <producer>/<version>")
    return value


def verification_events(metadata):
    events = metadata.get("verified", [])
    if isinstance(events, dict):
        events = [events]
    if not isinstance(events, list):
        raise ValueError("verified must be an event or event list")
    for event in events:
        if not isinstance(event, dict) or set(event) != {"by", "at"}:
            raise ValueError("Each verification event requires only by and at")
        actor(event["by"])
        timestamp(event["at"])
    return events


def trust_tier(metadata):
    events = verification_events(metadata)
    if any(event["by"].startswith("human:") for event in events):
        return "human-reviewed"
    return "machine-confirmed" if events else "unverified"


def properties():
    """Only definitions in the approved namespaces; never follow imports."""
    manifest = validate_pins()
    catalog = {}
    for artifact in manifest["artifacts"]:
        namespace = artifact["namespace"]
        if namespace is None:
            continue
        path = VENDOR / artifact["file"]
        if artifact["id"] == "schemaorg":
            document = json.loads(path.read_text(encoding="utf-8"))
            context = document["@context"]

            def expand(value):
                prefix, separator, suffix = value.partition(":")
                return context[prefix] + suffix if separator and isinstance(context.get(prefix), str) else value

            for item in document["@graph"]:
                types = item.get("@type", [])
                types = types if isinstance(types, list) else [types]
                uri = expand(item["@id"])
                if uri.startswith(namespace) and RDF + "Property" in {expand(t) for t in types}:
                    catalog[uri] = item
        else:
            tree = ET.parse(path)
            base = tree.getroot().get("{http://www.w3.org/XML/1998/namespace}base", artifact["source"])
            for item in tree.getroot():
                reference = item.get("{" + RDF + "}about")
                if reference is None:
                    continue
                uri = urljoin(base, reference)
                types = {item.tag.removeprefix("{").replace("}", "")}
                types.update(child.get("{" + RDF + "}resource", "") for child in item.findall("{" + RDF + "}type"))
                if uri.startswith(namespace) and types & PROPERTY_TYPES:
                    catalog[uri] = ET.tostring(item, encoding="unicode")
    return catalog


def sections(body):
    result = {}
    current = None
    for line in body.splitlines():
        if line.startswith("# "):
            current = line[2:].strip()
            if current in result:
                raise ValueError(f"Duplicate body section: {current}")
            result[current] = []
        elif current:
            result[current].append(line)
    return {key: "\n".join(value).strip() for key, value in result.items()}


def validate_profile(metadata, body, catalog=None):
    catalog = properties() if catalog is None else catalog
    unknown = set(metadata) - FORMAT_FIELDS - set(catalog)
    if unknown:
        raise ValueError(f"Unapproved metadata properties: {', '.join(sorted(unknown))}; preserve modeling gaps in narrative")
    for key in ("type", "title"):
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            raise ValueError(f"Resume authoring requires nonempty {key}")
    generated = metadata.get("generated")
    if not isinstance(generated, dict) or set(generated) != {"by", "at"}:
        raise ValueError("Resume authoring requires generated.by and generated.at")
    actor(generated["by"])
    timestamp(generated["at"])
    verification_events(metadata)
    if metadata.get("status", "stable") not in {"draft", "stable", "deprecated"}:
        raise ValueError("Invalid OKF lifecycle status")
    if "stale_after" in metadata:
        timestamp(metadata["stale_after"])
    sources = metadata.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("Resume authoring requires at least one attributed source")
    source_ids = set()
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get("resource"), str) or not source["resource"].strip():
            raise ValueError("Every source requires a nonempty resource")
        if set(source) - {"id", "resource", "title", "author", "usage_count", "last_modified", "usage_window"}:
            raise ValueError("Unknown source metadata; use defined OKF fields and narrative evidence notes")
        if "author" in source:
            actor(source["author"])
        if "last_modified" in source:
            timestamp(source["last_modified"])
        source_id = source.get("id")
        identifier(source_id)
        if source_id in source_ids:
            raise ValueError("Source ids must be unique")
        source_ids.add(source_id)
    used_ids = set(re.findall(r"\[\^([^\]]+)\](?!:)", body))
    defined_ids = set(re.findall(r"^\[\^([^\]]+)\]:", body, re.MULTILINE))
    if not used_ids or not used_ids <= source_ids or not used_ids <= defined_ids:
        raise ValueError("Cite evidence with footnotes matching source ids and footnote definitions")
    content = sections(body)
    required = {"Evidence assessment"}
    if metadata["type"] in ASSERTION_TYPES:
        required |= {"Claim", "Subject", "Role or event", "Time", "Measurement"}
    if metadata["type"] == "Derived assertion":
        required.add("Derivation")
    if metadata["type"] == "Requirement":
        required.add("Requirement basis")
    missing = {name for name in required if not content.get(name)}
    if missing:
        raise ValueError("Missing narrative sections: " + ", ".join(sorted(missing)))
    if metadata["type"] in ASSERTION_TYPES and not re.search(r"\[[^\]]+\]\([^)]+\.md(?:#[^)]*)?\)", content["Subject"]):
        raise ValueError("Assertions must link to their subject concept")
    if metadata["type"] == "Requirement" and not content["Requirement basis"].startswith(("Explicit:", "Inferred:")):
        raise ValueError("Requirement basis must start with Explicit: or Inferred: and explain the evidence")
    return trust_tier(metadata)


def bundle_path(workspace, kind, name):
    root = load_workspace(workspace)
    if kind not in {"applicant", "position"}:
        raise ValueError("Invalid bundle kind")
    bundle = root / (kind + "s") / identifier(name)
    if bundle.is_symlink() or not bundle.is_dir():
        raise ValueError("Bundle does not exist or is a symlink")
    return bundle


def local_link(bundle, document, target):
    """Resolve OKF paths without reading outside their bundle."""
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    target_path = unquote(parsed.path)
    path = bundle / target_path.lstrip("/") if target_path.startswith("/") else document.parent / target_path
    resolved = path.resolve()
    if resolved != bundle and bundle not in resolved.parents:
        raise ValueError(f"Concept link escapes its bundle: {target}")
    if any(p.is_symlink() for p in (path, *path.parents) if p != bundle and bundle in p.parents):
        raise ValueError(f"Concept link uses a symlink: {target}")
    return resolved


def validate_reserved(bundle, path, text):
    if path.name == "index.md" and text.startswith("---\n"):
        if path.parent != bundle:
            raise ValueError("Only the bundle-root index may have frontmatter")
        metadata, _ = read_concept(text.replace("---\n", "---\ntype: Index\n", 1))
        if set(metadata) != {"type", "okf_version"} or str(metadata["okf_version"]) != "0.2":
            raise ValueError("Resume bundle index must declare only okf_version: '0.2'")
    elif path.name == "log.md":
        if text.startswith("---\n"):
            raise ValueError("OKF log files must not have frontmatter")
        for heading in re.findall(r"^## (.+)$", text, re.MULTILINE):
            try:
                datetime.strptime(heading, "%Y-%m-%d")
            except ValueError as error:
                raise ValueError("Log date headings must use YYYY-MM-DD") from error
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", heading):
                raise ValueError("Log date headings must use YYYY-MM-DD")


def validate_bundle(workspace, kind, name):
    bundle = bundle_path(workspace, kind, name)
    catalog = properties()
    report = []
    for path in sorted(bundle.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Bundle contains a symlink: {path.name}")
        if not path.is_file() or path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        if path.name in {"index.md", "log.md"}:
            validate_reserved(bundle, path, text)
            continue
        metadata, body = read_concept(text)
        tier = validate_profile(metadata, body, catalog)
        broken = []
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", body):
            resolved = local_link(bundle, path, target)
            if resolved is not None and not resolved.exists():
                broken.append(target)
        report.append({"concept": path.relative_to(bundle).as_posix(), "trust": tier, "broken_links": broken})
    return report


def add_concept(workspace, kind, name, concept_id, text):
    bundle = bundle_path(workspace, kind, name)
    concept_id = identifier(concept_id)
    if concept_id in {"index", "log"}:
        raise ValueError("index and log are reserved OKF filenames")
    metadata, body = read_concept(text)
    validate_profile(metadata, body)
    path = bundle / (concept_id + ".md")
    for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", body):
        local_link(bundle, path, target)
    exclusive_write(path, text)
    return path
