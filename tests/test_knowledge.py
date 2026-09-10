from copy import deepcopy
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/resume/scripts"))
from knowledge import add_concept, properties, read_concept, trust_tier, validate_bundle, validate_profile
from workspace import create_bundle, init_workspace


CONCEPT = '''---
type: Assertion
title: Built the fictional reporting service
generated: {by: resume-test/1, at: "2026-09-10T12:00:00Z"}
sources:
  - id: interview
    resource: https://example.invalid/synthetic-interview
---
# Claim
The applicant built the reporting service in their internship.[^interview]

# Subject
[Applicant](/person.md)

# Role or event
[Internship](/internship.md)

# Time
Summer 2025; exact dates not yet provided.

# Measurement
Not applicable; no quantitative claim.

# Evidence assessment
Unverified self-report. Applicant confirmation is pending. No independent
corroboration has been supplied. No known conflict.

[^interview]: Synthetic interview for tests only.
'''


class KnowledgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = properties()

    def test_property_definitions_not_imports_or_classes(self):
        for uri in ("https://schema.org/knowsAbout", "http://www.w3.org/ns/prov#wasDerivedFrom",
                    "http://www.w3.org/2004/02/skos/core#prefLabel"):
            self.assertTrue(uri in self.catalog, uri)
        for uri in ("https://schema.org/Person", "http://purl.org/dc/terms/title",
                    "https://schema.org/inventedQualification"):
            self.assertTrue(uri not in self.catalog, uri)

    def test_reader_preserves_unknown_okf_metadata_and_missing_trust(self):
        metadata, body = read_concept("---\ntype: Future concept\ncustom: retained\n---\nText")
        self.assertEqual(metadata["custom"], "retained")
        self.assertEqual(body, "Text")
        self.assertEqual(trust_tier(metadata), "unverified")
        with self.assertRaisesRegex(ValueError, "Unapproved"):
            validate_profile(metadata, body, self.catalog)

    def test_bare_verification_and_trust_tiers(self):
        metadata, body = read_concept(CONCEPT)
        self.assertEqual(validate_profile(metadata, body, self.catalog), "unverified")
        metadata["verified"] = {"by": "process:test", "at": "2026-09-10T12:01:00Z"}
        self.assertEqual(validate_profile(metadata, body, self.catalog), "machine-confirmed")
        metadata["verified"] = [metadata["verified"], {"by": "human:reviewer", "at": "2026-09-10T12:02:00Z"}]
        self.assertEqual(validate_profile(metadata, body, self.catalog), "human-reviewed")

    def test_required_evidence_and_context(self):
        original, body = read_concept(CONCEPT)
        for field in ("sources", "generated", "title"):
            metadata = deepcopy(original)
            del metadata[field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_profile(metadata, body, self.catalog)
        for section in ("Claim", "Subject", "Time", "Measurement", "Role or event", "Evidence assessment"):
            changed = body.replace("# " + section, "# Removed " + section)
            with self.subTest(section=section), self.assertRaises(ValueError):
                validate_profile(original, changed, self.catalog)
        with self.assertRaisesRegex(ValueError, "footnote"):
            validate_profile(original, body.replace("[^interview]", "[^invented]"), self.catalog)

    def test_derived_claim_and_inferred_requirement(self):
        metadata, body = read_concept(CONCEPT)
        metadata["type"] = "Derived assertion"
        with self.assertRaisesRegex(ValueError, "Derivation"):
            validate_profile(metadata, body, self.catalog)
        self.assertEqual(validate_profile(metadata, body + "\n# Derivation\nInputs, method, and assumptions pending.\n", self.catalog), "unverified")
        metadata["type"] = "Requirement"
        with self.assertRaisesRegex(ValueError, "Requirement basis"):
            validate_profile(metadata, body, self.catalog)
        validate_profile(metadata, body + "\n# Requirement basis\nInferred: reasoning and source.[^interview]\n", self.catalog)

    def test_duplicate_and_unsafe_yaml_rejected(self):
        for text in ("---\ntype: Assertion\ntype: Person\n---\n", "---\ntype: !!python/object:bad {}\n---\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                read_concept(text)

    def test_bad_timestamps_and_actors(self):
        metadata, body = read_concept(CONCEPT)
        metadata["generated"]["at"] = "2026-09-10"
        with self.assertRaisesRegex(ValueError, "timezone"):
            validate_profile(metadata, body, self.catalog)
        metadata["generated"]["at"] = "2026-09-10T00:00:00Z"
        metadata["generated"]["by"] = "somebody"
        with self.assertRaisesRegex(ValueError, "Actor"):
            validate_profile(metadata, body, self.catalog)

    def test_add_validate_and_nonoverwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = init_workspace(Path(temp).resolve() / "private")
            bundle = create_bundle(root, "applicant", "solo")
            path = add_concept(root, "applicant", "solo", "reporting", CONCEPT)
            self.assertEqual(path.read_text(), CONCEPT)
            with self.assertRaises(FileExistsError):
                add_concept(root, "applicant", "solo", "reporting", CONCEPT)
            report = validate_bundle(root, "applicant", "solo")
            self.assertEqual(report[0]["trust"], "unverified")
            self.assertEqual(report[0]["broken_links"], ["/person.md", "/internship.md"])
            with self.assertRaisesRegex(ValueError, "escapes"):
                add_concept(root, "applicant", "solo", "bad-link", CONCEPT.replace("/person.md", "../../person.md"))
            self.assertFalse((bundle / "bad-link.md").exists())
            with self.assertRaisesRegex(ValueError, "reserved"):
                add_concept(root, "applicant", "solo", "index", CONCEPT)

    def test_reserved_files_and_cli_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp:
            root = init_workspace(Path(temp).resolve() / "private")
            bundle = create_bundle(root, "applicant", "solo")
            draft = root / "sources" / "draft.md"
            draft.write_text(CONCEPT)
            script = Path(__file__).resolve().parents[1] / "skills/resume/scripts/resume.py"
            result = subprocess.run([sys.executable, str(script), "add", "--workspace", str(root),
                                     "--kind", "applicant", "--bundle", "solo", "--id", "claim",
                                     "--file", str(draft)], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((bundle / "claim.md").read_text(), CONCEPT)
            (bundle / "log.md").write_text("# History\n## yesterday\nChanged claim\n")
            with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
                validate_bundle(root, "applicant", "solo")
            (bundle / "log.md").write_text("# History\n## 2026-09-10\nChanged claim\n")
            (bundle / "index.md").write_text('---\nokf_version: "0.2"\ncustom: invalid\n---\n')
            with self.assertRaisesRegex(ValueError, "declare only"):
                validate_bundle(root, "applicant", "solo")


if __name__ == "__main__":
    unittest.main()
