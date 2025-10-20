"""
ASGI config for pao_generic.

This module exposes the ASGI callable as a module-level variable named ``application``.

Resolution order for settings module:
  1) Respect existing environment variable DJANGO_SETTINGS_MODULE (if set).
  2) Otherwise, derive from PAO_ELEMENT (default: "firewall"):
       DJANGO_SETTINGS_MODULE = f"{PAO_ELEMENT}_wrapper.settings"

This allows a single ASGI entrypoint to serve any PAO wrapper (firewall/dnsfw/userBlock/mailFilter/rtbh/custom)
by setting PAO_ELEMENT or DJANGO_SETTINGS_MODULE in the environment.

Docs:
  https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

# 1) If DJANGO_SETTINGS_MODULE is already set, respect it.
_settings = os.environ.get("DJANGO_SETTINGS_MODULE")

# 2) Otherwise, derive it from PAO_ELEMENT using the naming convention "<slug>_wrapper.settings".
if not _settings:
    pao_element = os.environ.get("PAO_ELEMENT", "firewall")
    _settings = f"{pao_element}_wrapper.settings"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", _settings)

application = get_asgi_application()
