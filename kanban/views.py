import json
from http import HTTPStatus

from django.db import transaction
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    QueryDict,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import View

from kanban.forms import (
    BoardEditForm,
    CardCreateForm,
    CardDescriptionForm,
    CardEditForm,
    CardLabelForm,
    ColumnCreateForm,
    ColumnEditForm,
    LabelContextForm,
    LabelCreateForm,
    LabelEditForm,
)
from kanban.models import Board, Card, Column, Label
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
        Board.objects.prefetch_related("columns__cards__labels"), pk=1
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
        template_path = template_for_request(request, "_card.html")
        return render(request, template_path, {"card": card})


class CardDetailView(ApiView):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        card = fetch_or_error(Card, "Card não encontrado.", pk=pk)
        template_path = template_for_request(request, "_card.html")
        return render(request, template_path, {"card": card})

    def patch(self, request: HttpRequest, pk: int) -> HttpResponse:
        card = fetch_or_error(Card, "Card não encontrado.", pk=pk)
        data = QueryDict(request.body)
        form = CardEditForm(data)
        if not form.is_valid():
            raise ApiError(form_error_message(form))

        if form.cleaned_data["title"]:
            card.title = form.cleaned_data["title"]
            card.save(update_fields=["title"])
            template_path = template_for_request(request, "_card_title_updated.html")
            return render(request, template_path, {"card": card})

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

                card.column = target_column
                card.order = order
                card.save(update_fields=["column", "order"])

        return HttpResponse(status=HTTPStatus.NO_CONTENT)

    def delete(self, request: HttpRequest, pk: int) -> HttpResponse:
        card = fetch_or_error(Card, "Card não encontrado.", pk=pk)
        card.delete()
        return HttpResponse(status=HTTPStatus.NO_CONTENT)


def fetch_card(pk: int) -> Card:
    """A card with what the dialog needs (column, board, labels)."""
    return fetch_or_error(
        Card.objects.select_related("column__board").prefetch_related("labels"),
        "Card não encontrado.",
        pk=pk,
    )


def card_context(card: Card) -> dict:
    return {
        "card": card,
        "board_labels": card.column.board.labels.all(),
        "attached_ids": {label.pk for label in card.labels.all()},
        "color_choices": Column.COLOR_CHOICES,
    }


class CardDialogView(ApiView):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        card = fetch_card(pk)
        template_path = template_for_request(request, "_card_dialog.html")
        return render(request, template_path, card_context(card))


class CardDescriptionView(ApiView):
    def patch(self, request: HttpRequest, pk: int) -> HttpResponse:
        card = fetch_or_error(Card, "Card não encontrado.", pk=pk)
        form = CardDescriptionForm(QueryDict(request.body))
        if not form.is_valid():
            raise ApiError(form_error_message(form))

        card.description = form.cleaned_data["description"]
        card.save(update_fields=["description", "updated_at"])
        template_path = template_for_request(request, "_card_description_updated.html")
        return render(request, template_path, {"card": card})


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

        if attach:
            card.labels.add(label)
        else:
            card.labels.remove(label)

        card = fetch_card(pk)
        template_path = template_for_request(request, "_card_labels_updated.html")
        return render(request, template_path, card_context(card))


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
        .prefetch_related("labels")
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
