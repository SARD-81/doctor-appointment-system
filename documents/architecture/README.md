# Architecture Documentation

This directory is the navigation point for Architecture Baseline v1.0.

## Core baseline

- [Architecture Baseline v1.0](architecture-baseline-v1.md)
- [ERD — Architecture Baseline v1.0](erd.md)
- [UML 1 — Use Case Diagram](uml-use-case.md)
- [UML 2 — Domain Class Diagram](uml-domain-class.md)
- [UML 3 — Booking Sequence Diagram](uml-booking-sequence.md)
- [ADR index — ADR-001 through ADR-012](../adr/README.md)

## Review and reconciliation

- [Source traceability](source-traceability.md)
- [Implementation status snapshot](implementation-status.md)
- [Architecture review checklist](review-checklist.md)

## Status

The baseline was originally agreed on 2026-09-04 and versioned in the repository on 2026-09-06.

The architecture is **not yet fully frozen**. The remaining freeze conditions include team review, final OTP decision status, reconciliation with final domain migrations, and implementation conformance for the booking transaction contract.

## Source-of-truth rule

When transient feature-branch code conflicts with an accepted baseline decision, do not silently normalize the documentation to that branch. Resolve the branch or record an explicit architecture change through ADR review.
