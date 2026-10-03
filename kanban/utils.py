from http import HTTPStatus

from django.db.models import Model
from django.forms import Form
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def template_for_request(request: HttpRequest, base_path: str) -> str:
    if getattr(request, "web_components", False):
        return f"kanban/components/{base_path}"
    return f"kanban/templates/{base_path}"


class ApiError(Exception):
    """A request failed in a way the user should be told about (toast)."""

    def __init__(self, message: str, status: int = HTTPStatus.BAD_REQUEST):
        super().__init__(message)
        self.message = message
        self.status = status


def error_response(
    request: HttpRequest, message: str, status: int = HTTPStatus.BAD_REQUEST
) -> HttpResponse:
    """Toast fragment that htmx inserts into the page's toast area.

    HTMX does not swap 4xx responses on its own; ``HX-Retarget`` and
    ``HX-Reswap`` tell it where the toast goes and the page configures it to
    swap these responses.
    """
    response = render(
        request,
        template_for_request(request, "_toast.html"),
        {"message": message},
        status=status,
    )
    response["HX-Retarget"] = "#toast-area"
    response["HX-Reswap"] = "beforeend"
    return response


def fetch_or_error[M: Model](model: type[M], message: str, **lookup) -> M:
    try:
        return model.objects.get(**lookup)
    except model.DoesNotExist:
        raise ApiError(message, HTTPStatus.NOT_FOUND) from None


def form_error_message(form: Form) -> str:
    """First (non-field first) validation message of an invalid form."""
    non_field = form.non_field_errors()
    if non_field:
        return non_field[0]
    for errors in form.errors.values():
        return errors[0]
    return "Requisição inválida."


__all__ = [
    "ApiError",
    "error_response",
    "fetch_or_error",
    "form_error_message",
    "template_for_request",
]
