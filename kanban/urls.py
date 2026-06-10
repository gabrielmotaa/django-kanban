from django.urls import path

from .views import components, templates

urlpatterns = [
    path("templates/", templates.index, name="templates_index"),
    path("templates/card-move/", templates.card_move, name="templates_card_move"),
    path(
        "templates/card/<int:pk>/edit/", templates.card_edit, name="templates_card_edit"
    ),
    path(
        "templates/card/<int:pk>/delete/",
        templates.card_delete,
        name="templates_card_delete",
    ),
    path("templates/column-move/", templates.column_move, name="templates_column_move"),
    path(
        "templates/column/<int:pk>/delete/",
        templates.column_delete,
        name="templates_column_delete",
    ),
    path(
        "templates/column/<int:pk>/edit/",
        templates.column_edit,
        name="templates_column_edit",
    ),
    path(
        "templates/column/<int:column_id>/card-create/",
        templates.card_create,
        name="templates_card_create",
    ),
    path(
        "templates/board/<int:board_id>/column-create/",
        templates.column_create,
        name="templates_column_create",
    ),
    path(
        "templates/board/<int:pk>/edit/",
        templates.board_edit,
        name="templates_board_edit",
    ),
    path("components/", components.index, name="components_index"),
]
