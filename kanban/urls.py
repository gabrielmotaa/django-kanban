from django.urls import path

from .views import templates, components

urlpatterns = [
    path("templates/", templates.index, name="templates_index"),
    path("components/", components.index, name="components_index"),
]
