from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import contextmanager
import os

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/resume/scripts"
sys.path.insert(0, str(SCRIPTS))
from workspace import create_bundle, exclusive_write, init_workspace, load_workspace


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "private"

    def test_separate_repository_and_repeated_setup(self):
        root = init_workspace(self.root)
        self.assertTrue((root / ".git").is_dir())
        self.assertEqual(init_workspace(root), root)
        self.assertEqual(load_workspace(root), root)
        bundle = create_bundle(root, "applicant", "solo")
        self.assertIn('okf_version: "0.2"', (bundle / "index.md").read_text())
        create_bundle(root, "applicant", "second-person")
        create_bundle(root, "position", "engineer")
        with self.assertRaisesRegex(ValueError, "already exists"):
            create_bundle(root, "applicant", "solo")
        output = root / "outputs" / "resume.pdf"
        output.write_bytes(b"synthetic")
        result = subprocess.run(["git", "-C", str(root), "check-ignore", str(output)], capture_output=True)
        self.assertEqual(result.returncode, 0)

    def test_existing_repo_files_preserved(self):
        self.root.mkdir()
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)
        (self.root / ".gitignore").write_text("user-rule\n")
        (self.root / "README.md").write_text("User data repository")
        init_workspace(self.root)
        self.assertEqual((self.root / ".gitignore").read_text(), "user-rule\n")
        self.assertEqual((self.root / "README.md").read_text(), "User data repository")

    def test_source_repo_and_nested_repo_rejected(self):
        with self.assertRaisesRegex(ValueError, "nest"):
            init_workspace(SCRIPTS.parents[2] / "private-data")
        init_workspace(self.root)
        with self.assertRaisesRegex(ValueError, "nest"):
            init_workspace(self.root / "nested")
        self.assertFalse((self.root / "nested").exists())

    def test_skill_installation_rejected(self):
        for path in (SCRIPTS.parent, SCRIPTS.parent / "private-data"):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "outside"):
                init_workspace(path)

    def test_existing_unmanaged_data_and_collisions_rejected(self):
        self.root.mkdir()
        (self.root / "keep.txt").write_text("keep")
        with self.assertRaisesRegex(ValueError, "new/empty"):
            init_workspace(self.root)
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)
        (self.root / "applicants").mkdir()
        with self.assertRaisesRegex(ValueError, "conflict"):
            init_workspace(self.root)
        self.assertFalse((self.root / "resume-workspace.json").exists())
        self.assertEqual((self.root / "keep.txt").read_text(), "keep")

    def test_symlinks_and_identifier_traversal_rejected(self):
        init_workspace(self.root)
        alias = self.root.parent / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            load_workspace(alias)
        for name in ("../escape", "", "/tmp/escape", "a/b", "A", "a" * 65):
            with self.subTest(name=name), self.assertRaises(ValueError):
                create_bundle(self.root, "applicant", name)
        (self.root / "sources").rmdir()
        (self.root / "sources").symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "unsafe"):
            load_workspace(self.root)

    def test_cli_from_unrelated_working_directory(self):
        result = subprocess.run([sys.executable, str(SCRIPTS / "resume.py"), "init",
                                 "--workspace", str(self.root)], cwd=self.root.parent,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(self.root))

    def test_failed_write_removes_only_its_new_partial_file(self):
        self.root.mkdir()
        existing = self.root / "existing.md"
        existing.write_text("preserve")
        with self.assertRaises(FileExistsError):
            exclusive_write(existing, "replacement")
        self.assertEqual(existing.read_text(), "preserve")
        original_fdopen = os.fdopen

        @contextmanager
        def failing_stream(descriptor, *args, **kwargs):
            with original_fdopen(descriptor, *args, **kwargs) as stream:
                class PartialWriter:
                    def write(self, content):
                        stream.write(content[:5])
                        stream.flush()
                        raise OSError("synthetic disk full")
                yield PartialWriter()

        new = self.root / "new.md"
        with patch("workspace.os.fdopen", failing_stream):
            with self.assertRaisesRegex(OSError, "disk full"):
                exclusive_write(new, "content that must not be left half-written")
        self.assertFalse(new.exists())
        self.assertEqual(existing.read_text(), "preserve")


if __name__ == "__main__":
    unittest.main()
