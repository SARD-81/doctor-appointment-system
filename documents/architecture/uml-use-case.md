# UML 1 — Use Case Diagram

The use-case baseline defines the mandatory patient/admin scope and the optional external OAuth bonus.

```mermaid
flowchart LR
    P[Patient]
    A[Admin]
    G[Google OAuth<br/>optional bonus]
    E[Email Service]

    subgraph SYS[Doctor Appointment System]
        U1((Register / Login))
        U2((Verify OTP))
        U3((Search doctor<br/>name / specialty))
        U4((Simulated wallet top-up))
        U5((View available slots))
        U6((Book appointment))
        U7((View appointments))
        U8((Review & rate<br/>completed appointment))
        U9((Send booking confirmation))
        A1((Manage specialties))
        A2((Manage doctors & visit fee))
        A3((Manage appointment slots))
        A4((Mark appointment completed))
        O1((Login with Google<br/>optional bonus))
    end

    P --> U1
    P --> U2
    P --> U3
    P --> U4
    P --> U5
    P --> U6
    P --> U7
    P --> U8

    U6 -. includes .-> U5
    U6 -. includes .-> U9
    U8 -. eligible only if COMPLETED .-> U7
    U9 --> E

    A --> A1
    A --> A2
    A --> A3
    A --> A4

    O1 --> G
```

## Architecture notes

- `Doctor` is **not** an actor in baseline v1.0 because no doctor login/panel is a mandatory requirement.
- Admin is an actor backed by Django authentication/permissions; there is no separate `Admin` entity in the ERD.
- Review/rating eligibility requires a completed appointment.
- OTP persistence details remain pending under ADR-012.
