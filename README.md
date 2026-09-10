# Resume

Resume is a planned bundle of portable agent skills for curating knowledge
graphs, producing personalized resumes, and assessing qualifications against
position requirements with supporting evidence.

The repository includes pinned format and ontology artifacts with offline
checksum validation, separate private workspace setup, and OKF concept authoring
and validation. Guided skill workflows and document exporters are not yet
implemented. The full workflow below describes their intended behavior.

## Purpose and workflow

Guided interviews, supplied documents and URLs, and targeted public research
will feed a reusable knowledge base. The planned workflow is to:

1. Gather applicant evidence and position information.
2. Curate that material into linked assertions with source attribution.
3. Verify claims, surface conflicts, and resolve them with recorded evidence.
4. Analyze applicant fit against individual position requirements.
5. Generate a tailored resume and a separate evidence report.

Interviews and follow-up research will address unclear claims and missing
evidence without treating unanswered questions as proof of a qualification gap.

## Knowledge graph organization

The design uses one reusable Open Knowledge Format (OKF) bundle per applicant
and one per position. A solo applicant is the default workflow; recruiters may
manage multiple applicants with separate bundles. Applicant-position analyses
will reference the relevant bundles and their canonical assertions without
duplicating canonical facts.

- **Applicant knowledge:** Personal facts, education, training, employment,
  qualifications, achievements, and other resume-relevant evidence.
- **Position knowledge:** Posting requirements, responsibilities, employer
  research, and recruiter clarifications. Explicit requirements will remain
  distinguishable from inferred expectations, with evidence and reasoning for
  those inferences.

Knowledge will be recursively decomposed into fine-grained, atomic assertions,
each in its own OKF concept document. Entity and summary concepts will connect
those assertions. Each assertion will preserve explicit links to its subject,
role or event, time, and measurement context, where applicable, so decomposition
does not strip away meaning or imply broader experience than the evidence supports.

## Provenance, verification, and evidence integrity

Use the [authoring reference](skills/resume/references/authoring.md) for the
implemented concept profile, evidence conventions, and validation limits.
Install the authoring dependency and validate a bundle:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r skills/resume/scripts/requirements.txt
.venv/bin/python skills/resume/scripts/resume.py validate --workspace /absolute/path/to/private-resumes --kind applicant --bundle solo
```

On Windows, use `.venv\Scripts\python.exe` for the virtual environment interpreter.
The `add` command imports a supplied OKF Markdown concept without overwriting;
`property` looks up an exact property URI in the pinned ontology definitions.
Validation checks structure and metadata, while evidence meaning and ontology
value constraints require source-grounded review.

Every assertion must have source attribution, authorship metadata, and a
determinable verification state. The design will use OKF's `sources`,
`generated`, and `verified` conventions and actor identities. Under OKF, an
absent `verified` field means unverified; human review and machine confirmation
are distinct trust tiers. These conventions are defined in the official
[OKF v0.2 specification](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md).

OKF makes these metadata families optional. Requiring attribution and authorship
for every assertion, atomic decomposition, and the following evidence rules are
project extensions. Self-attestation must remain distinguishable from independent
corroboration, even when both involve human review.

- Applicants or recruiters may record human review, identifying the reviewer
  and time. Recruiter review must identify its evidence basis; review alone
  does not establish independent corroboration.
- Employer-facing personal claims require applicant attestation or independent
  corroboration. Applicant attestation means the applicant confirms a personal
  claim; it is separate from OKF's computational attestation mechanism.
- Corrections and supersession history must be preserved, with links from prior
  assertions to their replacements. Unresolved disputed claims must be excluded
  from employer-facing outputs and from facts used to establish qualification.
- Derived claims must retain their inputs, methods, and assumptions. Derivation
  must not automatically promote verification state or inherit human review;
  the resulting claim requires its own evidence assessment.

## Approved ontologies and semantic metadata

The project vendors the following approved ontology versions. Exact sources,
immutable revisions or dated publications, and checksums are recorded in
[the pin manifest](skills/resume/references/vendor/pins.json).

| Ontology and source | Selected version | Canonical namespace | Intended use |
| --- | --- | --- | --- |
| [Schema.org](https://schema.org/docs/releases.html) | 30.0 | `https://schema.org/` | People, organizations, employment, credentials, and job requirements |
| [PROV-O](https://www.w3.org/TR/2013/REC-prov-o-20130430/) | W3C Recommendation, 2013-04-30 | `http://www.w3.org/ns/prov#` | Attribution, derivation, and provenance relationships |
| [SKOS](https://www.w3.org/TR/2009/REC-skos-reference-20090818/) | W3C Recommendation, 2009-08-18 | `http://www.w3.org/2004/02/skos/core#` | Concept labels, hierarchies, and mappings |

Every additional semantic metadata attribute must identify an exact property URI
defined in an approved, pinned ontology. Local aliases require explicit mappings
to those URIs and must preserve the property's meaning and value constraints.
Invented properties are prohibited. Vocabularies referenced by an approved
ontology, including through equivalence links or examples, are not implicitly
approved.

OKF format fields, including `sources`, `generated`, and `verified`, retain their
agreed format semantics and the evidence rules above. Ontology mappings must not
redefine verification, promote a claim's verification state, or imply independent
corroboration from attribution, derivation, or review alone.

When no approved property faithfully represents the evidence, skills must
preserve that evidence in narrative form and report the modeling gap. Introducing
another ontology requires maintainer approval and a documented pin before use.
Automatic ontology upgrades are prohibited.

## Intended outputs

The skills will produce personalized PDF and DOCX resumes with separate evidence
reports tracing claims to their supporting assertions, sources, and verification
states. Tailoring may select, reorder, and rephrase supported facts while
preserving their meaning, scope, and qualifications.

Qualification assessments will map each position requirement to supporting
facts, partial support, missing evidence, or demonstrated gaps, without numeric
scoring. Reports will distinguish missing evidence from evidence that a
requirement is not met, and explicit requirements from inferred expectations.

## Portability and privacy

Skills will be authored as host-independent `SKILL.md` instructions. Portability
is a design goal; compatibility with particular agent hosts has not been tested.

Real applicant data, source materials, knowledge bundles, analyses, and generated
outputs must remain in separate private workspaces outside this repository.
Initialize a new data repository outside this checkout, or use the root of an
existing separate Git repository. Python 3.10+ and Git are required:

```sh
python3 skills/resume/scripts/resume.py init --workspace /absolute/path/to/private-resumes
python3 skills/resume/scripts/resume.py bundle --workspace /absolute/path/to/private-resumes --kind applicant --id solo
python3 skills/resume/scripts/resume.py bundle --workspace /absolute/path/to/private-resumes --kind position --id engineer
python3 skills/resume/scripts/resume.py workspace --workspace /absolute/path/to/private-resumes
```

Use an absolute script path when running from another directory. Setup preserves
existing repository files and creates `applicants/`, `positions/`, `sources/`,
`analyses/`, and `outputs/`. Each applicant and position gets its own OKF bundle.
Repeated setup validates the existing workspace. Conflicting directories,
symlinked workspace paths, and locations inside this skill repository are rejected.
Use physical paths (for example, `/private/tmp` instead of `/tmp` on macOS).

Generated outputs are Git-ignored. Canonical evidence and analyses can be tracked
in the private data repository. Setup does not commit, add a remote, or publish
data. Keep any remote private; review staged files before committing or sharing.
New data directories and configuration files use private local permissions where
supported; existing repository permissions are preserved.

## Format and ontology pins

The unmodified OKF v0.2 specification and selected ontology artifacts are
[vended with provenance and license notices](skills/resume/references/vendor/README.md)
inside the skill distribution directory. Validate all four artifacts offline:

```sh
python3 skills/resume/scripts/pins.py
.venv/bin/python -m unittest discover -s tests -v
```

The validator rejects missing artifacts, checksum mismatches, unapproved
versions, incomplete manifests, and nonlocal artifact paths. Stop affected
authoring if validation fails. Specification and ontology upgrades require
deliberate maintainer review; never refresh pins automatically.

Guided skill workflows, qualification analysis, and PDF and DOCX exporters remain
future work.
