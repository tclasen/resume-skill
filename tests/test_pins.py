import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/resume/scripts"))
from pins import VENDOR, validate_pins


class PinTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.vendor = Path(self.temp.name) / "vendor"
        shutil.copytree(VENDOR, self.vendor)

    def test_reviewed_artifacts(self):
        self.assertEqual(len(validate_pins()["artifacts"]), 4)

    def test_tampered_artifact(self):
        with (self.vendor / "okf-0.2.md").open("a") as stream:
            stream.write("tampered")
        with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
            validate_pins(self.vendor)

    def test_missing_artifact(self):
        (self.vendor / "skos-20090818.rdf").unlink()
        with self.assertRaises(OSError):
            validate_pins(self.vendor)

    def test_missing_pin_and_unapproved_version(self):
        path = self.vendor / "pins.json"
        original = json.loads(path.read_text())
        for change in ("missing", "version", "escape", "revision"):
            with self.subTest(change=change):
                data = json.loads(json.dumps(original))
                if change == "missing":
                    data["artifacts"].pop()
                elif change == "version":
                    data["artifacts"][0]["version"] = "0.3"
                elif change == "escape":
                    data["artifacts"][0]["file"] = "../okf-0.2.md"
                else:
                    data["artifacts"][0]["revision"] = "main"
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    validate_pins(self.vendor)


if __name__ == "__main__":
    unittest.main()
