import json
from http import HTTPStatus

from django.db import transaction
from django.db.models import Max
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    QueryDict,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import View

from kanban.activity import record_activity
from kanban.forms import (
    BoardEditForm,
    CardCreateForm,
    CardDescriptionForm,
    CardDueDateForm,
    CardEditForm,
    CardLabelForm,
    ChecklistCreateForm,
    ChecklistItemCreateForm,
    ChecklistItemEditForm,
    ChecklistRenameForm,
    ColumnCreateForm,
    ColumnEditForm,
    CommentForm,
    LabelContextForm,
    LabelCreateForm,
    LabelEditForm,
)
from kanban.models import (
    Board,
    Card,
    Checklist,
    ChecklistItem,
    Column,
    Comment,
    Label,
)
from kanban.utils import (
    ApiError,
    error_response,
    fetch_or_error,
    form_error_message,
    template_for_request,
)


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "kanban/home.html")


def label_registry(board: Board) -> list[dict]:
    """The board's labels as the components' registry (served as JSON)."""
    return [
        {
            "id": label.pk,
            "name": label.name,
            "color": label.color,
            "fg": label.fg_color,
            "colorName": label.color_name,
            "href": reverse("label_detail", args=[label.pk]),
        }
        for label in board.labels.all()
    ]


def index(request: HttpRequest, tech: str) -> HttpResponse:
    board = get_object_or_404(
        Board.objects.prefetch_related(
            "columns__cards__labels",
            "columns__cards__checklists__items",
            "columns__cards__comments",
        ),
        pk=1,
    )
    match tech:
        case "templates":
            template_name = "kanban/templates/index.html"
        case "components":
            template_name = "kanban/components/index.html"
        case _:
            raise Http404("Invalid tech")
    return render(
        request,
        template_name,
        {
            "board": board,
            "color_choices": Column.COLOR_CHOICES,
            "color_choices_json": json.dumps(Column.COLOR_CHOICES, ensure_ascii=False),
            "labels_json": json.dumps(label_registry(board), ensure_ascii=False),
        },
    )


class ApiView(View):
    """Turns `ApiError` into a toast response for HTMX requests."""

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except ApiError as error:
            return error_response(request, error.message, error.status)


class CardCreateView(ApiView):
    def post(self, request: HttpRequest) -> HttpResponse:
        form = CardCreateForm(request.POST)
        if not form.is_valid():
            raise ApiError(form_error_message(form))

        column = fetch_or_error(
            Column, "Coluna não encontrada.", pk=form.cleaned_data["column_id"]
        )
        order = column.cards.count()
        card = Card.objects.create(
            column=column, title=form.cleaned_data["title"], order=order
        )
        record_activity(card, "card_created", column=column.title)
        template_path = template_for_request(request, "_card.html")
        return render(request, template_path, {"card": card})


class CardDetailView(ApiView):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        card = fetch_card(pk)
        template_path = template_for_request(request, "_card.html")
        return render(request, template_path, {"card": card})

    def patch(self, request: HttpRequest, pk: int) -> HttpResponse:
        card = fetch_card(pk)
        data = QueryDict(request.body)
        form = CardEditForm(data)
        if not form.is_valid():
            raise ApiError(form_error_message(form))

        if form.cleaned_data["title"]:
            old_title = card.title
            card.title = form.cleaned_data["title"]
            card.save(update_fields=["title"])
            activity = None
            if card.title != old_title:
                activity = record_activity(
                    card, "title_renamed", old=old_title, new=card.title
                )
            template_path = template_for_request(request, "_card_title_updated.html")
            return render(request, template_path, {"card": card, "activity": activity})

        target_column = fetch_or_error(
            Column, "Coluna não encontrada.", pk=form.cleaned_data["column_id"]
        )
        order = form.cleaned_data["order"]

        with transaction.atomic():
            if card.column == target_column:
                # Same column.
                cards = list(target_column.cards.exclude(pk=card.pk))
                order = min(order, len(cards))
                cards.insert(order, card)
                for index, c in enumerate(cards):
                    if c.order != index:
                        c.order = index
                        c.save(update_fields=["order"])
            else:
                # Different column.
                # Remove from origin and reorder.
                cards = list(card.column.cards.exclude(pk=card.pk))
                for index, c in enumerate(cards):
                    if c.order != index:
                        c.order = index
                        c.save(update_fields=["order"])

                # Add into target and reorder.
                cards = list(target_column.cards.all())
                order = min(order, len(cards))
                cards.insert(order, card)
                for index, c in enumerate(cards):
                    if c.order != index:
                        c.order = index
                        c.save(update_fields=["order"])

                origin = card.column
                card.column = target_column
                card.order = order
                card.save(update_fields=["column", "order"])
                record_activity(
                    card,
                    "card_moved",
                    **{"from": origin.title, "to": target_column.title},
                )

        return HttpResponse(status=HTTPStatus.NO_CONTENT)

    def delete(self, request: HttpRequest, pk: int) -> HttpResponse:
        card = fetch_card(pk)
        card.delete()
        return HttpResponse(status=HTTPStatus.NO_CONTENT)


def next_order(queryset) -> int:
    """Position after the last row, also after earlier rows were deleted."""
    return (queryset.aggregate(last=Max("order"))["last"] or -1) + 1


def fetch_card(pk: int) -> Card:
    """A card with what the dialog needs (column, board, labels)."""
    return fetch_or_error(
        Card.objects.select_related("column__board").prefetch_related(
            "labels", "checklists__items", "comments", "activities"
        ),
        "Card não encontrado.",
        pk=pk,
    )


def card_context(card: Card) -> dict:
    return {
        "card": card,
        "board_labels": card.column.board.labels.all(),
        "attached_ids": {label.pk for label in card.labels.all()},
        "color_choices": Column.COLOR_CHOICES,
        "timeline": card.timeline(),
    }


class CardDialogView(ApiView):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        card = fetch_card(pk)
        template_path = template_for_request(request, "_card_dialog.html")
        return render(request, template_path, card_context(card))


class CardDescriptionView(ApiView):
    def patch(self, request: HttpRequest, pk: int) -> HttpResponse:
        card = fetch_card(pk)
        form = CardDescriptionForm(QueryDict(request.body))
        if not form.is_valid():
            raise ApiError(form_error_message(form))

        changed = card.description != form.cleaned_data["description"]
        card.description = form.cleaned_data["description"]
        card.save(update_fields=["description", "updated_at"])
        activity = record_activity(card, "description_changed") if changed else None
        template_path = template_for_request(request, "_card_description_updated.html")
        return render(request, template_path, {"card": card, "activity": activity})


class CardDueView(ApiView):
    def patch(self, request: HttpRequest, pk: int) -> HttpResponse:
        card = fetch_card(pk)
        form = CardDueDateForm(QueryDict(request.body))
        if not form.is_valid():
            raise ApiError(form_error_message(form))

        before_date, before_completed = card.due_date, card.completed
        card.due_date = form.cleaned_data["due_date"]
        # A card without a date cannot be completed.
        card.completed = form.cleaned_data["completed"] and card.due_date is not None
        card.save(update_fields=["due_date", "completed", "updated_at"])

        activities = []
        if card.due_date != before_date:
            if card.due_date:
                activities.append(
                    record_activity(card, "due_set", date=card.due_date.isoformat())
                )
            else:
                activities.append(record_activity(card, "due_removed"))
        if card.completed and not before_completed:
            activities.append(record_activity(card, "due_completed"))
        template_path = template_for_request(request, "_card_due_updated.html")
        # Newest first, like the timeline (one request may record two entries).
        context = {"card": card, "activities": activities[::-1]}
        return render(request, template_path, context)


def checklist_response(
    request, template, card_pk, checklist_pk=None, item_pk=None, activity=None
):
    """Render a checklist reply from a freshly fetched card (counts included)."""
    card = fetch_card(card_pk)
    checklist = next((c for c in card.checklists.all() if c.pk == checklist_pk), None)
    item = None
    if checklist is not None:
        item = next((i for i in checklist.items.all() if i.pk == item_pk), None)
    context = {
        "card": card,
        "checklist": checklist,
        "item": item,
        "activity": activity,
    }
    return render(request, template_for_request(request, template), context)


class CardChecklistsView(ApiView):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        card = fetch_card(pk)
        form = ChecklistCreateForm(request.POST)
        if not form.is_valid():
            raise ApiError(form_error_message(form))
        checklist = Checklist.objects.create(
            card=card,
            title=form.cleaned_data["title"] or "Checklist",
            order=next_order(card.checklists.all()),
        )
        return checklist_response(request, "_checklist_created.html", pk, checklist.pk)


class ChecklistDetailView(ApiView):
    def patch(self, request: HttpRequest, pk: int) -> HttpResponse:
        checklist = fetch_or_error(Checklist, "Checklist não encontrado.", pk=pk)
        form = ChecklistRenameForm(QueryDict(request.body))
        if not form.is_valid():
            raise ApiError(form_error_message(form))
        checklist.title = form.cleaned_data["title"]
        checklist.save(update_fields=["title"])
        return checklist_response(
            request, "_checklist_updated.html", checklist.card_id, checklist.pk
        )

    def delete(self, request: HttpRequest, pk: int) -> HttpResponse:
        checklist = fetch_or_error(Checklist, "Checklist não encontrado.", pk=pk)
        card_id = checklist.card_id
        checklist.delete()
        return checklist_response(request, "_checklist_deleted.html", card_id)


class ChecklistItemsView(ApiView):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        checklist = fetch_or_error(Checklist, "Checklist não encontrado.", pk=pk)
        form = ChecklistItemCreateForm(request.POST)
        if not form.is_valid():
            raise ApiError(form_error_message(form))
        item = ChecklistItem.objects.create(
            checklist=checklist,
            text=form.cleaned_data["text"],
            order=next_order(checklist.items.all()),
        )
        return checklist_response(
            request, "_checklist_item_created.html", checklist.card_id, pk, item.pk
        )


class ChecklistItemDetailView(ApiView):
    def patch(self, request: HttpRequest, pk: int) -> HttpResponse:
        item = fetch_or_error(
            ChecklistItem.objects.select_related("checklist"),
            "Item não encontrado.",
            pk=pk,
        )
        form = ChecklistItemEditForm(QueryDict(request.body))
        if not form.is_valid():
            raise ApiError(form_error_message(form))
        was_done = item.done
        if form.cleaned_data["text"]:
            item.text = form.cleaned_data["text"]
        if form.cleaned_data["done"] is not None:
            item.done = form.cleaned_data["done"]
        item.save(update_fields=["text", "done"])
        activity = None
        if item.done and not was_done:
            activity = record_activity(
                item.checklist.card,
                "checklist_item_completed",
                text=item.text,
                checklist=item.checklist.title,
            )
        return checklist_response(
            request,
            "_checklist_item_updated.html",
            item.checklist.card_id,
            item.checklist_id,
            item.pk,
            activity,
        )

    def delete(self, request: HttpRequest, pk: int) -> HttpResponse:
        item = fetch_or_error(
            ChecklistItem.objects.select_related("checklist"),
            "Item não encontrado.",
            pk=pk,
        )
        card_id, checklist_id = item.checklist.card_id, item.checklist_id
        item.delete()
        return checklist_response(
            request, "_checklist_item_deleted.html", card_id, checklist_id
        )


class CardCommentsView(ApiView):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        card = fetch_card(pk)
        form = CommentForm(request.POST)
        if not form.is_valid():
            raise ApiError(form_error_message(form))
        comment = Comment.objects.create(card=card, text=form.cleaned_data["text"])
        return comment_response(request, "_comment_created.html", pk, comment.pk)


class CommentDetailView(ApiView):
    def patch(self, request: HttpRequest, pk: int) -> HttpResponse:
        comment = fetch_or_error(Comment, "Comentário não encontrado.", pk=pk)
        form = CommentForm(QueryDict(request.body))
        if not form.is_valid():
            raise ApiError(form_error_message(form))
        comment.text = form.cleaned_data["text"]
        comment.save(update_fields=["text", "updated_at"])
        return comment_response(
            request, "_comment_updated.html", comment.card_id, comment.pk
        )

    def delete(self, request: HttpRequest, pk: int) -> HttpResponse:
        comment = fetch_or_error(Comment, "Comentário não encontrado.", pk=pk)
        card_id = comment.card_id
        comment.delete()
        return comment_response(request, "_comment_deleted.html", card_id)


def comment_response(request, template, card_pk, comment_pk=None) -> HttpResponse:
    card = fetch_card(card_pk)
    comment = next((c for c in card.comments.all() if c.pk == comment_pk), None)
    context = {"card": card, "comment": comment, "activity": None}
    return render(request, template_for_request(request, template), context)


class CardLabelsView(ApiView):
    """Attach (POST) or detach (DELETE ?label_id=) a label of the card's board."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        return self._toggle(request, pk, request.POST, attach=True)

    def delete(self, request: HttpRequest, pk: int) -> HttpResponse:
        return self._toggle(request, pk, request.GET, attach=False)

    def _toggle(self, request, pk: int, data, *, attach: bool) -> HttpResponse:
        card = fetch_card(pk)
        form = CardLabelForm(data)
        if not form.is_valid():
            raise ApiError(form_error_message(form))
        label = fetch_or_error(
            Label, "Etiqueta não encontrada.", pk=form.cleaned_data["label_id"]
        )
        if label.board_id != card.column.board_id:
            raise ApiError("Etiqueta de outro quadro.")

        attached = card.labels.filter(pk=label.pk).exists()
        activity = None
        if attach and not attached:
            card.labels.add(label)
            activity = record_activity(card, "label_added", name=str(label))
        elif not attach and attached:
            card.labels.remove(label)
            activity = record_activity(card, "label_removed", name=str(label))

        card = fetch_card(pk)
        template_path = template_for_request(request, "_card_labels_updated.html")
        context = card_context(card)
        context["activity"] = activity
        return render(request, template_path, context)


def labels_response(request, card: Card, affected: list[Card]) -> HttpResponse:
    """Reply to a label create/edit/delete sent from `card`'s dialog.

    Templates: the popover plus every affected card front, out-of-band.
    Components: the updated label registry (cards react to it).
    """
    context = card_context(card)
    context["affected_cards"] = affected
    context["board"] = card.column.board
    context["labels_json"] = json.dumps(
        label_registry(card.column.board), ensure_ascii=False
    )
    template_path = template_for_request(request, "_label_changes.html")
    return render(request, template_path, context)


def refetch(cards: list[int]) -> list[Card]:
    return list(
        Card.objects.filter(pk__in=cards)
        .select_related("column__board")
        .prefetch_related("labels", "checklists__items", "comments", "activities")
    )


class LabelCreateView(ApiView):
    def post(self, request: HttpRequest) -> HttpResponse:
        form = LabelCreateForm(request.POST)
        if not form.is_valid():
            raise ApiError(form_error_message(form))
        board = fetch_or_error(
            Board, "Quadro não encontrado.", pk=form.cleaned_data["board_id"]
        )
        card = fetch_card(form.cleaned_data["card_id"])
        if card.column.board_id != board.pk:
            raise ApiError("Card de outro quadro.")

        Label.objects.create(
            board=board,
            name=form.cleaned_data["name"],
            color=form.cleaned_data["color"],
        )
        return labels_response(request, fetch_card(card.pk), [])


class LabelDetailView(ApiView):
    def patch(self, request: HttpRequest, pk: int) -> HttpResponse:
        label = fetch_or_error(Label, "Etiqueta não encontrada.", pk=pk)
        form = LabelEditForm(QueryDict(request.body))
        if not form.is_valid():
            raise ApiError(form_error_message(form))
        card = self._context_card(form.cleaned_data["card_id"], label)

        affected_ids = list(label.cards.values_list("pk", flat=True))
        label.name = form.cleaned_data["name"]
        label.color = form.cleaned_data["color"]
        label.save(update_fields=["name", "color"])
        return labels_response(request, fetch_card(card.pk), refetch(affected_ids))

    def delete(self, request: HttpRequest, pk: int) -> HttpResponse:
        label = fetch_or_error(Label, "Etiqueta não encontrada.", pk=pk)
        form = LabelContextForm(request.GET)
        if not form.is_valid():
            raise ApiError(form_error_message(form))
        card = self._context_card(form.cleaned_data["card_id"], label)

        affected_ids = list(label.cards.values_list("pk", flat=True))
        label.delete()
        return labels_response(request, fetch_card(card.pk), refetch(affected_ids))

    @staticmethod
    def _context_card(card_id: int, label: Label) -> Card:
        card = fetch_card(card_id)
        if card.column.board_id != label.board_id:
            raise ApiError("Etiqueta de outro quadro.")
        return card


class ColumnCreateView(ApiView):
    def post(self, request: HttpRequest) -> HttpResponse:
        form = ColumnCreateForm(request.POST)
        if not form.is_valid():
            raise ApiError(form_error_message(form))

        board = fetch_or_error(
            Board, "Quadro não encontrado.", pk=form.cleaned_data["board_id"]
        )
        order = board.columns.count()
        color = form.cleaned_data.get("color")
        create_kwargs = {
            "board": board,
            "title": form.cleaned_data["title"],
            "order": order,
        }
        if color:
            create_kwargs["color"] = color
        column = Column.objects.create(**create_kwargs)
        template_path = template_for_request(request, "_column.html")
        return render(request, template_path, {"column": column})


class ColumnDetailView(ApiView):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        column = fetch_or_error(Column, "Coluna não encontrada.", pk=pk)
        template_path = template_for_request(request, "_column.html")
        return render(request, template_path, {"column": column})

    def patch(self, request: HttpRequest, pk: int) -> HttpResponse:
        column = fetch_or_error(Column, "Coluna não encontrada.", pk=pk)
        data = QueryDict(request.body)
        form = ColumnEditForm(data)
        if not form.is_valid():
            raise ApiError(form_error_message(form))

        order = form.cleaned_data.get("order")
        if order is not None:
            board = column.board
            with transaction.atomic():
                columns = list(board.columns.exclude(pk=column.pk))
                order = min(order, len(columns))
                columns.insert(order, column)
                for i, col in enumerate(columns):
                    if col.order != i:
                        col.order = i
                        col.save(update_fields=["order"])

            return HttpResponse(status=HTTPStatus.NO_CONTENT)
        else:
            title = form.cleaned_data.get("title")
            color = form.cleaned_data.get("color")

            update_fields = []
            if title:
                column.title = title
                update_fields.append("title")
            if color:
                column.color = color
                update_fields.append("color")

            column.save(update_fields=update_fields)

        template_path = template_for_request(request, "_column.html")
        return render(request, template_path, {"column": column})

    def delete(self, request: HttpRequest, pk: int) -> HttpResponse:
        column = fetch_or_error(Column, "Coluna não encontrada.", pk=pk)
        column.delete()
        return HttpResponse(status=HTTPStatus.NO_CONTENT)


class BoardDetailView(ApiView):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        board = fetch_or_error(Board, "Quadro não encontrado.", pk=pk)
        template_path = template_for_request(request, "_board_title.html")
        return render(request, template_path, {"board": board})

    def patch(self, request: HttpRequest, pk: int) -> HttpResponse:
        board = fetch_or_error(Board, "Quadro não encontrado.", pk=pk)
        data = QueryDict(request.body)
        form = BoardEditForm(data)
        if not form.is_valid():
            raise ApiError(form_error_message(form))

        board.title = form.cleaned_data["title"]
        board.save(update_fields=["title"])

        template_path = template_for_request(request, "_board_title.html")
        return render(request, template_path, {"board": board})
