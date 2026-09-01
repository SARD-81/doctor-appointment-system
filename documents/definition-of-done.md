# Definition of Done

A task is considered Done only when all applicable conditions below are satisfied.

## Implementation

- Requirement is fully implemented.
- Acceptance criteria are satisfied.
- Business rules are enforced server-side.
- Code follows the agreed architecture.
- No unrelated changes are included.

## Database

- Models are valid.
- Required constraints are enforced.
- Migrations are included.
- Migration history is valid.

## Quality

- `python manage.py check` passes.
- `ruff check .` passes.
- `ruff format --check .` passes.
- All automated tests pass.
- New business behavior has appropriate tests.

## Security

- No secrets are committed.
- Authorization is checked server-side.
- Sensitive input is validated.
- Debug-only code is removed.

## Git

- Work is linked to an Issue.
- Changes are submitted through a Pull Request.
- CI passes.
- Review feedback is resolved.
- PR is merged into `develop`.

## Release Definition of Done

A release additionally requires:

- Fresh clone can be configured from documentation.
- Docker build succeeds.
- Docker Compose starts required services.
- Production settings are valid.
- Static files can be collected.
- Full test suite passes.
- README is current.
- ERD is current.
- Presentation and final documentation are ready.
