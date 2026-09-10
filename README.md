# Resume

Resume is a planned bundle of portable agent skills for curating knowledge
graphs, producing personalized resumes, and assessing qualifications against
position requirements with supporting evidence.

The repository currently contains this design overview and the engineering
working agreement. No skills, knowledge bundles, private workspace setup, or
document exporters are implemented. All capabilities below describe intended
behavior.

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
Private workspace setup remains future implementation work.

## Format pin and future implementation

Before implementing OKF authoring, the project must vendor a copy of Google's
OKF v0.2 specification, recording an immutable upstream revision and a SHA-256
checksum of the vendored specification. The upstream link above is a reference,
not an immutable pin. Specification upgrades must undergo deliberate review
before changing the pinned copy or adapting project conventions.

Specification vendoring, skill implementation, private workspace setup, and PDF
and DOCX exporters remain future work. This README introduces no public APIs or
runtime interfaces.
