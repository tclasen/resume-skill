"""Create and locate a separate, local resume data repository."""

import json
import os
from pathlib import Path
import re
import subprocess

SKILL_ROOT = Path(__file__).resolve().parents[1]
CONFIG = "resume-workspace.json"
DIRECTORIES = ("applicants", "positions", "sources", "analyses", "outputs")


def checked_root(value):
    path = Path(value).expanduser().absolute()
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError(f"Workspace path must not use symlinks: {part}")
    path = path.resolve()
    protected = [SKILL_ROOT]
    protected.extend(p for p in SKILL_ROOT.parents if (p / ".resume-skill-repository").exists())
    if any(path == p or p in path.parents for p in protected):
        raise ValueError("Resume data must be outside the skill source and installation directories")
    return path


def git_root(path):
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=False,
    )
    return Path(result.stdout.strip()).resolve() if result.returncode == 0 else None


def exclusive_write(path, content):
    """Never clobber an existing file; private permissions on supported systems."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)


def load_workspace(value):
    root = checked_root(value)
    if git_root(root) != root:
        raise ValueError("Workspace must be the root of its separate Git repository")
    config_path = root / CONFIG
    if config_path.is_symlink():
        raise ValueError("Workspace configuration must not be a symlink")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config != {"format": "resume-workspace", "version": 1}:
        raise ValueError("Unsupported workspace configuration")
    for name in DIRECTORIES:
        child = root / name
        if child.is_symlink() or not child.is_dir():
            raise ValueError(f"Missing or unsafe workspace directory: {name}")
    return root


def init_workspace(value):
    root = checked_root(value)
    if (root / CONFIG).exists() or (root / CONFIG).is_symlink():
        return load_workspace(root)
    if root.exists() and not root.is_dir():
        raise ValueError("Workspace path is not a directory")
    # A new empty directory or an existing repository root is supported.
    # Do not turn arbitrary existing data directories into repositories.
    if root.exists() and any(root.iterdir()) and git_root(root) != root:
        raise ValueError("Use a new/empty directory or an existing separate Git repository root")
    if root.exists() and git_root(root) not in (None, root):
        raise ValueError("Do not nest a resume workspace inside another repository")
    parent = root.parent
    while not parent.exists():
        parent = parent.parent
    if git_root(parent) is not None and (not root.exists() or git_root(root) != root):
        raise ValueError("Do not nest a resume workspace inside another repository")
    for name in DIRECTORIES:
        if (root / name).exists() or (root / name).is_symlink():
            raise ValueError(f"Workspace setup would conflict with existing path: {name}")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if git_root(root) is None:
        subprocess.run(["git", "init", "--quiet", str(root)], check=True, capture_output=True)
    created = []
    try:
        for name in DIRECTORIES:
            directory = root / name
            directory.mkdir(mode=0o700)
            created.append(directory)
        # This ignore file applies only to generated outputs, preserving the
        # user's repository-wide .gitignore without modification.
        ignore = root / "outputs" / ".gitignore"
        exclusive_write(ignore, "*\n!.gitignore\n")
        created.append(ignore)
        config = root / CONFIG
        exclusive_write(config, json.dumps({"format": "resume-workspace", "version": 1}, indent=2) + "\n")
        created.append(config)
    except Exception:
        for path in reversed(created):
            if path.is_dir():
                path.rmdir()
            else:
                path.unlink()
        raise
    return load_workspace(root)


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise ValueError("Identifiers must contain lowercase letters, digits, and single hyphens")
    if len(value) > 64:
        raise ValueError("Identifiers must be at most 64 characters")
    return value


def create_bundle(workspace, kind, name):
    root = load_workspace(workspace)
    if kind not in ("applicant", "position"):
        raise ValueError("Bundle kind must be applicant or position")
    name = identifier(name)
    bundle = root / (kind + "s") / name
    if bundle.exists() or bundle.is_symlink():
        raise ValueError(f"Bundle already exists: {bundle}")
    bundle.mkdir(mode=0o700)
    try:
        exclusive_write(bundle / "index.md", f'---\nokf_version: "0.2"\n---\n# {kind.title()}: {name}\n\n')
        exclusive_write(bundle / "log.md", "# Directory Update Log\n\n")
    except Exception:
        for filename in ("index.md", "log.md"):
            (bundle / filename).unlink(missing_ok=True)
        bundle.rmdir()
        raise
    return bundle
