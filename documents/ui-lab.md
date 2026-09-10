# UI Lab

The project includes an internal development-only UI laboratory at:

```text
/__ui__/
```

The route must only be registered while `DEBUG=True`.

## Purpose

The lab is the visual reference for shared frontend primitives and states:

- Buttons and action hierarchy
- Forms and validation states
- Status badges
- Rating
- Doctor cards
- Appointment slot chips
- Skeleton loading
- Empty, error, and success states
- Authentication surface

## Rule

Feature branches should consume the shared components demonstrated in the UI Lab rather than creating independent global styles.

The lab is not a product page and should never be enabled as a public production route.
