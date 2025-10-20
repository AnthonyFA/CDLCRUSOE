#!/usr/bin/env python
"""Django's command-line utility for administrative tasks (generic PAO).

Resolution order for settings:
  1) Respect DJANGO_SETTINGS_MODULE if already set.
  2) Else, if PAO_ELEMENT is set -> use "<PAO_ELEMENT>_wrapper.settings".
  3) Else, fallback to "pao_generic.settings".
"""
import os
import sys


def main() -> None:
    settings_module = os.environ.get("DJANGO_SETTINGS_MODULE")
    if not settings_module:
        pao_element = os.environ.get("PAO_ELEMENT")
        if pao_element:
            settings_module = f"{pao_element}_wrapper.settings"
        else:
            settings_module = "pao_generic.settings"
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Is it installed and on your PYTHONPATH? "
            "Did you forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
