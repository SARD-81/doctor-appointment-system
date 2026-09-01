# Git Workflow

## Permanent Branches

- `main`: stable, release-ready code only.
- `develop`: team integration branch for reviewed feature work.

Direct pushes to both branches are forbidden after project bootstrap.

## Temporary Branches

Create one short-lived branch per GitHub Issue:

- `feature/*` - new product functionality
- `fix/*` - bug fixes
- `test/*` - test-only improvements
- `refactor/*` - behavior-preserving refactors
- `docs/*` - documentation changes
- `chore/*` - tooling, CI, repository maintenance

Examples:

```text
feature/doctor-domain
feature/account-authentication
feature/atomic-booking
fix/otp-expiration
chore/engineering-governance
```

## Starting a Task

Always start from the latest `develop`:

```bash
git switch develop
git pull --ff-only origin develop
git switch -c feature/task-name
```

The branch name should describe the Issue, not the developer.

## Working on the Task

Use small, focused commits and the agreed commit prefixes:

```text
feat:
fix:
test:
refactor:
docs:
chore:
```

Example:

```bash
git add .
git commit -m "feat: add doctor specialty models"
```

Do not commit secrets, `.env`, local databases, virtual environments, or debug-only files.

## Before Opening a Pull Request

First verify the feature locally:

```bash
python manage.py check
ruff check .
ruff format --check .
pytest -q
```

Then synchronize the branch with the latest integration state:

```bash
git fetch origin
git merge origin/develop
```

If there is a conflict, the developer who owns the feature branch resolves it and reruns all checks.

## Pull Request Rules

Feature branches target `develop`.

Release Pull Requests target `main`.

Every Pull Request must include:

- Related GitHub Issue
- Clear summary of the change
- Test results
- Migration information when relevant
- Confirmation that no unrelated files were changed

The Pull Request is not mergeable until CI is green and review feedback is resolved.

## Merge Strategy

Use **Squash Merge** for normal feature Pull Requests so each completed Issue becomes one clean commit in `develop`.

Do not merge feature branches directly into `main`.

## Release Flow

```text
Issue
  |
  v
feature/*
  |
  v
Pull Request + CI + Review
  |
  v
develop
  |
  v
Integration / Regression Test
  |
  v
Release Pull Request
  |
  v
main
```

Only the Team Lead promotes tested code from `develop` to `main`.

## Recommended Daily Commands

Starting work:

```bash
git switch develop
git pull --ff-only origin develop
git switch feature/my-current-task
```

Before pushing:

```bash
python manage.py check
ruff check .
ruff format --check .
pytest -q
git status
git push
```

## Definition of a Healthy Branch

A branch is ready for review only when:

- Its scope matches one Issue.
- It is synchronized with current `develop`.
- Django system checks pass.
- Ruff passes.
- All tests pass.
- Required migrations are included.
- No secrets or unrelated changes are present.
