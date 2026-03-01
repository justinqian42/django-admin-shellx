import pytest
from django.test import RequestFactory
from django.urls import NoReverseMatch

from django_admin_shellx_custom_admin.admin import CustomAdminSite

pytestmark = pytest.mark.django_db


def test_custom_admin_adds_terminal_entry(monkeypatch):
    site = CustomAdminSite(name="admin")

    fake_app_list = [{"app_label": "django_admin_shellx", "models": []}]

    monkeypatch.setattr(
        "django.contrib.admin.sites.AdminSite.get_app_list",
        lambda *_args, **_kwargs: fake_app_list,
    )
    monkeypatch.setattr(
        "django_admin_shellx_custom_admin.admin.reverse",
        lambda *_args, **_kwargs: (
            "/admin/django_admin_shellx/terminalcommand/terminal/"
        ),
    )

    app_list = site.get_app_list(request=RequestFactory().get("/admin/"))

    assert app_list[0]["models"][0]["object_name"] == "Terminal"
    assert (
        app_list[0]["models"][0]["admin_url"]
        == "/admin/django_admin_shellx/terminalcommand/terminal/"
    )


def test_custom_admin_skips_terminal_entry_when_reverse_fails(monkeypatch):
    site = CustomAdminSite(name="admin")

    fake_models = [{"object_name": "TerminalCommand", "admin_url": "/admin/x/"}]
    fake_app_list = [{"app_label": "django_admin_shellx", "models": fake_models.copy()}]

    monkeypatch.setattr(
        "django.contrib.admin.sites.AdminSite.get_app_list",
        lambda *_args, **_kwargs: fake_app_list,
    )

    def reverse_raises(*_args, **_kwargs):
        raise NoReverseMatch("missing")

    monkeypatch.setattr(
        "django_admin_shellx_custom_admin.admin.reverse", reverse_raises
    )

    app_list = site.get_app_list(request=RequestFactory().get("/admin/"))

    assert app_list[0]["models"] == fake_models
