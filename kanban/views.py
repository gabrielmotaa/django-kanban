import json
from http import HTTPStatus

from django.db import transaction
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    QueryDict,
)
from django.shortcuts import get_object_or_404, render
from django.views import View

from kanban.forms import (
    BoardEditForm,
    CardCreateForm,
    CardEditForm,
    ColumnCreateForm,
    ColumnEditForm,
)
from kanban.models import Board, Card, Column
from kanban.utils import template_for_request


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "kanban/home.html")


def index(request: HttpRequest, tech: str) -> HttpResponse:
    board = get_object_or_404(Board.objects.prefetch_related("columns__cards"), pk=1)
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
        },
    )


class CardCreateView(View):
    def post(self, request: HttpRequest) -> HttpResponse:
        form = CardCreateForm(request.POST)
        if not form.is_valid():
            return HttpResponseBadRequest(form.errors.as_text())

        column = get_object_or_404(Column, pk=form.cleaned_data["column_id"])
        order = column.cards.count()
        card = Card.objects.create(
            column=column, title=form.cleaned_data["title"], order=order
        )
        template_path = template_for_request(request, "_card.html")
        return render(request, template_path, {"card": card})


class CardDetailView(View):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        card = get_object_or_404(Card, pk=pk)
        template_path = template_for_request(request, "_card.html")
        return render(request, template_path, {"card": card})

    def patch(self, request: HttpRequest, pk: int) -> HttpResponse:
        card = get_object_or_404(Card, pk=pk)
        data = QueryDict(request.body)
        form = CardEditForm(data)
        if not form.is_valid():
            if form.non_field_errors():
                return HttpResponseBadRequest(form.non_field_errors()[0])
            return HttpResponseBadRequest(form.errors.as_text())

        if form.cleaned_data["title"]:
            card.title = form.cleaned_data["title"]
            card.save(update_fields=["title"])
            template_path = template_for_request(request, "_card.html")
            return render(request, template_path, {"card": card})

        target_column = get_object_or_404(Column, pk=form.cleaned_data["column_id"])
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
        card = get_object_or_404(Card, pk=pk)
        card.delete()
        return HttpResponse(status=HTTPStatus.NO_CONTENT)


class ColumnCreateView(View):
    def post(self, request: HttpRequest) -> HttpResponse:
        form = ColumnCreateForm(request.POST)
        if not form.is_valid():
            return HttpResponseBadRequest(form.errors.as_text())

        board = get_object_or_404(Board, pk=form.cleaned_data["board_id"])
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


class ColumnDetailView(View):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        column = get_object_or_404(Column, pk=pk)
        template_path = template_for_request(request, "_column.html")
        return render(request, template_path, {"column": column})

    def patch(self, request: HttpRequest, pk: int) -> HttpResponse:
        column = get_object_or_404(Column, pk=pk)
        data = QueryDict(request.body)
        form = ColumnEditForm(data)
        if not form.is_valid():
            if form.non_field_errors():
                return HttpResponseBadRequest(form.non_field_errors()[0])
            return HttpResponseBadRequest(form.errors.as_text())

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
        column = get_object_or_404(Column, pk=pk)
        column.delete()
        return HttpResponse(status=HTTPStatus.NO_CONTENT)


class BoardDetailView(View):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        board = get_object_or_404(Board, pk=pk)
        template_path = template_for_request(request, "_board_title.html")
        return render(request, template_path, {"board": board})

    def patch(self, request: HttpRequest, pk: int) -> HttpResponse:
        board = get_object_or_404(Board, pk=pk)
        data = QueryDict(request.body)
        form = BoardEditForm(data)
        if not form.is_valid():
            return HttpResponseBadRequest(form.errors.as_text())

        board.title = form.cleaned_data["title"]
        board.save(update_fields=["title"])

        template_path = template_for_request(request, "_board_title.html")
        return render(request, template_path, {"board": board})
