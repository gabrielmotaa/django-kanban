import json
import re
from html import unescape
from urllib.parse import urlencode

import pytest
from django.test import Client
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from kanban.models import Board, Card, Column

pytestmark = pytest.mark.django_db


@pytest.fixture
def board() -> Board:
    return Board.objects.create(id=1, title="Test Board")


@pytest.fixture
def col_a(board) -> Column:
    return Column.objects.create(board=board, title="Col A", order=0)


@pytest.fixture
def col_b(board) -> Column:
    return Column.objects.create(board=board, title="Col B", order=1)


def test_home(client: Client):
    response = client.get(reverse("home"))
    assert response.status_code == 200
    assertTemplateUsed(response, "kanban/home.html")


def test_template_index(client: Client, board: Board):
    response = client.get(reverse("index", args=["templates"]))
    assert response.status_code == 200
    assertTemplateUsed(response, "kanban/templates/index.html")


def test_components_index(client: Client, board: Board):
    response = client.get(reverse("index", args=["components"]))
    assert response.status_code == 200
    assertTemplateUsed(response, "kanban/components/index.html")


def test_column_move(client: Client, col_a: Column, col_b: Column):
    response = client.patch(
        reverse("column_detail", args=[col_b.pk]),
        data=urlencode({"order": 0}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 204
    col_a.refresh_from_db()
    col_b.refresh_from_db()
    assert col_b.order == 0
    assert col_a.order == 1


def test_column_move_with_three_columns(
    client: Client, board: Board, col_a: Column, col_b: Column
):
    col_c = Column.objects.create(board=board, title="Col C", order=2)
    response = client.patch(
        reverse("column_detail", args=[col_c.pk]),
        data=urlencode({"order": 1}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 204
    col_a.refresh_from_db()
    col_b.refresh_from_db()
    col_c.refresh_from_db()
    assert col_a.order == 0
    assert col_c.order == 1
    assert col_b.order == 2


def test_column_delete(client: Client, col_a: Column):
    response = client.delete(reverse("column_detail", args=[col_a.pk]))
    assert response.status_code == 204
    assert not Column.objects.filter(pk=col_a.pk).exists()


def test_card_delete(client: Client, col_a: Column):
    card = Card.objects.create(column=col_a, title="Delete Me", order=0)
    response = client.delete(reverse("card_detail", args=[card.pk]))
    assert response.status_code == 204
    assert not Card.objects.filter(pk=card.pk).exists()


@pytest.mark.parametrize("web_components", [True, False])
def test_card_create(client: Client, col_a: Column, web_components: bool):
    headers = {"X-Web-Components": "true"} if web_components else {}
    template_name = (
        "kanban/components/_card.html"
        if web_components
        else "kanban/templates/_card.html"
    )

    response = client.post(
        reverse("card_create"),
        {"column_id": col_a.pk, "title": "New Test Card"},
        headers=headers,
    )
    assert response.status_code == 200
    assertTemplateUsed(response, template_name)

    new_card = Card.objects.get(title="New Test Card")
    assert new_card.column == col_a
    assert new_card.order == 0


@pytest.mark.parametrize("web_components", [True, False])
def test_column_create(
    client: Client, board: Board, col_a: Column, col_b: Column, web_components: bool
):
    headers = {"X-Web-Components": "true"} if web_components else {}
    template_name = (
        "kanban/components/_column.html"
        if web_components
        else "kanban/templates/_column.html"
    )

    response = client.post(
        reverse("column_create"),
        {"board_id": board.pk, "title": "New Column"},
        headers=headers,
    )
    assert response.status_code == 200
    assertTemplateUsed(response, template_name)
    new_col = Column.objects.get(title="New Column")
    assert new_col.board == board
    assert new_col.order == 2


@pytest.mark.parametrize("web_components", [True, False])
def test_column_edit(client: Client, col_a: Column, web_components: bool):
    headers = {"X-Web-Components": "true"} if web_components else {}
    template_name = (
        "kanban/components/_column.html"
        if web_components
        else "kanban/templates/_column.html"
    )

    response = client.patch(
        reverse("column_detail", args=[col_a.pk]),
        data=urlencode({"title": "Renamed Col A"}),
        content_type="application/x-www-form-urlencoded",
        headers=headers,
    )
    assert response.status_code == 200
    assertTemplateUsed(response, template_name)
    col_a.refresh_from_db()
    assert col_a.title == "Renamed Col A"


@pytest.mark.parametrize("web_components", [True, False])
def test_column_create_with_color(
    client: Client, board: Board, col_a: Column, col_b: Column, web_components: bool
):
    headers = {"X-Web-Components": "true"} if web_components else {}
    template_name = (
        "kanban/components/_column.html"
        if web_components
        else "kanban/templates/_column.html"
    )

    response = client.post(
        reverse("column_create"),
        {"board_id": board.pk, "title": "New Green Column", "color": "#10b981"},
        headers=headers,
    )
    assert response.status_code == 200
    assertTemplateUsed(response, template_name)
    new_col = Column.objects.get(title="New Green Column")
    assert new_col.board == board
    assert new_col.color == "#10b981"


@pytest.mark.parametrize("web_components", [True, False])
def test_column_edit_color(client: Client, col_a: Column, web_components: bool):
    headers = {"X-Web-Components": "true"} if web_components else {}
    template_name = (
        "kanban/components/_column.html"
        if web_components
        else "kanban/templates/_column.html"
    )

    response = client.patch(
        reverse("column_detail", args=[col_a.pk]),
        data=urlencode({"title": "Col A", "color": "#ec4899"}),
        content_type="application/x-www-form-urlencoded",
        headers=headers,
    )
    assert response.status_code == 200
    assertTemplateUsed(response, template_name)
    col_a.refresh_from_db()
    assert col_a.color == "#ec4899"


@pytest.mark.parametrize("web_components", [True, False])
def test_column_edit_only_color(client: Client, col_a: Column, web_components: bool):
    headers = {"X-Web-Components": "true"} if web_components else {}
    template_name = (
        "kanban/components/_column.html"
        if web_components
        else "kanban/templates/_column.html"
    )

    response = client.patch(
        reverse("column_detail", args=[col_a.pk]),
        data=urlencode({"color": "#ec4899"}),
        content_type="application/x-www-form-urlencoded",
        headers=headers,
    )
    assert response.status_code == 200
    assertTemplateUsed(response, template_name)
    col_a.refresh_from_db()
    assert col_a.color == "#ec4899"


@pytest.mark.parametrize("web_components", [True, False])
def test_board_edit(client: Client, board: Board, web_components: bool):
    headers = {"X-Web-Components": "true"} if web_components else {}
    template_name = (
        "kanban/components/_board_title.html"
        if web_components
        else "kanban/templates/_board_title.html"
    )

    response = client.patch(
        reverse("board_detail", args=[board.pk]),
        data=urlencode({"title": "Renamed Board"}),
        content_type="application/x-www-form-urlencoded",
        headers=headers,
    )
    assert response.status_code == 200
    assertTemplateUsed(response, template_name)
    board.refresh_from_db()
    assert board.title == "Renamed Board"


def test_column_move_invalid(client: Client, col_a: Column, col_b: Column):
    response = client.patch(
        reverse("column_detail", args=[col_b.pk]),
        data=urlencode({"order": -5}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 400


def test_card_create_invalid(client: Client, col_a: Column):
    response = client.post(reverse("card_create"), {"column_id": col_a.pk, "title": ""})
    assert response.status_code == 400


def test_column_create_invalid(client: Client, board: Board):
    response = client.post(
        reverse("column_create"), {"board_id": board.pk, "title": ""}
    )
    assert response.status_code == 400


def test_column_edit_invalid_empty_fields(client: Client, col_a: Column):
    response = client.patch(
        reverse("column_detail", args=[col_a.pk]),
        data=urlencode({"title": "", "color": ""}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 400
    assert response.content.decode("utf-8") == "No title or color provided"


def test_board_edit_invalid(client: Client, board: Board):
    response = client.patch(
        reverse("board_detail", args=[board.pk]),
        data=urlencode({"title": ""}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 400


@pytest.mark.parametrize("web_components", [True, False])
def test_card_edit_get(client: Client, col_a: Column, web_components: bool):
    headers = {"X-Web-Components": "true"} if web_components else {}
    template_name = (
        "kanban/components/_card.html"
        if web_components
        else "kanban/templates/_card.html"
    )

    card = Card.objects.create(column=col_a, title="Original Card", order=0)
    response = client.get(reverse("card_detail", args=[card.pk]), headers=headers)
    assert response.status_code == 200
    assertTemplateUsed(response, template_name)
    assert b"Original Card" in response.content


@pytest.mark.parametrize("web_components", [True, False])
def test_card_edit_post_success(client: Client, col_a: Column, web_components: bool):
    headers = {"X-Web-Components": "true"} if web_components else {}
    template_name = (
        "kanban/components/_card.html"
        if web_components
        else "kanban/templates/_card.html"
    )

    card = Card.objects.create(column=col_a, title="Original Card", order=0)
    response = client.patch(
        reverse("card_detail", args=[card.pk]),
        data=urlencode({"title": "Updated Card Title"}),
        content_type="application/x-www-form-urlencoded",
        headers=headers,
    )
    assert response.status_code == 200
    assertTemplateUsed(response, template_name)
    card.refresh_from_db()
    assert card.title == "Updated Card Title"


def test_card_edit_post_invalid(client: Client, col_a: Column):
    card = Card.objects.create(column=col_a, title="Original Card", order=0)
    response = client.patch(
        reverse("card_detail", args=[card.pk]),
        data=urlencode({"title": ""}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 400


def test_card_move_same_column(client: Client, col_a: Column):
    card_1 = Card.objects.create(column=col_a, title="Card 1", order=0)
    card_2 = Card.objects.create(column=col_a, title="Card 2", order=1)
    response = client.patch(
        reverse("card_detail", args=[card_1.pk]),
        data=urlencode({"column_id": col_a.pk, "order": 1}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 204
    card_1.refresh_from_db()
    card_2.refresh_from_db()
    assert card_2.order == 0
    assert card_1.order == 1


def test_card_move_different_column(client: Client, col_a: Column, col_b: Column):
    card_1 = Card.objects.create(column=col_a, title="Card 1", order=0)
    response = client.patch(
        reverse("card_detail", args=[card_1.pk]),
        data=urlencode({"column_id": col_b.pk, "order": 0}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 204
    card_1.refresh_from_db()
    assert card_1.column == col_b
    assert card_1.order == 0


def test_card_move_same_column_with_three_cards(client: Client, col_a: Column):
    card_1 = Card.objects.create(column=col_a, title="Card 1", order=0)
    card_2 = Card.objects.create(column=col_a, title="Card 2", order=1)
    card_3 = Card.objects.create(column=col_a, title="Card 3", order=2)
    response = client.patch(
        reverse("card_detail", args=[card_3.pk]),
        data=urlencode({"column_id": col_a.pk, "order": 1}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 204
    card_1.refresh_from_db()
    card_2.refresh_from_db()
    card_3.refresh_from_db()
    assert card_1.order == 0
    assert card_3.order == 1
    assert card_2.order == 2


def test_card_move_different_column_with_unmoved_source(
    client: Client, col_a: Column, col_b: Column
):
    card_1 = Card.objects.create(column=col_a, title="Card 1", order=0)
    card_2 = Card.objects.create(column=col_a, title="Card 2", order=1)
    card_3 = Card.objects.create(column=col_a, title="Card 3", order=2)
    response = client.patch(
        reverse("card_detail", args=[card_3.pk]),
        data=urlencode({"column_id": col_b.pk, "order": 0}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 204
    card_1.refresh_from_db()
    card_2.refresh_from_db()
    card_3.refresh_from_db()
    assert card_1.order == 0
    assert card_2.order == 1
    assert card_3.column == col_b
    assert card_3.order == 0


def test_card_move_different_column_reorder_target(
    client: Client, col_a: Column, col_b: Column
):
    card_a1 = Card.objects.create(column=col_a, title="Card A1", order=0)
    card_b1 = Card.objects.create(column=col_b, title="Card B1", order=0)
    response = client.patch(
        reverse("card_detail", args=[card_a1.pk]),
        data=urlencode({"column_id": col_b.pk, "order": 0}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 204
    card_a1.refresh_from_db()
    card_b1.refresh_from_db()
    assert card_a1.column == col_b
    assert card_a1.order == 0
    assert card_b1.column == col_b
    assert card_b1.order == 1


def test_card_move_invalid(client: Client, col_b: Column):
    card = Card.objects.create(column=col_b, title="Test Card", order=0)
    response = client.patch(
        reverse("card_detail", args=[card.pk]),
        data=urlencode({"column_id": col_b.pk, "order": -1}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 400


def test_index_invalid_tech(client: Client, board: Board):
    response = client.get(reverse("index", args=["invalid-tech"]))
    assert response.status_code == 404


def test_card_move_different_column_reorder_source(
    client: Client, col_a: Column, col_b: Column
):
    card_1 = Card.objects.create(column=col_a, title="Card 1", order=0)
    card_2 = Card.objects.create(column=col_a, title="Card 2", order=1)
    response = client.patch(
        reverse("card_detail", args=[card_1.pk]),
        data=urlencode({"column_id": col_b.pk, "order": 0}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 204
    card_1.refresh_from_db()
    card_2.refresh_from_db()
    assert card_1.column == col_b
    assert card_1.order == 0
    assert card_2.column == col_a
    assert card_2.order == 0


@pytest.mark.parametrize("web_components", [True, False])
def test_column_detail_get(client: Client, col_a: Column, web_components: bool):
    headers = {"X-Web-Components": "true"} if web_components else {}
    template_name = (
        "kanban/components/_column.html"
        if web_components
        else "kanban/templates/_column.html"
    )
    response = client.get(reverse("column_detail", args=[col_a.pk]), headers=headers)
    assert response.status_code == 200
    assertTemplateUsed(response, template_name)
    assert col_a.title.encode("utf-8") in response.content


def test_column_edit_invalid_field_errors(client: Client, col_a: Column):
    response = client.patch(
        reverse("column_detail", args=[col_a.pk]),
        data=urlencode({"title": "Valid Title", "order": -5}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 400
    assert "order" in response.content.decode("utf-8")


@pytest.mark.parametrize("web_components", [True, False])
def test_board_detail_get(client: Client, board: Board, web_components: bool):
    headers = {"X-Web-Components": "true"} if web_components else {}
    template_name = (
        "kanban/components/_board_title.html"
        if web_components
        else "kanban/templates/_board_title.html"
    )
    response = client.get(reverse("board_detail", args=[board.pk]), headers=headers)
    assert response.status_code == 200
    assertTemplateUsed(response, template_name)
    assert board.title.encode("utf-8") in response.content


def test_card_move_missing_order(client: Client, col_a: Column, col_b: Column):
    card = Card.objects.create(column=col_a, title="Card 1", order=0)
    response = client.patch(
        reverse("card_detail", args=[card.pk]),
        data=urlencode({"column_id": col_b.pk}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 400


def test_card_move_missing_column(client: Client, col_a: Column):
    card = Card.objects.create(column=col_a, title="Card 1", order=0)
    response = client.patch(
        reverse("card_detail", args=[card.pk]),
        data=urlencode({"order": 1}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 400


def test_card_edit_invalid_field_errors(client: Client, col_a: Column):
    card = Card.objects.create(column=col_a, title="Original Card", order=0)
    response = client.patch(
        reverse("card_detail", args=[card.pk]),
        data=urlencode({"title": "Valid Title", "order": -5}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 400
    assert "order" in response.content.decode("utf-8")


def test_card_move_same_column_clamp_order(client: Client, col_a: Column):
    card_1 = Card.objects.create(column=col_a, title="Card 1", order=0)
    card_2 = Card.objects.create(column=col_a, title="Card 2", order=1)
    response = client.patch(
        reverse("card_detail", args=[card_1.pk]),
        data=urlencode({"column_id": col_a.pk, "order": 99}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 204
    card_1.refresh_from_db()
    card_2.refresh_from_db()
    assert card_2.order == 0
    assert card_1.order == 1


def test_card_move_different_column_clamp_order(
    client: Client, col_a: Column, col_b: Column
):
    card_a1 = Card.objects.create(column=col_a, title="Card A1", order=0)
    card_b1 = Card.objects.create(column=col_b, title="Card B1", order=0)
    response = client.patch(
        reverse("card_detail", args=[card_a1.pk]),
        data=urlencode({"column_id": col_b.pk, "order": 99}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 204
    card_a1.refresh_from_db()
    card_b1.refresh_from_db()
    assert card_b1.order == 0
    assert card_a1.column == col_b
    assert card_a1.order == 1


def test_column_move_clamp_order(
    client: Client, board: Board, col_a: Column, col_b: Column
):
    response = client.patch(
        reverse("column_detail", args=[col_a.pk]),
        data=urlencode({"order": 99}),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 204
    col_a.refresh_from_db()
    col_b.refresh_from_db()
    assert col_b.order == 0
    assert col_a.order == 1


def test_template_index_accessible_names(client: Client, board: Board, col_a: Column):
    html = client.get(reverse("index", args=["templates"])).content.decode()
    assert 'aria-label="Opções da coluna"' in html
    assert 'aria-label="Salvar nome"' in html
    assert 'aria-label="Cancelar edição"' in html
    assert 'aria-label="Nome da coluna"' in html
    assert 'aria-label="Título do quadro"' in html
    for _hex, name in Column.COLOR_CHOICES:
        assert f'aria-label="{name}"' in html


def test_components_index_exposes_color_names(client: Client, board: Board):
    html = client.get(reverse("index", args=["components"])).content.decode()
    names = [name for _hex, name in _palette_from(html)]
    assert names == [name for _hex, name in Column.COLOR_CHOICES]


# --- Issue 003: components are self-contained (URLs, palette, fg-color) ---

WC = {"HTTP_X_WEB_COMPONENTS": "true"}


def _palette_from(html: str) -> list:
    match = re.search(r'<kanban-board [^>]*colors="([^"]*)"', html)
    assert match, "kanban-board has no colors attribute"
    return json.loads(unescape(match.group(1)))


def test_components_card_fragment_has_href(client: Client, col_a: Column):
    card = Card.objects.create(column=col_a, title="C", order=0)
    html = client.get(reverse("card_detail", args=[card.pk]), **WC).content.decode()
    assert f'href="{reverse("card_detail", args=[card.pk])}"' in html


def test_components_column_fragment_has_urls_and_fg_color(client: Client, board: Board):
    column = Column.objects.create(board=board, title="Amber", order=0, color="#f59e0b")
    html = client.get(reverse("column_detail", args=[column.pk]), **WC).content.decode()
    assert f'href="{reverse("column_detail", args=[column.pk])}"' in html
    assert f'create-card-url="{reverse("card_create")}"' in html
    assert f'fg-color="{column.fg_color}"' in html
    assert 'fg-color="#1e293b"' in html


def test_components_board_title_fragment_has_href(client: Client, board: Board):
    html = client.get(reverse("board_detail", args=[board.pk]), **WC).content.decode()
    assert f'href="{reverse("board_detail", args=[board.pk])}"' in html


def test_components_index_is_self_contained(client: Client, board: Board, col_a):
    html = client.get(reverse("index", args=["components"])).content.decode()
    assert f'create-column-url="{reverse("column_create")}"' in html
    assert _palette_from(html) == [list(c) for c in Column.COLOR_CHOICES]
    assert "app-data" not in html
    assert "window.urls" not in html
    assert "window.colorChoices" not in html
    assert "X-Web-Components" not in html


def test_components_column_create_response_has_urls(client: Client, board: Board):
    response = client.post(
        reverse("column_create"), {"board_id": board.pk, "title": "N"}, **WC
    )
    html = response.content.decode()
    assert 'create-card-url="' in html
    assert 'fg-color="#ffffff"' in html


# --- Issue 004: minimal column fragments for components ---


@pytest.mark.parametrize("field", [{"title": "Renamed"}, {"color": "#ef4444"}])
def test_components_column_patch_has_no_cards(client: Client, col_a: Column, field):
    Card.objects.create(column=col_a, title="Alpha", order=0)
    Card.objects.create(column=col_a, title="Beta", order=1)
    response = client.patch(
        reverse("column_detail", args=[col_a.pk]), urlencode(field), **WC
    )
    html = response.content.decode()
    assert response.status_code == 200
    assert "<kanban-column" in html
    assert "kanban-card" not in html
    assert "Alpha" not in html


@pytest.mark.parametrize("field", [{"title": "Renamed"}, {"color": "#ef4444"}])
def test_templates_column_patch_keeps_cards(client: Client, col_a: Column, field):
    Card.objects.create(column=col_a, title="Alpha", order=0)
    Card.objects.create(column=col_a, title="Beta", order=1)
    response = client.patch(reverse("column_detail", args=[col_a.pk]), urlencode(field))
    html = response.content.decode()
    assert "Alpha" in html
    assert "Beta" in html


def test_components_index_renders_cards_inside_columns(client: Client, col_a: Column):
    Card.objects.create(column=col_a, title="Alpha", order=0)
    html = client.get(reverse("index", args=["components"])).content.decode()
    assert "<kanban-card" in html
    assert "Alpha" in html
