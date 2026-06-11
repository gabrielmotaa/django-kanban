from django.http import HttpRequest


def template_for_request(request: HttpRequest, base_path: str) -> str:
    if getattr(request, "web_components", False):
        return f"kanban/components/{base_path}"
    return f"kanban/templates/{base_path}"
