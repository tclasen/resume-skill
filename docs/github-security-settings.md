# GitHub security settings

Repository: `tclasen/resume-skill` (public, personal account).

The following settings were applied and read back through GitHub's API on
2026-09-10. They are external repository state, not automatically applied by
committing these files.

| Control | Setting |
| --- | --- |
| Secret scanning | Enabled |
| Secret push protection | Enabled |
| Private vulnerability reporting | Enabled |
| Dependabot alerts / security updates | Enabled |
| Release immutability | Enabled for future published releases |
| Default Actions token | Read-only; cannot approve pull requests |
| Allowed Actions | GitHub-owned only; full commit SHA pins required |
| Fork workflow execution | Maintainer approval for all external contributors |
| Merged branches | Automatically deleted |
| Default branch | PRs, resolved discussions, linear history, current passing checks; no force pushes, deletion, or bypass actors |
| Release tags `v*` | No updates or deletion; no bypass actors |

The exact ruleset payloads are versioned in
[`main-ruleset.json`](../.github/security/main-ruleset.json) and
[`tags-ruleset.json`](../.github/security/tags-ruleset.json). Required checks are
bound to the GitHub Actions app (ID 15368). There is no independent approval
minimum because the only collaborator is the owner, who cannot approve their own
PR. Add a second maintainer, then require one approval, code-owner approval, and
approval of the latest push. Repository administrators can still edit the settings;
there is no claim of protection from a compromised administrator.

## Activation and remaining verification

The workflow commits must reach GitHub through a PR before hosted validation can
complete. Required check names match the checked-in job names; confirm the actual
checks on the first PR before merging. CI configuration and local validation alone
do not establish a successful hosted build or SLSA conformance.

CodeQL checks require successful analysis. After the first default-branch analysis,
add a CodeQL code-scanning merge rule to block security findings, in addition to
analysis failures. This is deferred because GitHub requires analysis results on
both the base and proposed revision. Review any existing findings before enabling
the gate. The current required job checks do not themselves reject CodeQL alerts.

Non-provider secret patterns and secret validity checks remain disabled. GitHub
did not enable non-provider patterns in the repository update response; standard
provider secret scanning and push protection were verified enabled. Account MFA,
credential hygiene, access reviews, alert response, and future releases require
ongoing maintainer action.

## Inspect or reapply

```sh
gh api repos/tclasen/resume-skill/rulesets
gh api repos/tclasen/resume-skill/actions/permissions
gh api repos/tclasen/resume-skill/actions/permissions/selected-actions
gh api repos/tclasen/resume-skill/actions/permissions/workflow
gh api repos/tclasen/resume-skill/actions/permissions/fork-pr-contributor-approval
gh api repos/tclasen/resume-skill/private-vulnerability-reporting
gh api repos/tclasen/resume-skill/immutable-releases
gh api repos/tclasen/resume-skill --jq .security_and_analysis
```

To update an existing ruleset after review, get its ID from the first command and
use `gh api --method PUT repos/tclasen/resume-skill/rulesets/ID --input PATH` with
the corresponding JSON file. Use POST on `/rulesets` only to create a missing
ruleset; do not accumulate duplicates. Keep these files aligned with live changes.
