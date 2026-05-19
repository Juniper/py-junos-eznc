---
name: run-code-quality-tool
description: "Use when source code changes under lib/jnpr/junos and the user wants to run static code analysis and code format using pylint and ruff"
allowed-tools:
  - run_in_terminal
  - read_file
  - get_changed_files
  - grep_search
context: fork
---

# Run Code Quality Tool

## Goal
Run formatting checks and static analysis for Python changes under `lib/jnpr/junos`.

## Required Workflow

### 1) Install required code-quality tools
Install pylint and ruff before running checks:
- `python3 -m pip install pylint ruff`

### 2) Detect changed Python source files
Collect changed files under `lib/jnpr/junos` and keep only `.py` files.

Preferred commands:
- `git diff --name-only -- lib/jnpr/junos | grep -E '\\.py$'`
- `git diff --name-only --cached -- lib/jnpr/junos | grep -E '\\.py$'`

### 3) Run ruff format check for diff files
Run formatting check for only changed Python files under `lib/jnpr/junos`:
- `CHANGED=$( (git diff --name-only -- lib/jnpr/junos; git diff --name-only --cached -- lib/jnpr/junos) | grep -E '\\.py$' | sort -u )`
- `if [ -n "$CHANGED" ]; then echo "$CHANGED" | xargs -I{} ruff format --check "{}"; else echo "No changed Python files under lib/jnpr/junos"; fi`

### 4) Run pylint for changed files under lib/jnpr/junos
Run pylint for only changed Python files first:
- `CHANGED=$( (git diff --name-only -- lib/jnpr/junos; git diff --name-only --cached -- lib/jnpr/junos) | grep -E '\\.py$' | sort -u )`
- `if [ -n "$CHANGED" ]; then pylint $CHANGED --exit-zero; else echo "No changed Python files under lib/jnpr/junos"; fi`

### 5) Optional full ruff format for all Python files
If requested, run ruff format across all tracked Python files:
- `git ls-files '*.py' | xargs -I{} ruff format "{}"`

### 6) Optional full pylint command
If requested, run the broader pylint command:
- `pylint $(git ls-files '*.py' | grep -vE '^(docs/|build/|tests/|samples/|setup.py|versioneer.py)') --exit-zero`

## Output Contract
When this skill is invoked, the final response must include:
1. Changed Python files detected under `lib/jnpr/junos`.
2. `ruff format --check` result for changed files.
3. `pylint` result for changed files.
4. If optional full ruff format was run, include that result separately.
5. If full pylint was run, include that result separately.


