# Qualification assessment and resume selection

Read the applicant and position bundles and their sources before preparing an
assessment. Assess each current `Requirement`, including preferred and inferred
ones. Do not numerically rank people or collapse findings into a fit score.

## Make evidence judgments

For each requirement, record one outcome:

| Outcome | Evidence needed |
| --- | --- |
| `supported` | Eligible applicant assertions address the whole requirement, including scope and caveats. |
| `partial` | Eligible assertions address part; explain the uncovered part and ask a focused follow-up. |
| `missing-evidence` | No qualifying evidence is available. Ask for the missing evidence; do not infer inability. |
| `demonstrated-gap` | Eligible affirmative evidence establishes that the requirement is not met. Explain the comparison; absence of a document is insufficient. |

Retain explicit/inferred classification in the canonical requirement's
`# Requirement basis` section. Do not turn an employer expectation inferred from
research into a stated hiring requirement. If the posting is ambiguous, preserve
the ambiguity and ask for clarification rather than quietly strengthening it.

For every applicant assertion used for qualification or resume text, review its
sources and narrative evidence assessment. Record whether it is disputed and
whether its evidence basis is `unverified`, `applicant-attested`, or `independent`.
The review must refer to the exact current assertion hash. Eligible reviews
match the identity and time of an actual canonical `verified` event and name
the supporting source IDs. Applicant attestation must identify the actual human
applicant. Do not use a recruiter's or agent's identity as the applicant.
Independent evidence requires a source independent of the applicant's claim;
reposting the applicant's biography is not independent corroboration. Explain
this evidence relationship in the rationale. Recruiter review alone is not
independent evidence.

The validator enforces recorded eligibility and provenance, not natural-language
truth. Read the source before marking a decision: never set `disputed: false`
when the narrative or source history contains an unresolved dispute. Resolve it
with the applicant/recruiter, record the evidence, and revise/supersede affected
concepts first. A bare human review tier cannot override these rules.

Derived assertions need both their own eligible review and eligible reviews of
every canonical assertion linked in `# Derivation`. Keep methods, assumptions,
and input links in that section. Never use a derived number to hide disputed,
deprecated, stale, or unsupported inputs. Link background context outside the
Derivation section so it is not mistaken for an assertion input.

## Prepare a plan in the private workspace

Run `snapshot --workspace <root> --kind applicant --bundle <id>` and the same
command with `--kind position`. Each returns a bundle `sha256` and individual
file hashes. Snapshots include all bundle files, including local source captures.
External URLs are not fetched or hashed; refresh public research and preserve
dated captures when its currency matters. Rebuild the plan after any bundle
change; do not merely update hashes without reviewing the changes.

Save a JSON plan under the private workspace. It is an operational report input,
not a parallel knowledge graph: canonical facts stay in OKF and the plan records
references, review decisions, requirement reasoning, and proposed output wording.
It has exactly these fields:

```json
{
  "version": 1,
  "applicant": "solo",
  "position": "engineer",
  "applicant_snapshot": "<applicant bundle SHA-256>",
  "position_snapshot": "<position bundle SHA-256>",
  "generated": {"by": "<producer/version>", "at": "<ISO datetime with timezone>"},
  "reviews": {
    "applicants/solo/achievement.md": {
      "sha256": "<exact concept file SHA-256>",
      "disputed": false,
      "basis": "applicant-attested",
      "by": "human:<actual-applicant-id>",
      "at": "<matching canonical verification event datetime>",
      "evidence": ["interview"],
      "rationale": "Explain the actual confirmation and its source location."
    }
  },
  "requirements": [
    {
      "requirement": "positions/engineer/requirement.md",
      "outcome": "partial",
      "evidence": ["applicants/solo/achievement.md"],
      "rationale": "Explain what is supported and what remains unknown.",
      "follow_up": "Ask for the specific missing detail."
    }
  ],
  "resume": null
}
```

Replace placeholders with evidence-backed values. Add every nondeprecated
requirement exactly once. Draft and stale requirements must be resolved before
assessment. Missing-evidence findings have an empty evidence list; other
outcomes require eligible applicant assertions. Additional keys, including
numeric score fields, are rejected. Multiple applicants use different plans and
bundles; evidence from another applicant or position is rejected.

Use `resume: null` for a qualification-only report. For a tailored resume, use:

```json
{
  "name": {"text": "<Applicant name>", "evidence": ["applicants/solo/name.md"]},
  "contact": [
    {"text": "<Chosen contact details>", "evidence": ["applicants/solo/contact.md"]}
  ],
  "sections": [
    {
      "heading": "Experience",
      "items": [
        {"text": "<Supported, tailored statement>", "evidence": ["applicants/solo/achievement.md"]}
      ]
    }
  ]
}
```

Every personal line, including identity and contact, needs eligible atomic
assertions and reviews. Use plain single-line text; select, reorder, and rephrase
only while preserving meaning, dates, scope, attribution, and qualifications.
Link every assertion supporting a combined line. Do not introduce a number,
seniority, duration, credential, or broader responsibility by paraphrasing.

Supported section headings: Summary, Experience, Education, Skills,
Certifications, Projects, Publications, Awards, Volunteering, Training, Languages.
Put factual role/employer/date headings in evidence-backed items. Section order,
line order, and wording determine the rendered resume. An empty contact list is
allowed when the user wants to omit contact details. Avoid irrelevant personal
information; include only contact channels the applicant wants shared.

## Generate and review the evidence report

```sh
python <skill-directory>/scripts/resume.py assess --workspace <private-root> --file <private-root>/sources/assessment-draft.json --id solo-engineer-v1
```

This writes `analyses/solo-engineer-v1.json` and `.md` without overwriting prior
analyses. The report includes every requirement, qualitative finding, follow-up,
resume line trace, and reviewed concept's source/verification ledger. Both
canonical bundle snapshots are recorded. Reusing an old id is refused to
preserve review history. Check the report against the source evidence before
sharing; the report is separate from the employer-facing resume.
