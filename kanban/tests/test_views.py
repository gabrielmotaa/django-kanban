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


def test_template_index(client: Client, board: Board):
    response = client.get(reverse("templates_index"))
    assert response.status_code == 200
    assertTemplateUsed(response, "kanban/templates/index.html")


def test_components_index(client: Client, board: Board):
    response = client.get(reverse("components_index"))
    assert response.status_code == 200
    assertTemplateUsed(response, "kanban/components/index.html")


def test_column_move(client: Client, col_a: Column, col_b: Column):
    response = client.post(
        reverse("column_move"),
        {"column_id": col_b.pk, "order": 0},
    )
    assert response.status_code == 204
    col_a.refresh_from_db()
    col_b.refresh_from_db()
    assert col_b.order == 0
    assert col_a.order == 1


def test_column_delete(client: Client, col_a: Column):
    response = client.delete(reverse("column_delete", args=[col_a.pk]))
    assert response.status_code == 200
    assert not Column.objects.filter(pk=col_a.pk).exists()


def test_card_delete(client: Client, col_a: Column):
    card = Card.objects.create(column=col_a, title="Delete Me", order=0)
    response = client.delete(reverse("card_delete", args=[card.pk]))
    assert response.status_code == 200
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
        reverse("card_create", args=[col_a.pk]),
        {"title": "New Test Card"},
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
        reverse("column_create", args=[board.pk]),
        {"title": "New Column"},
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

    response = client.post(
        reverse("column_edit", args=[col_a.pk]),
        {"title": "Renamed Col A"},
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
        reverse("column_create", args=[board.pk]),
        {"title": "New Green Column", "color": "#10b981"},
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

    response = client.post(
        reverse("column_edit", args=[col_a.pk]),
        {"title": "Col A", "color": "#ec4899"},
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

    response = client.post(
        reverse("board_edit", args=[board.pk]),
        {"title": "Renamed Board"},
        headers=headers,
    )
    assert response.status_code == 200
    assertTemplateUsed(response, template_name)
    board.refresh_from_db()
    assert board.title == "Renamed Board"


def test_column_move_invalid(client: Client, col_a: Column, col_b: Column):
    response = client.post(
        reverse("column_move"), {"column_id": "invalid_id", "order": -5}
    )
    assert response.status_code == 400


def test_card_create_invalid(client: Client, col_a: Column):
    response = client.post(reverse("card_create", args=[col_a.pk]), {"title": ""})
    assert response.status_code == 400


def test_column_create_invalid(client: Client, board: Board):
    response = client.post(reverse("column_create", args=[board.pk]), {"title": ""})
    assert response.status_code == 400


def test_column_edit_invalid_empty_fields(client: Client, col_a: Column):
    response = client.post(
        reverse("column_edit", args=[col_a.pk]),
        {"title": "", "color": ""},
    )
    assert response.status_code == 400
    assert response.content.decode("utf-8") == "No title or color provided"


def test_board_edit_invalid(client: Client, board: Board):
    response = client.post(reverse("board_edit", args=[board.pk]), {"title": ""})
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
    response = client.get(reverse("card_edit", args=[card.pk]), headers=headers)
    assert response.status_code == 200
    assertTemplateUsed(response, template_name)
    if not web_components:
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
    response = client.post(
        reverse("card_edit", args=[card.pk]),
        {"title": "Updated Card Title"},
        headers=headers,
    )
    assert response.status_code == 200
    assertTemplateUsed(response, template_name)
    card.refresh_from_db()
    assert card.title == "Updated Card Title"


def test_card_edit_post_invalid(client: Client, col_a: Column):
    card = Card.objects.create(column=col_a, title="Original Card", order=0)
    response = client.post(reverse("card_edit", args=[card.pk]), {"title": ""})
    assert response.status_code == 400


def test_card_move_same_column(client: Client, col_a: Column):
    card_1 = Card.objects.create(column=col_a, title="Card 1", order=0)
    card_2 = Card.objects.create(column=col_a, title="Card 2", order=1)
    response = client.post(
        reverse("card_move"),
        {"card_id": card_1.pk, "column_id": col_a.pk, "order": 1},
    )
    assert response.status_code == 204
    card_1.refresh_from_db()
    card_2.refresh_from_db()
    assert card_2.order == 0
    assert card_1.order == 1


def test_card_move_different_column(client: Client, col_a: Column, col_b: Column):
    card_1 = Card.objects.create(column=col_a, title="Card 1", order=0)
    response = client.post(
        reverse("card_move"),
        {"card_id": card_1.pk, "column_id": col_b.pk, "order": 0},
    )
    assert response.status_code == 204
    card_1.refresh_from_db()
    assert card_1.column == col_b
    assert card_1.order == 0


def test_card_move_invalid(client: Client, col_b: Column):
    response = client.post(
        reverse("card_move"),
        {"card_id": -1, "column_id": col_b.pk, "order": 0},
    )
    assert response.status_code == 400
