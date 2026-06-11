from collections.abc import Callable

from django.http import HttpRequest, HttpResponse


class WebComponentsMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.web_components = request.headers.get("x-web-components") == "true"
        return self.get_response(request)
