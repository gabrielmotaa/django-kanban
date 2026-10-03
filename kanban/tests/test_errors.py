"""Error responses (issue 006): every failing request answers with a toast."""

from urllib.parse import urlencode

import pytest
from django.test import Client
from django.urls import reverse

from kanban.models import Board, Card, Column

pytestmark = pytest.mark.django_db

TOAST_MARKUP = {
    "templates": 'class="toast"',
    "components": "<kanban-toast",
}


@pytest.fixture
def board() -> Board:
    return Board.objects.create(id=1, title="Board")


@pytest.fixture
def column(board) -> Column:
    return Column.objects.create(board=board, title="Col", order=0)


@pytest.fixture
def card(column) -> Card:
    return Card.objects.create(column=column, title="Card", order=0)


def call(client: Client, tech: str, method: str, url: str, data=None):
    extra = {"HTTP_X_WEB_COMPONENTS": "true"} if tech == "components" else {}
    if method == "post":
        return client.post(url, data or {}, **extra)
    if method == "get":
        return client.get(url, **extra)
    body = urlencode(data or {})
    return getattr(client, method)(url, body, **extra)


def assert_toast(response, tech: str, status: int, message: str):
    assert response.status_code == status
    html = response.content.decode()
    assert TOAST_MARKUP[tech] in html
    assert message in html
    assert response["X-Toast"] == "true"
    assert response["HX-Reswap"] == "beforeend"


@pytest.mark.parametrize("tech", ["templates", "components"])
class TestCardErrors:
    def test_create_without_title(self, client, column, tech):
        r = call(client, tech, "post", reverse("card_create"), {"column_id": column.pk})
        assert_toast(r, tech, 400, "O título é obrigatório.")

    def test_create_whitespace_title(self, client, column, tech):
        data = {"column_id": column.pk, "title": "   "}
        r = call(client, tech, "post", reverse("card_create"), data)
        assert_toast(r, tech, 400, "O título é obrigatório.")

    def test_create_title_too_long(self, client, column, tech):
        data = {"column_id": column.pk, "title": "x" * 201}
        r = call(client, tech, "post", reverse("card_create"), data)
        assert_toast(r, tech, 400, "no máximo 200 caracteres")

    def test_create_in_missing_column(self, client, tech):
        data = {"column_id": 999, "title": "x"}
        r = call(client, tech, "post", reverse("card_create"), data)
        assert_toast(r, tech, 404, "Coluna não encontrada.")

    def test_get_missing(self, client, tech):
        r = call(client, tech, "get", reverse("card_detail", args=[999]))
        assert_toast(r, tech, 404, "Card não encontrado.")

    def test_patch_missing(self, client, tech):
        r = call(
            client, tech, "patch", reverse("card_detail", args=[999]), {"title": "x"}
        )
        assert_toast(r, tech, 404, "Card não encontrado.")

    def test_patch_empty(self, client, card, tech):
        r = call(client, tech, "patch", reverse("card_detail", args=[card.pk]), {})
        assert_toast(r, tech, 400, "Informe um título ou a nova posição do card.")

    def test_patch_blank_title(self, client, card, tech):
        r = call(
            client,
            tech,
            "patch",
            reverse("card_detail", args=[card.pk]),
            {"title": " "},
        )
        assert_toast(r, tech, 400, "Informe um título ou a nova posição do card.")

    def test_move_to_missing_column(self, client, card, tech):
        data = {"column_id": 999, "order": 0}
        r = call(client, tech, "patch", reverse("card_detail", args=[card.pk]), data)
        assert_toast(r, tech, 404, "Coluna não encontrada.")

    def test_delete_missing(self, client, tech):
        r = call(client, tech, "delete", reverse("card_detail", args=[999]))
        assert_toast(r, tech, 404, "Card não encontrado.")


@pytest.mark.parametrize("tech", ["templates", "components"])
class TestColumnErrors:
    def test_create_without_title(self, client, board, tech):
        r = call(client, tech, "post", reverse("column_create"), {"board_id": board.pk})
        assert_toast(r, tech, 400, "O título é obrigatório.")

    def test_create_in_missing_board(self, client, tech):
        data = {"board_id": 999, "title": "x"}
        r = call(client, tech, "post", reverse("column_create"), data)
        assert_toast(r, tech, 404, "Quadro não encontrado.")

    def test_get_missing(self, client, tech):
        r = call(client, tech, "get", reverse("column_detail", args=[999]))
        assert_toast(r, tech, 404, "Coluna não encontrada.")

    def test_patch_missing(self, client, tech):
        r = call(
            client, tech, "patch", reverse("column_detail", args=[999]), {"order": 0}
        )
        assert_toast(r, tech, 404, "Coluna não encontrada.")

    def test_patch_empty(self, client, column, tech):
        r = call(client, tech, "patch", reverse("column_detail", args=[column.pk]), {})
        assert_toast(
            r, tech, 400, "Informe um título, uma cor ou a nova posição da coluna."
        )

    def test_delete_missing(self, client, tech):
        r = call(client, tech, "delete", reverse("column_detail", args=[999]))
        assert_toast(r, tech, 404, "Coluna não encontrada.")


@pytest.mark.parametrize("tech", ["templates", "components"])
class TestBoardErrors:
    def test_get_missing(self, client, tech):
        r = call(client, tech, "get", reverse("board_detail", args=[999]))
        assert_toast(r, tech, 404, "Quadro não encontrado.")

    def test_patch_missing(self, client, tech):
        r = call(
            client, tech, "patch", reverse("board_detail", args=[999]), {"title": "x"}
        )
        assert_toast(r, tech, 404, "Quadro não encontrado.")

    def test_patch_blank_title(self, client, board, tech):
        r = call(
            client,
            tech,
            "patch",
            reverse("board_detail", args=[board.pk]),
            {"title": ""},
        )
        assert_toast(r, tech, 400, "O título é obrigatório.")


@pytest.mark.parametrize("web_components", [True, False])
def test_toast_escapes_message(client, web_components):
    from kanban.utils import error_response

    request = client.get("/").wsgi_request
    request.web_components = web_components
    response = error_response(request, "<script>x</script>", 400)
    html = response.content.decode()
    assert "<script>x" not in html
    assert "&lt;script&gt;" in html
