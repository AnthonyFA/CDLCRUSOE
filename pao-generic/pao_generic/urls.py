"""
Generic Project URL Configuration for a CRUSOE PAO wrapper.

- Exposes the Django admin.
- Mounts the app URLConf under a configurable prefix (PAO_SLUG / PAO_ELEMENT).
- Works for any wrapper by setting PAO_SLUG/PAO_ELEMENT and APP_URLCONF in settings.py.
"""
from django.contrib import admin
from django.conf import settings
from django.urls import path, include

# Resolve public URL prefix: prefer PAO_SLUG, fallback to PAO_ELEMENT, then "firewall".
PAO_PREFIX: str = getattr(settings, "PAO_SLUG", None) or getattr(settings, "PAO_ELEMENT", "firewall")

# Resolve app urlconf: prefer explicit APP_URLCONF, fallback to convention "{slug}_wrapper_project.urls".
APP_URLCONF: str = getattr(settings, "APP_URLCONF", f"{PAO_PREFIX}_wrapper_project.urls")

urlpatterns = [
    path("admin/", admin.site.urls),
    path(f"{PAO_PREFIX}/", include(APP_URLCONF)),
]
