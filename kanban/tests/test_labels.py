"""Labels (issue 008): model, form, admin, views and the board query budget."""

import json
from urllib.parse import urlencode

import pytest
from django.contrib.admin.sites import AdminSite
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from kanban.admin import CardAdmin, LabelAdmin
from kanban.forms import LabelForm
from kanban.models import Board, Card, Column, Label

pytestmark = pytest.mark.django_db

VARIANTS = ["templates", "components"]


def headers(tech: str) -> dict:
    return {"HTTP_X_WEB_COMPONENTS": "true"} if tech == "components" else {}


@pytest.fixture
def board() -> Board:
    return Board.objects.create(id=1, title="Board")


@pytest.fixture
def other_board() -> Board:
    return Board.objects.create(id=2, title="Other")


@pytest.fixture
def column(board) -> Column:
    return Column.objects.create(board=board, title="Doing", order=0)


@pytest.fixture
def card(column) -> Card:
    return Card.objects.create(column=column, title="Write docs", order=0)


@pytest.fixture
def bug(board) -> Label:
    return Label.objects.create(board=board, name="Bug", color="#ef4444")


def send(client, tech, method, url, data=None):
    extra = headers(tech)
    if method == "post":
        return client.post(url, data or {}, **extra)
    if method == "delete":
        return client.delete(f"{url}?{urlencode(data or {})}", **extra)
    return client.patch(
        url,
        urlencode(data or {}),
        content_type="application/x-www-form-urlencoded",
        **extra,
    )


# -- model ------------------------------------------------------------------


def test_label_defaults_and_str(board):
    label = Label.objects.create(board=board)
    assert label.name == ""
    assert label.color == "#64748b"
    assert str(label) == "Cinza"
    assert str(Label(board=board, name="Bug")) == "Bug"


def test_labels_are_ordered_by_name(board):
    Label.objects.create(board=board, name="Zeta")
    Label.objects.create(board=board, name="Alfa")
    assert [label.name for label in board.labels.all()] == ["Alfa", "Zeta"]


def test_label_color_is_validated(board):
    label = Label(board=board, name="x", color="#000000")
    with pytest.raises(ValidationError):
        label.full_clean()
    Label(board=board, name="x", color="#ef4444").full_clean()


def test_blank_name_allowed(board):
    Label(board=board, name="", color="#ef4444").full_clean()


def test_label_fg_color_and_color_name(board):
    amber = Label(board=board, color="#f59e0b")
    assert amber.fg_color == "#1e293b"
    assert amber.color_name == "Âmbar"
    assert Label(board=board, color="#ef4444").fg_color == "#ffffff"


def test_card_labels_many_to_many(card, bug):
    card.labels.add(bug)
    assert list(bug.cards.all()) == [card]


def test_deleting_board_deletes_labels(board, bug):
    board.delete()
    assert not Label.objects.exists()


# -- form ---------------------------------------------------------------------


def test_label_form_valid_and_blank_name():
    form = LabelForm({"name": "", "color": "#ef4444"})
    assert form.is_valid()
    assert form.cleaned_data["name"] == ""


def test_label_form_invalid_color():
    form = LabelForm({"name": "x", "color": "#123456"})
    assert not form.is_valid()
    assert "color" in form.errors


def test_label_form_name_too_long():
    form = LabelForm({"name": "x" * 31, "color": "#ef4444"})
    assert not form.is_valid()
    assert "no máximo 30 caracteres" in form.errors["name"][0]


# -- admin --------------------------------------------------------------------


def test_label_admin_color_preview(bug):
    preview = LabelAdmin(Label, AdminSite()).color_preview(bug)
    assert "#ef4444" in preview


def test_card_admin_uses_horizontal_filter_for_labels():
    assert CardAdmin.filter_horizontal == ("labels",)


# -- attach / detach ----------------------------------------------------------


@pytest.mark.parametrize("tech", VARIANTS)
class TestAttachDetach:
    def test_attach(self, client: Client, card, bug, tech):
        url = reverse("card_labels", args=[card.pk])
        response = send(client, tech, "post", url, {"label_id": bug.pk})
        assert response.status_code == 200
        assert list(card.labels.all()) == [bug]
        html = response.content.decode()
        assert f'id="card-{card.pk}"' in html
        if tech == "components":
            assert f'labels="{bug.pk}"' in html
            assert "<kanban-card-labels" in html
        else:
            assert 'hx-swap-oob="true"' in html
            assert 'id="label-popover"' in html
            assert 'id="label-pills"' in html
            assert "Bug" in html

    def test_attach_is_idempotent(self, client: Client, card, bug, tech):
        card.labels.add(bug)
        url = reverse("card_labels", args=[card.pk])
        assert send(client, tech, "post", url, {"label_id": bug.pk}).status_code == 200
        assert card.labels.count() == 1

    def test_detach(self, client: Client, card, bug, tech):
        card.labels.add(bug)
        url = reverse("card_labels", args=[card.pk])
        response = send(client, tech, "delete", url, {"label_id": bug.pk})
        assert response.status_code == 200
        assert card.labels.count() == 0

    def test_attach_foreign_board_label_rejected(
        self, client: Client, card, other_board, tech
    ):
        foreign = Label.objects.create(board=other_board, name="Nope")
        url = reverse("card_labels", args=[card.pk])
        response = send(client, tech, "post", url, {"label_id": foreign.pk})
        assert response.status_code == 400
        assert "Etiqueta de outro quadro." in response.content.decode()
        assert card.labels.count() == 0

    def test_attach_missing_label(self, client: Client, card, tech):
        url = reverse("card_labels", args=[card.pk])
        response = send(client, tech, "post", url, {"label_id": 999})
        assert response.status_code == 404
        assert "Etiqueta não encontrada." in response.content.decode()

    def test_attach_without_label_id(self, client: Client, card, tech):
        url = reverse("card_labels", args=[card.pk])
        response = send(client, tech, "post", url, {})
        assert response.status_code == 400

    def test_missing_card(self, client: Client, bug, tech):
        url = reverse("card_labels", args=[999])
        response = send(client, tech, "post", url, {"label_id": bug.pk})
        assert response.status_code == 404
        assert "Card não encontrado." in response.content.decode()

    def test_detach_missing_card(self, client: Client, bug, tech):
        url = reverse("card_labels", args=[999])
        response = send(client, tech, "delete", url, {"label_id": bug.pk})
        assert response.status_code == 404


# -- create / edit / delete ---------------------------------------------------


@pytest.mark.parametrize("tech", VARIANTS)
class TestLabelCrud:
    def test_create(self, client: Client, board, card, tech):
        data = {
            "board_id": board.pk,
            "card_id": card.pk,
            "name": "Design",
            "color": "#8b5cf6",
        }
        response = send(client, tech, "post", reverse("label_create"), data)
        assert response.status_code == 200
        label = Label.objects.get(name="Design")
        assert (label.board, label.color) == (board, "#8b5cf6")
        html = response.content.decode()
        if tech == "components":
            assert "<kanban-board" in html
            registry = _registry(html)
            assert [entry["name"] for entry in registry] == ["Design"]
        else:
            assert 'id="label-popover"' in html
            assert "Design" in html

    def test_create_blank_name(self, client: Client, board, card, tech):
        data = {
            "board_id": board.pk,
            "card_id": card.pk,
            "name": "",
            "color": "#ef4444",
        }
        response = send(client, tech, "post", reverse("label_create"), data)
        assert response.status_code == 200
        assert Label.objects.filter(name="").count() == 1

    def test_create_invalid_color(self, client: Client, board, card, tech):
        data = {
            "board_id": board.pk,
            "card_id": card.pk,
            "name": "x",
            "color": "#123456",
        }
        response = send(client, tech, "post", reverse("label_create"), data)
        assert response.status_code == 400
        assert "Cor inválida." in response.content.decode()
        assert not Label.objects.exists()

    def test_create_missing_board(self, client: Client, card, tech):
        data = {"board_id": 999, "card_id": card.pk, "name": "x", "color": "#ef4444"}
        response = send(client, tech, "post", reverse("label_create"), data)
        assert response.status_code == 404
        assert "Quadro não encontrado." in response.content.decode()

    def test_edit_updates_every_card_showing_the_label(
        self, client: Client, board, column, card, bug, tech
    ):
        second = Card.objects.create(column=column, title="Other", order=1)
        card.labels.add(bug)
        second.labels.add(bug)
        data = {"card_id": card.pk, "name": "Defect", "color": "#f97316"}
        response = send(
            client, tech, "patch", reverse("label_detail", args=[bug.pk]), data
        )
        assert response.status_code == 200
        bug.refresh_from_db()
        assert (bug.name, bug.color) == ("Defect", "#f97316")
        html = response.content.decode()
        if tech == "components":
            registry = _registry(html)
            assert registry[0]["name"] == "Defect"
            assert registry[0]["color"] == "#f97316"
        else:
            # One out-of-band card front per affected card.
            assert html.count('hx-swap-oob="true"') >= 2
            assert f'id="card-{card.pk}"' in html
            assert f'id="card-{second.pk}"' in html
            assert "Defect" in html

    def test_edit_missing(self, client: Client, card, tech):
        data = {"card_id": card.pk, "name": "x", "color": "#ef4444"}
        response = send(
            client, tech, "patch", reverse("label_detail", args=[999]), data
        )
        assert response.status_code == 404
        assert "Etiqueta não encontrada." in response.content.decode()

    def test_edit_invalid_color(self, client: Client, card, bug, tech):
        data = {"card_id": card.pk, "name": "x", "color": "nope"}
        response = send(
            client, tech, "patch", reverse("label_detail", args=[bug.pk]), data
        )
        assert response.status_code == 400
        bug.refresh_from_db()
        assert bug.name == "Bug"

    def test_edit_from_a_card_of_another_board_rejected(
        self, client: Client, other_board, bug, tech
    ):
        other_column = Column.objects.create(board=other_board, title="C", order=0)
        stranger = Card.objects.create(column=other_column, title="S", order=0)
        data = {"card_id": stranger.pk, "name": "x", "color": "#ef4444"}
        response = send(
            client, tech, "patch", reverse("label_detail", args=[bug.pk]), data
        )
        assert response.status_code == 400
        assert "Etiqueta de outro quadro." in response.content.decode()

    def test_delete_removes_label_from_cards(
        self, client: Client, column, card, bug, tech
    ):
        second = Card.objects.create(column=column, title="Other", order=1)
        card.labels.add(bug)
        second.labels.add(bug)
        response = send(
            client,
            tech,
            "delete",
            reverse("label_detail", args=[bug.pk]),
            {"card_id": card.pk},
        )
        assert response.status_code == 200
        assert not Label.objects.filter(pk=bug.pk).exists()
        assert card.labels.count() == 0
        html = response.content.decode()
        if tech == "templates":
            assert f'id="card-{card.pk}"' in html
            assert f'id="card-{second.pk}"' in html
        else:
            assert _registry(html) == []

    def test_delete_missing(self, client: Client, card, tech):
        response = send(
            client,
            tech,
            "delete",
            reverse("label_detail", args=[999]),
            {"card_id": card.pk},
        )
        assert response.status_code == 404


def _registry(html: str) -> list:
    import re
    from html import unescape

    match = re.search(r'<kanban-board[^>]* labels="([^"]*)"', html)
    assert match, html
    return json.loads(unescape(match.group(1)))


# -- rendering ------------------------------------------------------------------


@pytest.mark.parametrize("tech", VARIANTS)
def test_card_front_lists_labels_in_label_order(client: Client, board, card, tech):
    zeta = Label.objects.create(board=board, name="Zeta", color="#ef4444")
    alfa = Label.objects.create(board=board, name="Alfa", color="#10b981")
    card.labels.add(zeta, alfa)
    html = client.get(
        reverse("card_detail", args=[card.pk]), **headers(tech)
    ).content.decode()
    if tech == "components":
        assert f'labels="{alfa.pk},{zeta.pk}"' in html
    else:
        assert html.index("Alfa") < html.index("Zeta") < html.index("Write docs")


def test_components_index_exposes_registry(client: Client, board, bug):
    html = client.get(reverse("index", args=["components"])).content.decode()
    registry = _registry(html)
    assert registry == [
        {
            "id": bug.pk,
            "name": "Bug",
            "color": "#ef4444",
            "fg": "#ffffff",
            "colorName": "Vermelho",
            "href": reverse("label_detail", args=[bug.pk]),
        }
    ]


@pytest.mark.parametrize("tech", VARIANTS)
def test_dialog_includes_labels_section(client: Client, card, bug, tech):
    card.labels.add(bug)
    html = client.get(
        reverse("card_dialog", args=[card.pk]), **headers(tech)
    ).content.decode()
    if tech == "components":
        assert "<kanban-card-labels" in html
        assert f'card-labels="{bug.pk}"' in html
    else:
        assert 'id="card-labels"' in html
        assert "Buscar etiquetas…" in html
        assert "Criar uma nova etiqueta" in html


@pytest.mark.parametrize("tech", VARIANTS)
def test_board_page_query_count_does_not_grow_with_cards(client: Client, board, tech):
    column = Column.objects.create(board=board, title="C", order=0)
    label = Label.objects.create(board=board, name="L")

    def count_queries() -> int:
        with CaptureQueriesContext(connection) as ctx:
            assert client.get(reverse("index", args=[tech])).status_code == 200
        return len(ctx)

    card = Card.objects.create(column=column, title="one", order=0)
    card.labels.add(label)
    baseline = count_queries()
    for i in range(10):
        extra = Card.objects.create(column=column, title=f"c{i}", order=i + 1)
        extra.labels.add(label)
    assert count_queries() == baseline


def test_fixture_loads_labels_on_board_one():
    call_command("loaddata", "initial_data", verbosity=0)
    names = set(Label.objects.filter(board_id=1).values_list("name", flat=True))
    assert names == {"Bug", "Melhoria", "Urgente", "Design"}
    assert Card.objects.filter(labels__isnull=False).exists()
