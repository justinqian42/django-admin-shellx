from django.contrib import admin
from django.contrib.admin import autodiscover
from django.urls import NoReverseMatch, reverse


class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        # Ensure admin modules are registered before URL patterns are built.
        autodiscover()
        return super().get_urls()

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)

        for app in app_list:
            if app["app_label"] == "django_admin_shellx":
                try:
                    terminal_url = reverse(
                        "admin:django_admin_shellx_terminalcommand_terminal"
                    )
                except NoReverseMatch:
                    break

                app["models"].insert(
                    0,
                    {
                        "name": "Terminal",
                        "object_name": "Terminal",
                        "admin_url": terminal_url,
                        "view_only": True,
                    },
                )
                break

        return app_list
