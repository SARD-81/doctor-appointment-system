from importlib import reload

from django.contrib.messages import constants as message_constants
from django.contrib.messages.storage.base import Message
from django.template.loader import render_to_string
from django.test import Client, override_settings
from django.urls import clear_url_caches

from config import urls as project_urls


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
