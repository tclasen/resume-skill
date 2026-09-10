"""Offline validation of the reviewed format and ontology artifacts."""

import hashlib
import json
from pathlib import Path
import re
import sys

VENDOR = Path(__file__).resolve().parents[1] / "references" / "vendor"
EXPECTED = {
    "okf": ("0.2", None),
    "schemaorg": ("30.0", "https://schema.org/"),
    "prov": ("2013-04-30", "http://www.w3.org/ns/prov#"),
    "skos": ("2009-08-18", "http://www.w3.org/2004/02/skos/core#"),
}


def validate_pins(vendor=VENDOR):
    """Return the manifest after validation; never fetch or repair artifacts."""
    vendor = Path(vendor).resolve()
    manifest = json.loads((vendor / "pins.json").read_text(encoding="utf-8"))
    if manifest.get("manifest_version") != 1:
        raise ValueError("Unsupported pin manifest version")
    artifacts = manifest["artifacts"]
    if len(artifacts) != len(EXPECTED) or {a["id"] for a in artifacts} != set(EXPECTED):
        raise ValueError("Exactly the four approved artifact pins are required")
    for artifact in artifacts:
        name = artifact["id"]
        if (artifact["version"], artifact["namespace"]) != EXPECTED[name]:
            raise ValueError(f"Unapproved version or namespace: {name}")
        revision = artifact["revision"]
        pattern = r"[0-9a-f]{40}" if name in {"okf", "schemaorg"} else re.escape(artifact["version"])
        if not re.fullmatch(pattern, revision):
            raise ValueError(f"Missing immutable revision or dated publication: {name}")
        if not artifact["source"].startswith("https://"):
            raise ValueError(f"Missing HTTPS source: {name}")
        filename = artifact["file"]
        path = (vendor / filename).resolve()
        if Path(filename).name != filename or path.parent != vendor:
            raise ValueError(f"Artifact must be a local file: {name}")
        expected = artifact["sha256"]
        if not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError(f"Invalid checksum: {name}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Checksum mismatch: {name}; stop authoring and restore reviewed pins")
    return manifest


if __name__ == "__main__":
    try:
        validate_pins()
    except (OSError, ValueError, KeyError, TypeError) as error:
        sys.exit(f"Pin validation failed: {error}")
    print("OK: all four pinned artifacts match their reviewed checksums")
