from django.http import HttpResponse
from django.test import RequestFactory

from kanban.middleware import WebComponentsMiddleware


def test_middleware_with_web_components_header():
    factory = RequestFactory()
    request = factory.get("/", headers={"X-Web-Components": "true"})

    def dummy_get_response(req):
        return HttpResponse("OK")

    middleware = WebComponentsMiddleware(dummy_get_response)
    response = middleware(request)

    assert response.status_code == 200
    assert getattr(request, "web_components", None) is True


def test_middleware_without_web_components_header():
    factory = RequestFactory()
    request = factory.get("/")

    def dummy_get_response(req):
        return HttpResponse("OK")

    middleware = WebComponentsMiddleware(dummy_get_response)
    response = middleware(request)

    assert response.status_code == 200
    assert getattr(request, "web_components", None) is False


def test_middleware_with_invalid_web_components_header():
    factory = RequestFactory()
    request = factory.get("/", headers={"X-Web-Components": "false"})

    def dummy_get_response(req):
        return HttpResponse("OK")

    middleware = WebComponentsMiddleware(dummy_get_response)
    response = middleware(request)

    assert response.status_code == 200
    assert getattr(request, "web_components", None) is False
