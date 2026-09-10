# Authoring resume knowledge

Run `scripts/resume.py pins` before authoring. Keep all working files and source
materials in the selected private workspace. Installed scripts locate their
vendored artifacts relative to themselves, independent of the working directory.

Install the authoring dependency into a virtual environment using
`python -m pip install -r <skill-directory>/scripts/requirements.txt`.
Workspace setup and pin validation need only Python 3.10+ and Git; knowledge
reading uses PyYAML's safe loader with duplicate-key rejection.

## Bundle and concept structure

Use one `applicants/<id>/` bundle per person and one `positions/<id>/` bundle per
position. Keep `index.md` as a linked directory overview and `log.md` as dated
history. Bundle-root indexes may declare `okf_version: "0.2"`; other indexes and
logs have no frontmatter. Log date headings use `## YYYY-MM-DD`.

Write one atomic factual assertion per concept. Split compound claims until
each can be independently supported, disputed, corrected, or selected. Use
`type: Assertion`, `type: Derived assertion`, or `type: Requirement` for those
concepts; use descriptive entity/summary types such as `Person`, `Employment`,
`Organization`, `Credential`, or `Summary` for connecting concepts. Entity
summaries link to canonical assertions rather than introducing unattributed facts.

Concept IDs are paths without `.md`. The add command accepts lowercase ASCII
letters, digits, and single hyphens, at most 64 characters; it creates a root
concept without overwriting an existing one. Hand-authored nested concepts are
also readable. `index` and `log` are reserved filenames.

All authored concepts require `type`, `title`, `generated: {by, at}`, and a
nonempty `sources` list. Each source has a stable `id` and `resource`; cite it
with `[^source-id]` and a matching footnote definition. Resource URLs, relative
source paths, and clearly identified source-scope descriptions retain OKF's
semantics. Capture source dates, access context, exact excerpts or page/section
locations, and limitations in the narrative. Do not manufacture inaccessible
source contents. Source documents can be copied into `references/` inside their
bundle; source Markdown files there must themselves be valid OKF concepts.

## Context and evidence narrative

Assertions require these level-one body sections:

- `# Claim`: one supported assertion with source footnotes; preserve caveats.
- `# Subject`: link to the person, position, organization, or other subject.
- `# Role or event`: link to the relevant employment, project, course, or event;
  explicitly say why none applies when appropriate.
- `# Time`: interval/as-of date and precision; link to the dated context concept
  when one exists. Never infer full-time duration from year-only dates.
- `# Measurement`: unit, population, baseline, time window, attribution and
  method for a metric; otherwise explain that no metric is asserted.
- `# Evidence assessment`: explain self-report versus independent evidence,
  review identity/time/basis, unresolved conflicts, and remaining uncertainty.

Every entity/summary also has an `# Evidence assessment` section. Narrative
section names are authoring conventions, not invented ontology properties.

Derived assertions also require `# Derivation`: link every input concept, state
the method and assumptions, and show calculations where relevant. Do not
inherit verification from inputs. A derived assertion needs its own review.

Requirements also require `# Requirement basis`, beginning with `Explicit:` or
`Inferred:`. Explicit requirements cite the posting or recruiter clarification;
inferred expectations cite evidence and explain the inference. Preserve each
requirement's scope, alternatives, mandatory/preferred wording, and exceptions.

## Verification and corrections

Actors use `human:<id>`, `process:<id>`, or `<producer>/<version>`. All timestamps
have explicit timezones. `verified` may be one `{by, at}` mapping or a list.
Absent/empty verification is unverified; nonhuman verification is
machine-confirmed; any human event yields human-reviewed. These OKF tiers do not
prove independent corroboration or authorize employer-facing use.

Record human review only when the person actually reviewed the claim. Applicant
attestation is the applicant's confirmation of a personal claim; it is separate
from OKF computational attestation. Recruiter review must describe its evidence
basis, and does not by itself independently corroborate the claim. A machine
validator never writes `verified` merely because checks pass.

Keep unresolved disputed claims in the graph for investigation, but exclude them
from qualification support and employer-facing output. Preserve old assertions
when correcting them: create a replacement concept, mark the old concept
`status: deprecated`, add narrative links from old to replacement and replacement
to old, and record dated reasons and evidence in `log.md`. Do not erase source
history or transfer old review events to changed claims. Reassess dependent
derivations and analyses after corrections.

## Semantic metadata

Outside OKF format fields, use full property URIs defined in the three pinned
ontologies. `scripts/resume.py property <URI>` returns the actual pinned
definition for inspection. It excludes imported vocabularies and class URIs.
This authoring profile uses full URIs rather than local aliases.

Before applying a property, inspect its meaning, domain, range, cardinality,
language constraints, and relevant normative conditions. A valid property name
does not imply a semantically valid value. For example, `schema:knowsAbout`
describes knowledge about a topic, not proven professional competence. SKOS
`prefLabel` must respect its language uniqueness constraint. Attribution and
derivation properties never elevate trust. If no property faithfully fits, keep
the evidence in prose under `# Modeling gaps` and explain why; do not invent a
property or silently approve a referenced vocabulary.

## Commands and limits

```sh
python <skill-directory>/scripts/resume.py add --workspace <private-root> --kind applicant --bundle solo --id achievement --file <private-root>/sources/achievement-draft.md
python <skill-directory>/scripts/resume.py validate --workspace <private-root> --kind applicant --bundle solo
python <skill-directory>/scripts/resume.py property https://schema.org/knowsAbout
```

The validator checks syntax, attribution, actor/timestamp conventions, approved
property membership, required narrative sections, and unsafe local links. It
reports broken local concept links without treating them as invalid OKF.
Complete those links before relying on the assertions in an output. It does not
establish truth, verify source contents, prove atomicity, check every ontology
value constraint, or decide whether narrative evidence supports a claim. The
agent must review these aspects against the sources and ask focused questions
where evidence is missing. Read-only OKF parsing preserves unknown fields;
stricter rejection occurs in this project's authoring profile, not as a claim
that such external documents are invalid OKF.
