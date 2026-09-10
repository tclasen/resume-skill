# Supply-chain security

The release workflow targets **SLSA v1.2 Build Level 2** for the uploaded
`resume-skill.tar.gz` artifact. This is not a certification, a claim about
unbuilt Git checkouts, or a claim that dependencies and code are vulnerability-free.
Compliance requires a successful hosted build and verified provenance for the
specific artifact, plus ongoing maintenance of the repository controls.

| Build L2 requirement | Implementation |
| --- | --- |
| Consistent build process | Version-controlled `release.yml` tests the source and archives only tracked distribution files. |
| Hosted build | Build, attestation, and publication use separate GitHub-hosted Ubuntu runners. |
| Provenance exists | `actions/attest` records the artifact SHA-256, source revision, workflow identity, and build invocation. |
| Authentic provenance | GitHub OIDC and Sigstore sign the SLSA provenance; no long-lived signing secret is stored in the repository. |
| Provenance distribution | The Sigstore bundle accompanies the archive in Actions artifacts and tagged GitHub Releases; attestations are also stored by GitHub. |

The build job has read-only repository access. The attestation job does not check
out or execute project code. Only the final publication job receives repository
write permission. Actions are pinned to full commit IDs and updated by Dependabot.
No build caches or self-hosted runners are used. Python dependencies are directly
version-pinned, but this does not claim a hermetic build or complete transitive
dependency pinning. SLSA Build L3 is outside this configuration's scope.

## Build and release

After merging the workflow, run it manually on `main` for a validation build:

```sh
gh workflow run release.yml --repo tclasen/resume-skill --ref main
```

This produces the `attested-distribution` Actions artifact, retained for 30 days,
without publishing a release. Download it from that run to verify the archive.
For a release, create and push a version tag such as `v1.0.0` on a reviewed commit
already merged into `main`. The workflow rejects tags whose commits are outside
`main` or whose names do not match its version pattern. Use lightweight tags so
the workflow SHA identifies the source commit directly.

The workflow creates a draft, uploads the archive, checksum and provenance bundle,
and then publishes it. Repository release immutability must be enabled before
publishing. Published releases retain the assets beyond Actions artifact expiry.
If publication fails after draft creation, inspect the draft and workflow failure
before recovery; the workflow deliberately does not overwrite existing assets.
Publish a new version to replace a defective immutable release.

## Verify before installing

Choose the intended release and obtain its expected source commit through your
reviewed release/change process. Replace the example values below:

```sh
tag=v1.0.0
commit=REPLACE_WITH_REVIEWED_FULL_COMMIT_SHA
gh release download "$tag" --repo tclasen/resume-skill \
  --pattern resume-skill.tar.gz --pattern resume-skill.sigstore.json
gh attestation verify resume-skill.tar.gz \
  --bundle resume-skill.sigstore.json \
  --repo tclasen/resume-skill \
  --signer-workflow tclasen/resume-skill/.github/workflows/release.yml \
  --source-ref "refs/tags/$tag" --source-digest "$commit" \
  --deny-self-hosted-runners
```

For a manual validation build, use `--source-ref refs/heads/main` and that run's
source commit. Verification must succeed before extracting or executing files.
The bundle supplies the signature and provenance; verification also needs trusted
Sigstore roots (the CLI normally retrieves them online). A checksum alone does
not authenticate a release. The archive extracts into `resume-skill/`; the skill
is under `resume-skill/skills/resume/`.

The `skills.sh` Git installation path in the README does not perform this
attestation verification. GitHub's automatically generated source ZIP/tar archives
are also outside this artifact's provenance claim.

## Repository controls

Maintain secret scanning and push protection, private vulnerability reporting,
Dependabot alerts and security updates, read-only default workflow tokens, and
full-SHA action pinning. Protect `main` with pull requests, passing test and code
scanning checks, resolved discussions, and blocked force pushes and deletion.
Protect version tags against updates and deletion. Require independent approval
when a second maintainer is available; a sole maintainer cannot approve their own
pull request. Review account access and security alerts regularly.

These are GitHub settings, not effects of checking in YAML. Their applied state
must be verified through the API or repository settings. Two-factor authentication
is an account control and cannot be enforced by this personal repository.

References: [SLSA v1.2 build requirements](https://slsa.dev/spec/v1.2/build-requirements),
[GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations),
[GitHub CLI verification](https://cli.github.com/manual/gh_attestation_verify).
