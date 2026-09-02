from importlib import reload

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
