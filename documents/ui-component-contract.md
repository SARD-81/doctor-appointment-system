# UI Component Contract

This document defines how feature branches should consume the shared frontend foundation.

## Principles

- Feature templates extend the shared layouts instead of creating independent page shells.
- Shared colors, spacing, shadows, radii, and motion come from `static/css/variables.css`.
- Feature branches should not redefine global button, form, card, alert, or badge styles.
- RTL, responsive behavior, keyboard focus, and reduced-motion support are mandatory.
- Business logic remains in Django views/forms/services; templates only represent state and interaction.

## Shared Layouts

### Base layout

```django
{% extends "base.html" %}
```

### Authentication layout

```django
{% extends "layouts/auth.html" %}
```

Authentication pages provide:

- `auth_eyebrow`
- `auth_title`
- `auth_description`
- `auth_content`
- `auth_footer`

## Form Fields

Render a Django form field with:

```django
{% include "components/form_field.html" with field=form.email %}
```

Feature forms should normally use the `.app-form` wrapper.

For password fields that need the shared visibility control, opt in with:

```django
{% include "components/form_field.html" with field=form.password password_toggle=True %}
```

The component renders a `type="button"` toggle wired to the shared `main.js` password-visibility behavior. The native password input remains the submitted form control; the toggle only changes visibility and maintains `aria-pressed` state.

## Doctor Card

The doctor card is intentionally presentation-oriented and avoids coupling to a specific model field layout.

Example:

```django
{% include "components/doctor_card.html" with
    name="دکتر سارا احمدی"
    specialty="متخصص قلب و عروق"
    rating="4.8"
    reviews_count=32
    fee="۳۵۰٬۰۰۰ تومان"
    next_slot="امروز، ۱۸:۳۰"
    verified=True
%}
```

Feature owners should map model values to the component inputs instead of changing global markup for one page.

## Status Badge

```django
{% include "components/status_badge.html" with label="تکمیل شده" tone="success" icon="bi-check-circle" %}
```

Available tones:

- `neutral`
- `success`
- `warning`
- `danger`
- `info`

## Appointment Slot

For display-only usage:

```django
{% include "components/slot_chip.html" with label="۱۸:۳۰" %}
```

For a real booking form, pass both `name` and `value` so the component renders a native radio control whose selected value is submitted with the form:

```django
{% include "components/slot_chip.html" with
    label="۱۸:۳۰"
    name="slot"
    value=slot.id
    selected=slot.is_selected
    disabled=slot.is_unavailable
%}
```

Slot selection uses native radio semantics. The shared JavaScript only synchronizes the visual selected state; form submission does not depend on JavaScript.

Supported states:

- default
- `selected=True`
- `disabled=True`

## Loading State

Use `components/skeleton_doctor_card.html` while async/HTMX doctor results are loading.

## Empty State

```django
{% include "components/empty_state.html" with
    icon="bi-search"
    title="پزشکی پیدا نشد"
    description="عبارت جستجو یا تخصص انتخابی را تغییر دهید."
%}
```

## Motion

Elements may opt into subtle viewport reveal motion using:

```html
<div data-reveal>...</div>
```

The implementation automatically respects `prefers-reduced-motion`.

## Ownership

Changes to global UI primitives, `base.html`, shared CSS, or component contracts must be coordinated with the Team Lead before modification.
