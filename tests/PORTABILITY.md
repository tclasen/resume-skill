# Portability validation

On 2026-09-10, skills CLI 1.5.25 installed this package with `--all --copy` for
all 79 supported agent targets, covering 55 distinct project directories.
Multiple agents share a directory. Each installed path retained the complete
runtime assets and skill instructions and passed `resume.py pins`.

The official Eve adapter reformats frontmatter and omits `name`/`compatibility`;
its description and workflow body remain intact. The package does not bypass
that adapter or depend on a host-specific frontmatter extension.

Reproduce in a new temporary project directory, not an existing agent project:

```sh
DISABLE_TELEMETRY=1 npx --yes skills@1.5.25 add tclasen/resume-skill --all --copy
```

Then, from this source checkout:

```sh
.venv/bin/python tests/verify_installation.py <temporary-install-root> --expected-paths 55
.venv/bin/python -m unittest discover -s tests -v
```

The standard suite also copies only the skill directory into a separate private
repository, removes `PYTHONPATH`, and executes pin checking, assessment, and both
document exports from the private repository's working directory. This detects
accidental dependencies on the source checkout or a specific agent directory.

The observed run used macOS and Python 3.14. Installation checks do not launch all
agent products or evaluate their models. Host-specific browsing and document
viewing remain capability requirements stated in the skill. No installation
or test above publishes the repository or sends applicant data.
