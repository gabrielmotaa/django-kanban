"""Card dialog and description (issue 007)."""

from urllib.parse import urlencode

import pytest
from django.test import Client
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from kanban.models import Board, Card, Column

pytestmark = pytest.mark.django_db

VARIANTS = ["templates", "components"]


def headers(tech: str) -> dict:
    return {"HTTP_X_WEB_COMPONENTS": "true"} if tech == "components" else {}


@pytest.fixture
def column() -> Column:
    board = Board.objects.create(id=1, title="Board")
    return Column.objects.create(board=board, title="Doing", order=0)


@pytest.fixture
def card(column) -> Card:
    return Card.objects.create(column=column, title="Write docs", order=0)


def patch(client, url, data, tech):
    return client.patch(
        url,
        urlencode(data),
        content_type="application/x-www-form-urlencoded",
        **headers(tech),
    )


def has_oob_card(html: str, card: Card, tech: str) -> bool:
    marker = "<kanban-card " if tech == "components" else "<div"
    start = html.find(f'id="card-{card.pk}"')
    return start != -1 and 'hx-swap-oob="true"' in html and marker in html


def test_description_defaults_to_empty(card):
    assert card.description == ""


@pytest.mark.parametrize("tech", VARIANTS)
class TestDialogGet:
    def test_renders_dialog(self, client: Client, card, tech):
        response = client.get(reverse("card_dialog", args=[card.pk]), **headers(tech))
        assert response.status_code == 200
        assertTemplateUsed(response, f"kanban/{tech}/_card_dialog.html")
        html = response.content.decode()
        assert "Write docs" in html
        assert "Doing" in html
        assert "Adicione uma descrição mais detalhada…" in html or "<kanban-" in html

    def test_shows_existing_description(self, client: Client, card, tech):
        card.description = "Line 1\nLine 2"
        card.save()
        html = client.get(
            reverse("card_dialog", args=[card.pk]), **headers(tech)
        ).content.decode()
        assert "Line 1\nLine 2" in html

    def test_missing_card(self, client: Client, tech):
        response = client.get(reverse("card_dialog", args=[999]), **headers(tech))
        assert response.status_code == 404
        assert "Card não encontrado." in response.content.decode()


@pytest.mark.parametrize("tech", VARIANTS)
class TestDescriptionPatch:
    def test_saves_and_returns_oob_card(self, client: Client, card, tech):
        url = reverse("card_description", args=[card.pk])
        response = patch(client, url, {"description": "Hello\nworld"}, tech)
        assert response.status_code == 200
        card.refresh_from_db()
        assert card.description == "Hello\nworld"
        html = response.content.decode()
        assert "Hello\nworld" in html
        assert has_oob_card(html, card, tech)

    def test_empty_clears(self, client: Client, card, tech):
        card.description = "old"
        card.save()
        url = reverse("card_description", args=[card.pk])
        response = patch(client, url, {"description": ""}, tech)
        assert response.status_code == 200
        card.refresh_from_db()
        assert card.description == ""
        assert has_oob_card(response.content.decode(), card, tech)

    def test_too_long(self, client: Client, card, tech):
        url = reverse("card_description", args=[card.pk])
        response = patch(client, url, {"description": "x" * 5001}, tech)
        assert response.status_code == 400
        assert "no máximo 5000 caracteres" in response.content.decode()
        card.refresh_from_db()
        assert card.description == ""

    def test_missing_card(self, client: Client, tech):
        url = reverse("card_description", args=[999])
        response = patch(client, url, {"description": "x"}, tech)
        assert response.status_code == 404
        assert "Card não encontrado." in response.content.decode()


@pytest.mark.parametrize("tech", VARIANTS)
def test_title_patch_returns_oob_card(client: Client, card, tech):
    url = reverse("card_detail", args=[card.pk])
    response = patch(client, url, {"title": "Renamed"}, tech)
    assert response.status_code == 200
    html = response.content.decode()
    assert "Renamed" in html
    assert has_oob_card(html, card, tech)


@pytest.mark.parametrize("tech", VARIANTS)
def test_card_front_flags_description(client: Client, card, tech):
    url = reverse("card_detail", args=[card.pk])
    html = client.get(url, **headers(tech)).content.decode()
    assert "Este card tem descrição" not in html
    assert "has-description" not in html

    card.description = "something"
    card.save()
    html = client.get(url, **headers(tech)).content.decode()
    if tech == "components":
        assert "has-description" in html
    else:
        assert "Este card tem descrição" in html


@pytest.mark.parametrize("tech", VARIANTS)
def test_card_front_links_to_dialog(client: Client, card, tech):
    html = client.get(
        reverse("card_detail", args=[card.pk]), **headers(tech)
    ).content.decode()
    assert reverse("card_dialog", args=[card.pk]) in html
