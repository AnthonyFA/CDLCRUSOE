# pao_generic_project/views.py — abstract

from __future__ import annotations
from typing import Any, Dict, Optional, Type
import importlib

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView


# -----------------------------
# Domain-agnostic exceptions
# -----------------------------
class ServiceUnavailableError(Exception):
    """Backend is down or unreachable (-> 503)."""


class NotSupportedError(Exception):
    """Functionality not supported by backend (-> 403)."""


class NotFoundError(Exception):
    """Resource not found (-> 404)."""


class ValidationError(Exception):
    """Invalid input/payload (-> 400)."""


# -----------------------------
# Service resolver (DI via settings)
# -----------------------------
def _import_object(dotted_path: str) -> Any:
    """
    Import "pkg.module:Class" or "pkg.module.Class".
    """
    if ":" in dotted_path:
        module_path, obj_name = dotted_path.split(":", 1)
    else:
        module_path, obj_name = dotted_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, obj_name)


def get_pao_service() -> Any:
    dotted = getattr(settings, "PAO_SERVICE_CLASS", None)
    if not dotted:
        raise ImproperlyConfigured(
            "PAO_SERVICE_CLASS is not configured. "
            "Set it to the dotted path of a service implementing the generic PAO contract."
        )
    svc_cls: Type[Any] = _import_object(dotted)
    try:
        return svc_cls()  # Adapt if your service requires args/factory
    except Exception as exc:
        raise ImproperlyConfigured(f"Cannot instantiate PAO_SERVICE_CLASS '{dotted}': {exc}") from exc


# -----------------------------
# Base view mixin
# -----------------------------
class PAOViewMixin:
    SERVICE_UNAVAILABLE_MSG = "Service unavailable!"
    FUNCTION_NOT_SUPPORTED_MSG = "Function not supported!"
    RESOURCE_NOT_FOUND_MSG = "Resource not found!"

    def svc(self) -> Any:
        return get_pao_service()

    @staticmethod
    def _handle_error(exc: Exception):
        if isinstance(exc, ServiceUnavailableError):
            return Response(PAOViewMixin.SERVICE_UNAVAILABLE_MSG, status=503)
        if isinstance(exc, NotSupportedError):
            return HttpResponseForbidden(PAOViewMixin.FUNCTION_NOT_SUPPORTED_MSG)
        if isinstance(exc, NotFoundError):
            return HttpResponseNotFound(PAOViewMixin.RESOURCE_NOT_FOUND_MSG)
        if isinstance(exc, ValidationError) or isinstance(exc, ValueError):
            return HttpResponseBadRequest()
        # Let DRF/Django handle unexpected errors (500)
        raise


# -----------------------------
# Abstract views (generic API)
# -----------------------------
class Health(PAOViewMixin, RetrieveAPIView):
    """
    [GET] /<PAO>/health
    Returns overall health status for the PAO implementation.
    """
    def get(self, request, **kwargs):
        try:
            return Response(self.svc().health_status())
        except Exception as exc:
            return self._handle_error(exc)


class Capacity(PAOViewMixin, RetrieveAPIView):
    """
    [GET] /<PAO>/capacity
    Returns capacity figures for the PAO implementation.
    """
    def get(self, request, **kwargs):
        try:
            return Response(self.svc().capacity())
        except Exception as exc:
            return self._handle_error(exc)


class Rules(PAOViewMixin, APIView):
    """
    [GET] /<PAO>/rules?subject=...
    [POST] /<PAO>/rules
    """
    def get(self, request, **kwargs):
        try:
            subject: Optional[str] = request.query_params.get("subject")
            return Response(self.svc().list_rules(subject=subject))
        except Exception as exc:
            return self._handle_error(exc)

    def post(self, request, **kwargs):
        try:
            payload: Dict[str, Any] = request.data if isinstance(request.data, dict) else {}
            return Response(self.svc().create_rule(payload))
        except Exception as exc:
            return self._handle_error(exc)


class RuleDetail(PAOViewMixin, APIView):
    """
    [GET]    /<PAO>/rules/{ruleId}
    [PUT]    /<PAO>/rules/{ruleId}
    [DELETE] /<PAO>/rules/{ruleId}
    """
    def get(self, request, ruleId: str, **kwargs):
        try:
            rid = int(ruleId)
            return Response(self.svc().get_rule(rid))
        except ValueError as exc:
            return self._handle_error(exc)
        except Exception as exc:
            return self._handle_error(exc)

    def put(self, request, ruleId: str, **kwargs):
        try:
            rid = int(ruleId)
            payload: Dict[str, Any] = request.data if isinstance(request.data, dict) else {}
            return Response(self.svc().update_rule(rid, payload))
        except ValueError as exc:
            return self._handle_error(exc)
        except Exception as exc:
            return self._handle_error(exc)

    def delete(self, request, ruleId: str, **kwargs):
        try:
            rid = int(ruleId)
            return Response(self.svc().delete_rule(rid))
        except ValueError as exc:
            return self._handle_error(exc)
        except Exception as exc:
            return self._handle_error(exc)


class RulesBySubject(PAOViewMixin, APIView):
    """
    [GET]    /<PAO>/rules/subject/{subject}
    [PUT]    /<PAO>/rules/subject/{subject}
    [DELETE] /<PAO>/rules/subject/{subject}
    """
    def get(self, request, subject: str, **kwargs):
        try:
            return Response(self.svc().list_by_subject(subject))
        except Exception as exc:
            return self._handle_error(exc)

    def put(self, request, subject: str, **kwargs):
        try:
            payload: Dict[str, Any] = request.data if isinstance(request.data, dict) else {}
            return Response(self.svc().bulk_update_by_subject(subject, payload))
        except Exception as exc:
            return self._handle_error(exc)

    def delete(self, request, subject: str, **kwargs):
        try:
            return Response(self.svc().bulk_delete_by_subject(subject))
        except Exception as exc:
            return self._handle_error(exc)
