from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("card/", views.CardCreateView.as_view(), name="card_create"),
    path("card/<int:pk>/", views.CardDetailView.as_view(), name="card_detail"),
    path("card/<int:pk>/dialog/", views.CardDialogView.as_view(), name="card_dialog"),
    path(
        "card/<int:pk>/description/",
        views.CardDescriptionView.as_view(),
        name="card_description",
    ),
    path("card/<int:pk>/due/", views.CardDueView.as_view(), name="card_due"),
    path(
        "card/<int:pk>/checklists/",
        views.CardChecklistsView.as_view(),
        name="card_checklists",
    ),
    path(
        "checklist/<int:pk>/",
        views.ChecklistDetailView.as_view(),
        name="checklist_detail",
    ),
    path(
        "checklist/<int:pk>/items/",
        views.ChecklistItemsView.as_view(),
        name="checklist_items",
    ),
    path(
        "checklist-item/<int:pk>/",
        views.ChecklistItemDetailView.as_view(),
        name="checklist_item_detail",
    ),
    path("card/<int:pk>/labels/", views.CardLabelsView.as_view(), name="card_labels"),
    path("label/", views.LabelCreateView.as_view(), name="label_create"),
    path("label/<int:pk>/", views.LabelDetailView.as_view(), name="label_detail"),
    path("column/", views.ColumnCreateView.as_view(), name="column_create"),
    path("column/<int:pk>/", views.ColumnDetailView.as_view(), name="column_detail"),
    path("board/<int:pk>/", views.BoardDetailView.as_view(), name="board_detail"),
    # Keep it last, it will catch all the other cases.
    path("<str:tech>/", views.index, name="index"),
]
