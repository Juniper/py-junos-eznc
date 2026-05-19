## Description

<!-- A concise summary of the changes in this PR. Reference related issues where applicable. -->

Closes #<!-- issue number -->

## Type of Change

<!-- Check all that apply -->

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] Feature / Enhancement (non-breaking change that adds functionality)
- [ ] Task / Chore (refactor, dependency update, CI, docs, etc.)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)

## Changes Made

<!-- List the key changes introduced by this PR -->

-
-
-

---

## Checklist

### Code Quality

- [ ] Code follows the project's style guidelines
- [ ] `ruff format --check .` passes with no formatting issues
- [ ] `pylint` reports no new errors or warnings (run against changed `.py` files)

```bash
ruff format --check .
pylint <changed_files>
```

### Unit Tests

- [ ] New or updated unit tests have been added under `tests/unit/`
- [ ] All unit tests pass locally

```bash
nose2 -vvv tests.unit --with-coverage --coverage-report xml
```

- [ ] Code coverage has not decreased (check `coverage.xml`)

### Functional Tests

- [ ] Functional tests in `tests/functional/` have been reviewed for impact
- [ ] Any affected functional tests pass (requires a live Junos device or vMX)

```bash
nose2 -vvv tests.functional
```

### Documentation

- [ ] Docstrings updated for any new/changed public methods or classes
- [ ] Sphinx docs build cleanly (if docs were changed)

```bash
sphinx-build -b html docs docs/_build/html -W
```

### General

- [ ] `RELEASE-NOTES.md` updated (if applicable)
- [ ] No hardcoded credentials, IPs, or sensitive data introduced
- [ ] Dependencies in `requirements.txt` updated (if new packages were added)

---

## Testing Matrix

<!-- Confirm which Python versions / OS combinations you tested locally, if any -->

| Python | OS | Passed? |
|--------|----|---------|
| 3.x    |    | [ ]     |

---

## Additional Notes

<!-- Anything else reviewers should know: deployment considerations, follow-up tasks, known limitations, etc. -->
