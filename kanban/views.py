from http import HTTPStatus

from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from kanban.forms import (
    BoardEditForm,
    CardCreateForm,
    CardEditForm,
    CardMoveForm,
    ColumnCreateForm,
    ColumnEditForm,
    ColumnMoveForm,
)
from kanban.models import Board, Card, Column
from kanban.utils import template_for_request


def templates_index(request: HttpRequest) -> HttpResponse:
    board = get_object_or_404(Board.objects.prefetch_related("columns__cards"), pk=1)
    return render(request, "kanban/templates/index.html", {"board": board})


def components_index(request: HttpRequest) -> HttpResponse:
    board = get_object_or_404(Board.objects.prefetch_related("columns__cards"), pk=1)
    return render(request, "kanban/components/index.html", {"board": board})


@require_http_methods(["POST"])
def card_move(request: HttpRequest) -> HttpResponse:
    form = CardMoveForm(request.POST)

    if not form.is_valid():
        return HttpResponseBadRequest(form.errors.as_text())

    card = get_object_or_404(Card, pk=form.cleaned_data["card_id"])
    target_column = get_object_or_404(Column, pk=form.cleaned_data["column_id"])
    order = form.cleaned_data["order"]

    with transaction.atomic():
        if card.column == target_column:
            # Same column.
            cards = list(target_column.cards.exclude(pk=card.pk))
            order = min(order, len(cards))
            cards.insert(order, card)
            for index, c in enumerate(cards):
                c.order = index
                c.save(update_fields=["order"])
        else:
            # Different column.
            # Remove from origin and reorder.
            cards = list(card.column.cards.exclude(pk=card.pk))
            for index, c in enumerate(cards):
                c.order = index
                c.save(update_fields=["order"])

            # Add into target and reorder.
            cards = list(target_column.cards.all())
            order = min(order, len(cards))
            cards.insert(order, card)
            for index, c in enumerate(cards):
                c.order = index
                c.save(update_fields=["order"])

            card.column = target_column
            card.order = order
            card.save(update_fields=["column", "order"])

    return HttpResponse(status=HTTPStatus.NO_CONTENT)


@require_http_methods(["GET", "POST"])
def card_edit(request: HttpRequest, pk: int) -> HttpResponse:
    card = get_object_or_404(Card, pk=pk)

    if request.method == "POST":
        form = CardEditForm(request.POST)
        if not form.is_valid():
            return HttpResponseBadRequest(form.errors.as_text())
        card.title = form.cleaned_data["title"]
        card.save(update_fields=["title"])

    template_path = template_for_request(request, "_card.html")
    return render(request, template_path, {"card": card})


@require_http_methods(["DELETE"])
def card_delete(request: HttpRequest, pk: int) -> HttpResponse:
    card = get_object_or_404(Card, pk=pk)
    card.delete()
    return HttpResponse(status=HTTPStatus.OK)


@require_http_methods(["POST"])
def column_move(request: HttpRequest) -> HttpResponse:
    form = ColumnMoveForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest(form.errors.as_text())

    column = get_object_or_404(Column, pk=form.cleaned_data["column_id"])
    board = column.board
    order = form.cleaned_data["order"]

    with transaction.atomic():
        columns = list(board.columns.exclude(pk=column.pk))
        order = min(order, len(columns))
        columns.insert(order, column)
        for i, col in enumerate(columns):
            if col.order != i:
                col.order = i
                col.save(update_fields=["order"])

    return HttpResponse(status=HTTPStatus.NO_CONTENT)


@require_http_methods(["DELETE"])
def column_delete(request: HttpRequest, pk: int) -> HttpResponse:
    column = get_object_or_404(Column, pk=pk)
    column.delete()
    return HttpResponse(status=HTTPStatus.OK)


@require_http_methods(["POST"])
def card_create(request: HttpRequest, column_id: int) -> HttpResponse:
    column = get_object_or_404(Column, pk=column_id)
    form = CardCreateForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest(form.errors.as_text())

    order = column.cards.count()
    card = Card.objects.create(
        column=column, title=form.cleaned_data["title"], order=order
    )
    template_path = template_for_request(request, "_card.html")
    return render(request, template_path, {"card": card})


@require_http_methods(["POST"])
def column_create(request: HttpRequest, board_id: int) -> HttpResponse:
    board = get_object_or_404(Board, pk=board_id)
    form = ColumnCreateForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest(form.errors.as_text())

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


@require_http_methods(["POST"])
def column_edit(request: HttpRequest, pk: int) -> HttpResponse:
    column = get_object_or_404(Column, pk=pk)
    form = ColumnEditForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest(form.errors.as_text())

    title = form.cleaned_data.get("title")
    color = form.cleaned_data.get("color")

    if not title and not color:
        return HttpResponseBadRequest("No title or color provided")

    update_fields = []
    if title:
        column.title = title
        update_fields.append("title")
    if color:
        column.color = color
        update_fields.append("color")

    if update_fields:
        column.save(update_fields=update_fields)
    template_path = template_for_request(request, "_column.html")
    return render(request, template_path, {"column": column})


@require_http_methods(["POST"])
def board_edit(request: HttpRequest, pk: int) -> HttpResponse:
    board = get_object_or_404(Board, pk=pk)
    form = BoardEditForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest(form.errors.as_text())

    board.title = form.cleaned_data["title"]
    board.save(update_fields=["title"])
    template_path = template_for_request(request, "_board_title.html")
    return render(request, template_path, {"board": board})
