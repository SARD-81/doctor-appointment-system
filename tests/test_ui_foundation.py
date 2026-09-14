import re
from importlib import reload
from pathlib import Path

from django.contrib.messages import constants as message_constants
from django.contrib.messages.storage.base import Message
from django.template.loader import render_to_string
from django.test import Client, override_settings
from django.urls import clear_url_caches

from config import urls as project_urls

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def reload_project_urls():
    clear_url_caches()
    reload(project_urls)
    clear_url_caches()


def test_home_page_renders():
    response = Client().get("/")

    assert response.status_code == 200
    assert "نوبت پزشک" in response.content.decode("utf-8")


def test_ui_lab_is_available_when_debug_is_enabled():
    with override_settings(DEBUG=True):
        reload_project_urls()

        response = Client().get("/__ui__/")

        assert response.status_code == 200
        assert "آزمایشگاه رابط کاربری" in response.content.decode("utf-8")

    reload_project_urls()


def test_ui_lab_is_hidden_when_debug_is_disabled():
    with override_settings(DEBUG=False):
        reload_project_urls()

        response = Client().get("/__ui__/")

        assert response.status_code == 404

    reload_project_urls()


def test_slot_chip_renders_submittable_selected_radio():
    html = render_to_string(
        "components/slot_chip.html",
        {
            "label": "۱۰:۳۰",
            "name": "slot",
            "value": "42",
            "selected": True,
        },
    )

    assert 'type="radio"' in html
    assert 'name="slot"' in html
    assert 'value="42"' in html
    assert "data-slot-radio" in html
    assert "checked" in html


def test_disabled_slot_chip_disables_form_control():
    html = render_to_string(
        "components/slot_chip.html",
        {
            "label": "۱۱:۰۰",
            "name": "slot",
            "value": "43",
            "disabled": True,
        },
    )

    assert 'type="radio"' in html
    assert "disabled" in html
    assert 'aria-disabled="true"' in html


def test_message_extra_tags_do_not_override_error_severity():
    message = Message(
        message_constants.ERROR,
        "رزرو ناموفق بود.",
        extra_tags="checkout",
    )

    html = render_to_string("components/messages.html", {"messages": [message]})

    assert "alert-danger" in html
    assert "alert-info" not in html


def test_theme_is_initialized_before_styles_and_toggle_is_rendered():
    response = Client().get("/")
    html = response.content.decode("utf-8")

    assert "localStorage.getItem(storageKey)" in html
    assert "prefers-color-scheme: dark" in html
    assert html.index("doctor-appointment-theme") < html.index("css/variables.css")
    assert "data-theme-toggle" in html
    assert 'aria-pressed="false"' in html


def test_component_styles_use_theme_tokens_instead_of_hardcoded_colors():
    color_literal = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(")
    violations = []

    for stylesheet in (PROJECT_ROOT / "static" / "css").glob("*.css"):
        if stylesheet.name == "variables.css":
            continue
        for line_number, line in enumerate(stylesheet.read_text().splitlines(), start=1):
            if color_literal.search(line):
                violations.append(f"{stylesheet.name}:{line_number}")

    assert violations == []


def test_dark_theme_defines_the_core_surface_and_text_tokens():
    tokens = (PROJECT_ROOT / "static" / "css" / "variables.css").read_text()

    assert ':root[data-theme="dark"]' in tokens
    assert "--color-bg:" in tokens
    assert "--color-surface:" in tokens
    assert "--color-text:" in tokens
    assert "--color-muted:" in tokens
    assert "--color-border:" in tokens
