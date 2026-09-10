# Software Engineering Working Agreement

## Scope and definition of done

These instructions apply to all work in this repository.

- A requested task is not done until its result has been validated and committed to Git.
- Break work into small, coherent subtasks whenever possible. Each subtask must independently follow the full implement, validate, review, and commit cycle before starting the next dependent subtask.
- Make frequent atomic commits. Each commit must represent one logical, working change and include the tests and documentation needed for that change.
- If validation or committing is blocked, report the blocker and the incomplete state. Do not claim completion or treat unavailable checks as passing.
- Revert failed or abandoned work. Preserve unrelated user changes and previously validated work.

## Correctness first

- Read applicable guidance and inspect the existing code, tests, and Git status before editing.
- Identify the expected behavior, acceptance criteria, relevant constraints, and likely failure cases before implementation. Resolve material ambiguity rather than guessing at requirements.
- Prefer the smallest clear solution that satisfies the requirements. Follow existing architecture and conventions; avoid unrelated refactors, speculative abstractions, and unnecessary dependencies.
- Maintain explicit invariants, validate inputs at appropriate boundaries, handle errors deliberately, and preserve compatibility unless a change is requested.
- Consider edge cases, security, data integrity, resource cleanup, and concurrency where relevant. Never hide failures or weaken checks to make a change appear successful.

## Incremental workflow

1. Inspect the starting state and identify any existing user changes. Define one bounded subtask and how its success will be verified.
2. Implement only that subtask, keeping the diff small and reviewable.
3. Add or update meaningful tests as appropriate, then run the relevant validation against the final changes.
4. Review the diff for correctness, scope, accidental changes, secrets, and unnecessary generated files. Fix findings and rerun affected checks after edits.
5. Stage only the intended changes, inspect the staged diff, and make an atomic conventional commit.
6. Verify the commit and Git status, then proceed to the next subtask. Report the completed changes, validation results, and commit identifiers when handing off.

Do not accumulate multiple completed subtasks into a single end-of-task commit. Keep each intermediate commit coherent and usable.

## Testing and validation

- Select checks based on the behavior and risk of the change. Run required repository checks and relevant tests, linting, type checks, and builds when applicable.
- For bug fixes, add a regression test when practical and confirm that it exposes the original defect before verifying the fix.
- Test observable behavior and important failure paths. Use integration or end-to-end checks when correctness depends on interactions that unit tests cannot verify.
- Keep tests deterministic and independent. Avoid tests that merely mirror implementation details or assertions weakened to accommodate a defect.
- Documentation and configuration changes still require validation: review accuracy and consistency, check formatting and references as applicable, and run available targeted validators. Do not invent low-value tests solely to satisfy a checklist.
- Record which checks ran and their outcomes. Distinguish existing failures, new failures, and checks that could not run. A new failure must be fixed or the responsible change reverted before the subtask can be completed.
- Validate the final state being committed; earlier successful checks do not cover subsequent behavior changes.

## Git discipline

- Use conventional commit messages: `type(optional-scope): imperative description`.
- Choose an appropriate type, such as `feat`, `fix`, `refactor`, `test`, `docs`, `build`, `ci`, `perf`, or `chore`. Example: `fix(parser): reject malformed dates`.
- Use `!` and a `BREAKING CHANGE:` footer for intentional breaking changes, and explain the impact and migration when needed.
- Include a commit body when it helps explain the reason for a change, tradeoffs, or validation.
- Never commit secrets, unrelated user edits, temporary debugging artifacts, or known failing work.
- Do not amend, rewrite history, force-push, or publish changes unless authorized. Local commits are required by this agreement; pushing is a separate action.

## Failed work and recovery

- When an approach fails, diagnose it and either repair it within the current bounded subtask or revert that approach before trying another.
- Revert only changes made for the failed work. Do not use broad destructive resets or restores that could remove user changes or successful subtasks.
- If failed work was already committed, normally undo it with a targeted revert commit rather than rewriting history. Validate the restored state and use a conventional commit message such as `fix: revert invalid cache behavior`.
- After recovery, inspect the diff and Git status to confirm that failed changes are gone and unrelated work is intact. Report unresolved blockers honestly.
