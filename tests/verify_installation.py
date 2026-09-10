"""Verify an isolated `skills add --all` installation against source assets.

Usage: python tests/verify_installation.py <temporary-install-root> --expected-paths 55
Run the actual CLI first; this checks its output, not a simulated agent registry.
"""

import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

import yaml


def verify(root, expected_paths):
    source = Path(__file__).resolve().parents[1] / "skills/resume"
    _, original_meta, original_body = (source / "SKILL.md").read_text().split("---", 2)
    metadata = yaml.safe_load(original_meta)
    files = {p.relative_to(source): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in source.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.name != "SKILL.md"}
    installs = sorted(Path(root).rglob("SKILL.md"))
    if len(installs) != expected_paths:
        raise ValueError(f"Expected {expected_paths} installation paths, found {len(installs)}")
    for skill in installs:
        _, installed_meta, installed_body = skill.read_text().split("---", 2)
        adapted = yaml.safe_load(installed_meta)
        # The official Eve adapter removes name/compatibility and reformats
        # frontmatter; substantive instructions and description must survive.
        if installed_body.strip() != original_body.strip() or adapted["description"] != metadata["description"]:
            raise ValueError(f"Installed instructions differ: {skill}")
        for relative, checksum in files.items():
            if hashlib.sha256((skill.parent / relative).read_bytes()).hexdigest() != checksum:
                raise ValueError(f"Missing or changed runtime asset: {skill.parent / relative}")
        subprocess.run([sys.executable, "-B", str(skill.parent / "scripts/resume.py"), "pins"],
                       check=True, capture_output=True, text=True)
    print(f"Verified all assets, instructions, and runtime pins at {len(installs)} installed paths")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("--expected-paths", type=int, required=True)
    args = parser.parse_args()
    verify(args.root, args.expected_paths)
