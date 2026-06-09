from django.urls import path

from .views import components, templates

urlpatterns = [
    path("templates/", templates.index, name="templates_index"),
    path("components/", components.index, name="components_index"),
]
