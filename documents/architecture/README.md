# Architecture Documentation

This directory is the navigation point for Architecture Baseline v1.0.

## Core baseline

- [Architecture Baseline v1.0](architecture-baseline-v1.md)
- [ERD — Architecture Baseline v1.0](erd.md)
- [UML 1 — Use Case Diagram](uml-use-case.md)
- [UML 2 — Domain Class Diagram](uml-domain-class.md)
- [UML 3 — Booking Sequence Diagram](uml-booking-sequence.md)
- [ADR index — ADR-001 through ADR-013](../adr/README.md)

## Review and reconciliation

- [Source traceability](source-traceability.md)
- [Implementation status snapshot](implementation-status.md)
- [Architecture review checklist](review-checklist.md)

## Status

The baseline was originally agreed on 2026-09-04 and versioned in the repository on 2026-09-06.

Architecture Baseline v1.0 is implemented across the integrated domains. Future changes to domain boundaries, financial invariants, OTP persistence, or appointment lifecycle require an explicit ADR amendment and migration review.

## Source-of-truth rule

When transient feature-branch code conflicts with an accepted baseline decision, do not silently normalize the documentation to that branch. Resolve the branch or record an explicit architecture change through ADR review.
