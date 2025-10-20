# views.py — pao_generic_project (abstract & generic)

from __future__ import annotations
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable, Tuple, Type
import importlib

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView


# ---------------------------------------------------------------------------
# Domain-agnostic exceptions (service layer -> HTTP mapping)
# ---------------------------------------------------------------------------
class ServiceUnavailableError(Exception):
    """The PAO backend is down or unreachable (-> 503)."""


class NotSupportedError(Exception):
    """The PAO backend does not support this function (-> 403)."""


class NotFoundError(Exception):
    """Requested resource was not found (-> 404)."""


class ValidationError(Exception):
    """Invalid input/payload (-> 400)."""


# ---------------------------------------------------------------------------
# Abstract Service Interface (no domain fields here)
# ---------------------------------------------------------------------------
@runtime_checkable
class BasePAOService(Protocol):
    """Abstract PAO service contract. Implement this in your wrapper."""

    # Health / Capacity --------------------------------------------------------
    def health_status(self) -> Dict[str, Any]:
        """
        Return a health payload, e.g.: {"serviceStatus": "alive"}.
        Raise ServiceUnavailableError if backend is not healthy.
        """
        ...

    def capacity(self) -> Dict[str, int]:
        """
        Return capacity, e.g.: {"maxCapacity": 0, "usedCapacity": 0, "freeCapacity": 0}.
        Raise NotSupportedError if not applicable.
        """
        ...

    # Rules (generic) ----------------------------------------------------------
    def list_rules(self, subject: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Return a list of rule dicts. If subject is provided, filter by subject.
        """
        ...

    def create_rule(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a rule from the generic payload. Must return at least {"ruleId": <int>}.
        Raise ValidationError on bad input.
        """
        ...

    def get_rule(self, rule_id: int) -> Dict[str, Any]:
        """Return a single rule by id. Raise NotFoundError if missing."""
        ...

    def update_rule(self, rule_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update mutable fields of a rule. Return the updated rule.
        Raise NotFoundError or ValidationError as appropriate.
        """
        ...

    def delete_rule(self, rule_id: int) -> Dict[str, Any]:
        """
        Delete a rule. Return a minimal descriptor (e.g., {"ruleId": id}) or the deleted rule.
        Raise NotFoundError if missing.
        """
        ...

    # Bulk by subject ----------------------------------------------------------
    def list_by_subject(self, subject: str) -> List[Dict[str, Any]]:
        """Return all rules for a given subject."""
        ...

    def bulk_update_by_subject(self, subject: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Update rules for subject. Return updated rules list."""
        ...

    def bulk_delete_by_subject(self, subject: str) -> Dict[str, Any]:
        """Delete rules for subject. Return an ack payload."""
        ...


# ---------------------------------------------------------------------------
# Service resolver (dependency injection via settings.PAO_SERVICE_CLASS)
# ---------------------------------------------------------------------------
def _import_object(dotted_path: str) -> Any:
    """
    Import "pkg.module:ClassName" or "pkg.module.ClassName".
    """
    if ":" in dotted_path:
        module_path, obj_name = dotted_path.split(":", 1)
    else:
        module_path, obj_name = dotted_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, obj_name)


def get_pao_service() -> BasePAOService:
    dotted = getattr(settings, "PAO_SERVICE_CLASS", None)
    if not dotted:
        raise ImproperlyConfigured(
            "PAO_SERVICE_CLASS is not configured. "
            "Set it to the dotted path of a BasePAOService implementation."
        )
    svc_cls: Type[BasePAOService] = _import_object(dotted)
    svc = svc_cls()  # If you need DI/args, adapt this to a factory pattern
    if not isinstance(svc, BasePAOService):
        raise ImproperlyConfigured(f"{dotted} does not implement BasePAOService.")
    return svc


# ---------------------------------------------------------------------------
# Base View mixin: resolve service & map exceptions -> HTTP responses
# ---------------------------------------------------------------------------
class PAOViewMixin:
    SERVICE_UNAVAILABLE_MSG = "Service unavailable!"
    FUNCTION_NOT_SUPPORTED_MSG = "Function not supported!"
    RESOURCE_NOT_FOUND_MSG = "Resource not found!"

    def svc(self) -> BasePAOService:
        return get_pao_service()

    @staticmethod
    def _handle_error(exc: Exception) -> Response:
        if isinstance(exc, ServiceUnavailableError):
            return Response(PAOViewMixin.SERVICE_UNAVAILABLE_MSG, status=503)
        if isinstance(exc, NotSupportedError):
            return HttpResponseForbidden(PAOViewMixin.FUNCTION_NOT_SUPPORTED_MSG)
        if isinstance(exc, NotFoundError):
            return HttpResponseNotFound(PAOViewMixin.RESOURCE_NOT_FOUND_MSG)
        if isinstance(exc, ValidationError):
            return HttpResponseBadRequest()
        # Unexpected error -> let DRF handle (500) or transform if desired
        raise


# ---------------------------------------------------------------------------
# Views (generic, no domain specifics)
# ---------------------------------------------------------------------------
class Health(PAOViewMixin, RetrieveAPIView):
    """
    [GET] /<PAO>/health
    """
    def get(self, request, **kwargs):
        try:
            return Response(self.svc().health_status())
        except Exception as exc:
            return self._handle_error(exc)


class Capacity(PAOViewMixin, RetrieveAPIView):
    """
    [GET] /<PAO>/capacity
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
            subject = request.query_params.get("subject")
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
    [GET] /<PAO>/rules/{ruleId}
    [PUT] /<PAO>/rules/{ruleId}
    [DELETE] /<PAO>/rules/{ruleId}
    """
    def get(self, request, ruleId: str, **kwargs):
        try:
            rid = int(ruleId)
            return Response(self.svc().get_rule(rid))
        except ValueError:
            return HttpResponseBadRequest()
        except Exception as exc:
            return self._handle_error(exc)

    def put(self, request, ruleId: str, **kwargs):
        try:
            rid = int(ruleId)
            payload: Dict[str, Any] = request.data if isinstance(request.data, dict) else {}
            return Response(self.svc().update_rule(rid, payload))
        except ValueError:
            return HttpResponseBadRequest()
        except Exception as exc:
            return self._handle_error(exc)

    def delete(self, request, ruleId: str, **kwargs):
        try:
            rid = int(ruleId)
            return Response(self.svc().delete_rule(rid))
        except ValueError:
            return HttpResponseBadRequest()
        except Exception as exc:
            return self._handle_error(exc)


class RulesBySubject(PAOViewMixin, APIView):
    """
    [GET] /<PAO>/rules/subject/{subject}
    [PUT] /<PAO>/rules/subject/{subject}
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
