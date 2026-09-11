# Team Contract

## Team

- Team Lead / Product & Application Owner: `SARD-81`
- Docker / Infrastructure Developer: `Mahsa-Alipour`
- Docker / Infrastructure Developer: `amirrezaparvaneh`

## Current Ownership Model

Effective from the final-delivery ownership consolidation, all remaining **non-Docker application work** is owned by the Team Lead (`SARD-81`).

This includes, unless explicitly reassigned:

- application/domain models and migrations;
- business/domain services;
- Wallet and payment ledger behavior;
- BookingService and booking transaction orchestration;
- Review/rating domain and eligibility rules;
- Django views, URLs, forms, templates, UI integration, and frontend behavior;
- application-level tests and integration tests;
- cross-domain application integration and final merge decisions.

Mahsa and Amirreza own **Docker/infrastructure work only** for the remainder of the project.

### Mahsa Docker ownership

- Issue #19 — Development Compose + Django + PostgreSQL integration.
- Issue #21 — Production Compose + Nginx + environment/release wiring when the Team Lead opens the production phase.

### Amirreza Docker ownership

- Docker compatibility/review support for Issue #19.
- Issue #20 — Production Django/Gunicorn image when the Team Lead opens the production phase.

Previous merged work remains credited to its original author. Existing non-Docker branches/PRs owned by Mahsa or Amirreza must not continue or merge unless the Team Lead explicitly reassigns them.

Docker work must not modify application domain models, business services, views, templates, or product behavior unless coordinated and explicitly approved by the Team Lead.

## Active Application Delivery Path

The Team Lead owns the remaining application sequence:

1. Issue #23 — doctor detail + available slots.
2. Issue #24 — Wallet domain + top-up service + wallet UI.
3. Issue #25 — atomic BookingService + booking/appointment UI.
4. Issue #26 — Review domain + eligibility service + review/rating UI.

The application path should not wait on Docker work unless a feature genuinely requires Docker-only verification.

## Core Rules

1. Direct pushes to `main` and `develop` are forbidden.
2. Every development task must have a GitHub Issue.
3. Every task is implemented in its own short-lived branch.
4. Every branch must be created from the latest `develop`.
5. Every change reaches `develop` through a Pull Request.
6. Feature code without appropriate tests is not considered complete.
7. Shared architecture and cross-domain contracts must not be changed without Team Lead approval.
8. Secrets, credentials, tokens, and real `.env` files must never be committed.
9. Each developer is responsible for resolving conflicts introduced by their branch.
10. Pull Requests must stay inside the assigned ownership/scope.
11. Squash Merge is the default strategy for normal feature/chore Pull Requests.
12. Green CI and Team Lead review are required before merge.

## Definition of Ready for Review

Before requesting final review, run the applicable quality gates:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
ruff check .
ruff format --check .
pytest -q
```

Docker issues must additionally execute and document the Docker/Compose verification required by their own acceptance criteria.

## Daily Communication

Each developer reports:

- what was completed;
- what is being worked on now;
- whether there is a blocker.

A blocker that cannot be resolved quickly should be surfaced to the Team Lead instead of silently delaying the project.

## Work In Progress

Mahsa and Amirreza should each have only their current Docker task in progress.

The Team Lead may sequence the remaining application issues aggressively to complete the mandatory project scope, while still keeping one clean PR per Issue.

## Local Git Safety

All team members must enable repository Git hooks after cloning:

```bash
./scripts/setup-git-hooks.sh
```

The local hook blocks direct pushes to `main` and `develop`. It complements, but does not replace, Pull Requests, CI, and human review.

## Release

`develop` is the integration branch.

`main` represents stable release-ready code.

Only reviewed and tested code from `develop` may be promoted to `main` by the Team Lead.
