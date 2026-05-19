---
name: generate-test-cases
description: "Use when source code changes under lib/jnpr/junos and the user wants unit tests created or updated for those changes."
allowed-tools:
  - read_file
  - file_search
  - grep_search
  - run_in_terminal
  - apply_patch
  - get_errors
  - get_changed_files
context: fork
---

# Generate Unit Tests For PyEZ Source Changes

## Goal
Create or update unit tests for code changes under `lib/jnpr/junos`, matching the existing project style in `tests/unit`.

## Use This Skill When
- The user asks to write unit tests for modified source code.
- The requested scope is changes under `lib/jnpr/junos`.
- The user expects actual test files/edits, not only a coverage review.

## Do Not Use This Skill When
- The task is only test planning or test-case enumeration without code changes.
- The task is functional/integration test authoring under `tests/functional`.

## Required Workflow

### 1) Detect changed source files
Collect changed files and keep only paths under `lib/jnpr/junos`.

Preferred commands:
- `git diff --name-only -- lib/jnpr/junos`
- `git diff --name-only --cached -- lib/jnpr/junos`

If both are empty, ask for the exact files or compare against the upstream default branch:
- `git diff --name-only origin/master...HEAD -- lib/jnpr/junos`

### 2) Map source file to unit test location
Use these conventions first, then adjust to existing repository layout:
- `lib/jnpr/junos/device.py` -> `tests/unit/test_device.py`
- `lib/jnpr/junos/console.py` -> `tests/unit/test_console.py`
- `lib/jnpr/junos/facts/<name>.py` -> `tests/unit/facts/test_<name>.py`
- `lib/jnpr/junos/factory/<name>.py` -> `tests/unit/factory/test_<name>.py`
- `lib/jnpr/junos/utils/<name>.py` -> `tests/unit/utils/test_<name>.py`

If no matching test file exists, create one in the appropriate test subdirectory with naming `test_<module>.py`.

### 3) Learn local testing style before writing
Read nearby tests and follow established conventions:
- `unittest`/`unittest2` style classes and `test_*` methods.
- Heavy use of `unittest.mock` (`patch`, `MagicMock`, `mock_open`).
- Keep fixtures and mocked RPC replies consistent with existing patterns in `tests/unit/**/rpc-reply`.

### 4) Implement tests for behavior, not implementation details
Cover only behavior changed by the source diff.

For each changed behavior, include positive and negative paths when applicable:
- successful path and return value/side effects
- raised exception or error mapping
- edge cases (None, empty input, malformed values)
- compatibility branches if present (for example Python-version or platform branches)

Avoid brittle assertions on internal private state unless that is the public contract used across this repo.

### 5) Keep edits minimal and scoped
- Do not refactor unrelated tests.
- Do not reformat unrelated files.
- Reuse existing helpers and fixtures before adding new ones.

### 6) Validate quickly with targeted test runs
Install required dependencies before executing tests:
- `python3 -m pip install ntc_templates==1.4.1 textfsm==0.4.1 `
- `python3 -m pip install -r requirements.txt`
- `python3 -m pip install nose2 junos-eznc`


Run generated/updated testcase modules first (targeted validation), for example:
- `nose2 -vvv tests.unit.facts.test_<name> --plugin nose2.plugins.junitxml --junit-xml`
- `nose2 -vvv tests.unit.test_<module> --plugin nose2.plugins.junitxml --junit-xml`

Only after targeted tests pass, optionally run the broader unit suite:
- `nose2 -vvv tests.unit --plugin nose2.plugins.junitxml --junit-xml`

### 7) Report results
Summarize:
- changed source files detected
- test files created/updated
- scenarios covered
- test command(s) run and pass/fail outcome
- remaining risks or uncovered branches

Include the generated testcase execution output in verbose format from `nose2 -vvv`.
At minimum, include:
- one line per testcase with status (`... ok` / `... FAIL` / `... ERROR`)
- final summary block (`Ran X tests in Ys` and final status)

## Output Contract
When this skill is invoked, the final response must include:
1. Source-to-test mapping used.
2. Exact test files modified.
3. What behaviors each new/updated test verifies.
4. Validation command summary and outcomes.
5. Verbose generated testcase output (or key excerpt) from `nose2 -vvv`.

