import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

from test_assessment import make_workspace

SKILL = Path(__file__).resolve().parents[1] / "skills/resume"


class PackagingTests(unittest.TestCase):
    def test_skill_metadata_and_local_references(self):
        text = (SKILL / "SKILL.md").read_text()
        _, frontmatter, body = text.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        self.assertEqual(metadata["name"], SKILL.name)
        self.assertRegex(metadata["name"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertLessEqual(len(metadata["name"]), 64)
        self.assertTrue(0 < len(metadata["description"]) <= 1024)
        self.assertTrue(0 < len(metadata["compatibility"]) <= 500)
        self.assertLess(len(text.splitlines()), 500)
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", body):
            self.assertFalse("://" in target, target)
            self.assertTrue((SKILL / target).is_file(), target)

    def test_installed_skill_runs_full_export_without_source_checkout(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            root, plan = make_workspace(base)
            installed = root / ".agents" / "skills" / "resume"
            shutil.copytree(SKILL, installed, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            draft = root / "sources" / "plan.json"
            draft.write_text(json.dumps(plan))
            environment = dict(os.environ)
            environment.pop("PYTHONPATH", None)
            script = installed / "scripts" / "resume.py"
            for args in (("pins",), ("assess", "--workspace", str(root), "--file", str(draft), "--id", "installed"),
                         ("export", "--workspace", str(root), "--file", str(draft), "--id", "installed")):
                result = subprocess.run([sys.executable, "-B", str(script), *args], cwd=root,
                                        env=environment, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "outputs/installed/resume.pdf").is_file())
            self.assertTrue((root / "outputs/installed/resume.docx").is_file())
            self.assertTrue((root / "analyses/installed.md").is_file())


if __name__ == "__main__":
    unittest.main()
