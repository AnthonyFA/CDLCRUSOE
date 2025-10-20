# pao_generic_project/urls.py (abstracto)
from django.conf import settings
from django.urls import path, re_path
import importlib

PAO_ELEMENT = getattr(settings, "PAO_ELEMENT", "firewall")
APP_NAME = getattr(settings, "APP_NAME", f"{PAO_ELEMENT}_wrapper_project")
VIEWS_MODULE = getattr(settings, "PAO_VIEWS_MODULE", f"{APP_NAME}.views")
views = importlib.import_module(VIEWS_MODULE)

urlpatterns = [
    path("health", views.Health.as_view(), name="health"),
    path("capacity", views.Capacity.as_view(), name="capacity"),
    path("rules", views.Rules.as_view(), name="rules"),
    re_path(r"^rules/(?P<ruleId>[1-9]\d*)$", views.RuleDetail.as_view(), name="rule_detail"),
    path("rules/subject/<str:subject>", views.RulesBySubject.as_view(), name="rules_by_subject"),
]
