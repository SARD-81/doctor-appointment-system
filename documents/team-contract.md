# Team Contract

## Team

- Team Lead: SARD-81
- Developer: mahsa-alipour
- Developer: amirrezaparvaneh

## Core Rules

1. Direct pushes to `main` and `develop` are forbidden after project bootstrap.
2. Every development task must have a GitHub Issue.
3. Every task is implemented in its own branch.
4. Every branch must be created from the latest `develop`.
5. Every change reaches `develop` through a Pull Request.
6. Feature code without appropriate tests is not considered complete.
7. Shared architecture and cross-domain contracts must not be changed without Team Lead coordination.
8. Secrets, credentials, tokens, and real `.env` files must never be committed.
9. Each developer is responsible for resolving conflicts introduced by their feature branch.
10. Pull Requests must be small enough to review properly.

## Daily Communication

Each developer reports:

- What was completed?
- What is being worked on now?
- Is there any blocker?

A blocker that cannot be resolved within roughly one hour should be communicated to the team instead of being silently carried forward.

## Work In Progress

Each developer should normally have only one primary task in progress.

Finishing one feature is preferred over partially implementing several features.

## Review

A Pull Request must include:

- Related Issue
- Description of changes
- Test result
- Migration information when relevant

The Team Lead owns final integration decisions.

## Release

`develop` is the integration branch.

`main` represents stable release-ready code.

Only tested code from `develop` may be promoted to `main`.

## Local Git Safety

All team members must enable the repository Git hooks after cloning:

```bash
./scripts/setup-git-hooks.sh
```

Direct pushes to `main` and `develop` are prohibited. The local pre-push hook exists to prevent accidental violations of this rule.

Because the current private repository plan does not provide server-side branch protection, compliance with the Pull Request workflow is a mandatory team responsibility.

## Review Responsibility

- Pull Requests created by Mahsa or Amirreza require Team Lead review before merge.
- Pull Requests created by the Team Lead should be reviewed by at least one other team member when practical.
- A green CI run is required before any merge.
- Squash Merge is the standard merge strategy.
