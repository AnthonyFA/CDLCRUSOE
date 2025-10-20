"""
WSGI config for pao_generic.

Exposes the WSGI callable as a module-level variable named ``application``.

Settings resolution order:
  1) Respect existing DJANGO_SETTINGS_MODULE if present.
  2) Otherwise, derive from PAO_ELEMENT (default: "firewall"):
       DJANGO_SETTINGS_MODULE = f"{PAO_ELEMENT}_wrapper.settings"

Docs:
  https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""
import os
from typing import Optional
from django.core.wsgi import get_wsgi_application

_settings: Optional[str] = os.environ.get("DJANGO_SETTINGS_MODULE")
if not _settings:
    pao_element: str = os.environ.get("PAO_ELEMENT", "firewall")
    _settings = f"{pao_element}_wrapper.settings"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", _settings)

application = get_wsgi_application()
