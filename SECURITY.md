# Security policy

Report vulnerabilities privately through
[GitHub's vulnerability reporting form](https://github.com/tclasen/resume-skill/security/advisories/new).
Include the affected commit or release, reproduction steps using synthetic data,
impact, and any suggested mitigation. Do not include real applicant information,
credentials, or confidential employer documents. Avoid public issues for
undisclosed vulnerabilities.

Security fixes target the current `main` branch and the latest release when one
exists. Older revisions are not maintained; update before reporting a problem
that has already been fixed. Response times are best effort.

This repository contains reusable code and synthetic tests. Applicant evidence
belongs in a separate private repository. Treat imported documents and generated
content as untrusted input and review exports before sharing them.

Maintainers should triage private reports, reproduce with synthetic fixtures,
prepare a regression test and fix, and coordinate disclosure with the reporter.
Revoke exposed credentials immediately; removing a file does not revoke a secret.
Use phishing-resistant two-factor authentication and least-privilege credentials
for GitHub accounts. Review dependency updates and workflow changes before merging.
