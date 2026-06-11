from django.urls import path

from . import views

urlpatterns = [
    path("templates/", views.templates_index, name="templates_index"),
    path("components/", views.components_index, name="components_index"),
    path("card-move/", views.card_move, name="card_move"),
    path("card/<int:pk>/edit/", views.card_edit, name="card_edit"),
    path(
        "card/<int:pk>/delete/",
        views.card_delete,
        name="card_delete",
    ),
    path("column-move/", views.column_move, name="column_move"),
    path(
        "column/<int:pk>/delete/",
        views.column_delete,
        name="column_delete",
    ),
    path(
        "column/<int:pk>/edit/",
        views.column_edit,
        name="column_edit",
    ),
    path(
        "column/<int:column_id>/card-create/",
        views.card_create,
        name="card_create",
    ),
    path(
        "board/<int:board_id>/column-create/",
        views.column_create,
        name="column_create",
    ),
    path(
        "board/<int:pk>/edit/",
        views.board_edit,
        name="board_edit",
    ),
]
