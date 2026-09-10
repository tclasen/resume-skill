# Resume

A portable agent skill for maintaining career evidence, assessing qualifications,
and generating tailored PDF and DOCX resumes with separate evidence reports.
Applicant data lives in a **separate private Git repository**; this repository
contains only the reusable skill, code, references, and synthetic tests.

## Install

Install with the [skills.sh CLI](https://www.skills.sh/docs) from the private
repository where you want to use it. Choose your agent interactively:

```sh
npx skills add /absolute/path/to/this-repository --skill resume
```

Once this repository is hosted, replace the local path with its Git URL or
GitHub `owner/repo`. To install for every supported agent:

```sh
npx skills add <git-url-or-local-path> --skill resume --agent '*' --copy
```

Use `--copy` when you prefer independent copies over agent-directory symlinks.
Use `--global` for a user-level installation where the chosen agent supports it.
The installer requires Node.js; follow its current runtime requirements.

The skill follows the [Agent Skills format](https://agentskills.io/specification)
and uses ordinary file, terminal, document, and browsing capabilities without a
specific model, connector, or API key. Installation was verified with skills CLI
**1.5.25** for all **79 agent targets**, covering **55 distinct project paths**.
Every installed copy preserved the instructions and runtime assets and passed
pin validation. This checks distribution and executable portability; it does
not claim an end-to-end model evaluation in every agent product.

## Use

Ask your agent, for example:

- “Use resume to interview me and organize my career evidence in this private repo.”
- “Tailor my resume to this job posting and produce PDF, DOCX, and an evidence report.”
- “Assess this applicant against the position requirements; distinguish missing evidence from gaps.”
- “Correct this achievement, preserve its history, and refresh the affected application.”

The agent follows [the skill workflow](skills/resume/SKILL.md):

1. Gather applicant evidence and position information through supplied materials,
   guided interviews, and targeted public research.
2. Curate linked atomic assertions with source attribution and contextual links.
3. Review evidence, surface conflicts, and preserve corrections and supersession.
4. Map every position requirement to supported facts, partial support, missing
   evidence, or demonstrated gaps, without numeric scoring.
5. Select and rephrase supported facts for the role, then export both resume
   formats and the separate evidence report.

Unanswered questions remain missing evidence, not proof that a qualification is
absent. Explicit requirements remain distinct from inferred expectations.

## Runtime and private workspace

Python **3.10+** and Git are required. Install the Python dependencies in a virtual
environment. Use your installed skill's absolute path in place of `<skill-dir>`:

```sh
python3 -m venv /absolute/path/to/resume-venv
/absolute/path/to/resume-venv/bin/python -m pip install -r <skill-dir>/scripts/requirements.txt
```

On Windows, use the virtual environment's `Scripts\python.exe` interpreter.
The following examples use `python` for that environment's interpreter:

```sh
python <skill-dir>/scripts/resume.py pins
python <skill-dir>/scripts/resume.py init --workspace /absolute/path/to/private-resumes
python <skill-dir>/scripts/resume.py bundle --workspace /absolute/path/to/private-resumes --kind applicant --id solo
python <skill-dir>/scripts/resume.py bundle --workspace /absolute/path/to/private-resumes --kind position --id engineer
```

Setup accepts a new empty directory or an existing separate Git repository root.
If installing the skill into a new project first, initialize that project with
`git init` before running workspace setup. Existing repository files are preserved.
The workspace contains:

```text
private-resumes/
  resume-workspace.json
  applicants/<applicant-id>/    # One reusable OKF bundle per person
  positions/<position-id>/      # One reusable OKF bundle per position
  sources/                     # Intake material and working drafts
  analyses/                    # Reference-based plans and evidence reports
  outputs/<export-id>/          # PDF, DOCX, Markdown, evidence, and checksums
```

One applicant is the default; recruiters can maintain separate bundles for many
people. Context and summary concepts connect each person's fine-grained assertions
without stripping away subject, role/event, time, or measurement context.

Use physical workspace paths; symlinked paths are rejected (for example, use
`/private/tmp` instead of `/tmp` on macOS). Setup rejects data locations inside
the skill installation and creation of nested Git repositories. New data directories and files
use private permissions where supported; existing repository permissions remain
unchanged. Setup never commits, adds a remote, or publishes data. Keep any data
remote private and review files before committing or sharing. Generated outputs
are Git-ignored.

## Evidence and knowledge integrity

The skill uses the vendored Open Knowledge Format **v0.2** specification. Each
assertion has `sources`, `generated` authorship, and a determinable verification
state. Missing `verified` means unverified; machine confirmation and human review
are different trust tiers. The stricter resume authoring profile extends OKF
without changing its format semantics.

Employer-facing personal claims require actual applicant attestation or
independent corroboration. Applicant attestation is a person's confirmation,
separate from OKF computational attestation. Recruiter review records the reviewer,
time, and evidence basis; review alone does not establish independent corroboration.
Unresolved disputed claims are excluded from resume text and qualification support.

Corrections preserve prior assertions, replacement links, and dated history.
Derived claims retain input links, methods, and assumptions and require their own
evidence assessment. They do not inherit verification from their inputs.
Assessment plans reference canonical assertions and contain operational review
and output decisions, not a duplicate knowledge graph. Content hashes invalidate
old reviews/plans when evidence changes.

Only property URIs defined in these approved, pinned ontologies may be used as
additional semantic metadata:

| Ontology | Version | Namespace |
| --- | --- | --- |
| [Schema.org](https://schema.org/docs/releases.html) | 30.0 | `https://schema.org/` |
| [PROV-O](https://www.w3.org/TR/2013/REC-prov-o-20130430/) | 2013-04-30 Recommendation | `http://www.w3.org/ns/prov#` |
| [SKOS](https://www.w3.org/TR/2009/REC-skos-reference-20090818/) | 2009-08-18 Recommendation | `http://www.w3.org/2004/02/skos/core#` |

The authoring profile uses full URIs. Property meanings and value constraints must
be preserved; imported vocabularies and equivalence links are not approval to use
other ontologies. Unmappable evidence stays in narrative form with a modeling-gap
note. New ontologies and pin upgrades require deliberate maintainer approval;
there are no automatic upgrades. Provenance mappings never elevate verification.

[The pin manifest](skills/resume/references/vendor/pins.json) records immutable
revisions or dated publications and SHA-256 checksums. All pins are checked
offline before commands run. Missing or changed pins stop affected operations.
[Upstream artifacts and license notices](skills/resume/references/vendor/README.md)
are included in the skill distribution.

## Commands and outputs

Run `python <skill-dir>/scripts/resume.py --help` for arguments.

| Command | Purpose |
| --- | --- |
| `pins` | Validate the four reviewed format/ontology artifacts |
| `init`, `workspace`, `bundle` | Initialize/check private workspaces and create bundles |
| `add`, `validate` | Add attributed OKF concepts without overwriting and validate bundles |
| `property` | Inspect a pinned ontology's exact property definition |
| `snapshot` | Hash current bundle contents for assessment review |
| `assess` | Check complete requirement coverage and write the evidence report/plan |
| `export` | Generate PDF, DOCX, Markdown, separate evidence, and output checksums |

Detailed guides: [interview/research](skills/resume/references/interview.md),
[authoring](skills/resume/references/authoring.md),
[assessment plan format](skills/resume/references/assessment.md), and
[export and document review](skills/resume/references/export.md).

Export supports US Letter and A4, selectable PDF text with embedded fonts, and
editable DOCX paragraphs. Long documents paginate. Unsupported PDF glyphs fail
with an actionable font message; custom TrueType fonts are supported. Inspect
complex-script shaping and the final page layout in your document viewer.

Validation checks recorded provenance, references, snapshots, metadata, and
eligibility. It cannot establish truth, prove a human attestation occurred, or
judge whether a paraphrase preserves meaning. The agent must review source
contents, ontology value constraints, and output wording. A passing check is not
independent corroboration. Browsing and visual document review depend on the
host's available tools; unavailable checks must be reported honestly.

## Development

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r tests/requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python skills/resume/scripts/pins.py
```

Tests use synthetic data in temporary separate repositories. They exercise
workspace isolation, provenance and ontology validation, requirement coverage,
eligibility rejection, stale evidence, derivations, and PDF/DOCX text and export
failure cleanup. Do not add real applicant data to this repository.
