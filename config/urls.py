from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path(
        "",
        TemplateView.as_view(template_name="home.html"),
        name="home",
    ),
    path("accounts/", include("apps.accounts.urls")),
    path("doctors/", include("apps.doctors.urls")),
    path("admin/", admin.site.urls),
]


if settings.DEBUG:
    urlpatterns += [
        path(
            "__ui__/",
            TemplateView.as_view(template_name="ui_lab.html"),
            name="ui_lab",
        ),
    ]
