"""Due date and completion (issue 009)."""

import datetime as dt
from urllib.parse import urlencode

import pytest
from django.test import Client
from django.urls import reverse

from kanban.admin import CardAdmin
from kanban.forms import CardDueDateForm
from kanban.models import Board, Card, Column

pytestmark = pytest.mark.django_db

VARIANTS = ["templates", "components"]
TODAY = dt.date(2026, 10, 10)


@pytest.fixture(autouse=True)
def frozen_today(monkeypatch):
    monkeypatch.setattr("kanban.models.timezone.localdate", lambda: TODAY)


@pytest.fixture
def card() -> Card:
    board = Board.objects.create(id=1, title="Board")
    column = Column.objects.create(board=board, title="Doing", order=0)
    return Card.objects.create(column=column, title="Write docs", order=0)


def headers(tech: str) -> dict:
    return {"HTTP_X_WEB_COMPONENTS": "true"} if tech == "components" else {}


def patch(client, card, data, tech):
    return client.patch(
        reverse("card_due", args=[card.pk]),
        urlencode(data),
        content_type="application/x-www-form-urlencoded",
        **headers(tech),
    )


# -- model ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("due", "completed", "status"),
    [
        (None, False, None),
        (None, True, None),
        (TODAY - dt.timedelta(days=1), False, "overdue"),
        (TODAY, False, "soon"),
        (TODAY + dt.timedelta(days=1), False, "soon"),
        (TODAY + dt.timedelta(days=2), False, "ok"),
        (TODAY - dt.timedelta(days=30), True, "complete"),
        (TODAY + dt.timedelta(days=30), True, "complete"),
    ],
)
def test_due_status(card, due, completed, status):
    card.due_date = due
    card.completed = completed
    assert card.due_status == status


def test_due_labels(card):
    assert (card.due_label, card.due_chip) == ("", "")
    card.due_date = TODAY - dt.timedelta(days=1)
    assert (card.due_label, card.due_chip) == ("Atrasado", "Atrasado")
    card.due_date = TODAY
    assert (card.due_label, card.due_chip) == ("Vence em breve", "Vence em breve")
    card.due_date = TODAY + dt.timedelta(days=9)
    assert (card.due_label, card.due_chip) == ("Data de entrega", "")
    card.completed = True
    assert (card.due_label, card.due_chip) == ("Concluído", "")


def test_defaults(card):
    assert card.due_date is None
    assert card.completed is False


# -- form -----------------------------------------------------------------------


def test_form_accepts_date_and_completed():
    form = CardDueDateForm({"due_date": "2026-10-12", "completed": "true"})
    assert form.is_valid()
    assert form.cleaned_data["due_date"] == dt.date(2026, 10, 12)
    assert form.cleaned_data["completed"] is True


def test_form_empty_date_means_removal():
    form = CardDueDateForm({"due_date": "", "completed": "false"})
    assert form.is_valid()
    assert form.cleaned_data["due_date"] is None
    assert form.cleaned_data["completed"] is False


def test_form_rejects_invalid_date():
    form = CardDueDateForm({"due_date": "31/02/2026"})
    assert not form.is_valid()
    assert form.errors["due_date"] == ["Data inválida."]


# -- admin ----------------------------------------------------------------------


def test_admin_lists_and_filters_due_fields():
    assert "due_date" in CardAdmin.list_display
    assert "completed" in CardAdmin.list_display
    assert "due_date" in CardAdmin.list_filter
    assert "completed" in CardAdmin.list_filter


# -- view -----------------------------------------------------------------------


@pytest.mark.parametrize("tech", VARIANTS)
class TestDuePatch:
    def test_set_date(self, client: Client, card, tech):
        response = patch(
            client, card, {"due_date": "2026-10-12", "completed": "false"}, tech
        )
        assert response.status_code == 200
        card.refresh_from_db()
        assert card.due_date == dt.date(2026, 10, 12)
        assert card.completed is False
        html = response.content.decode()
        assert f'id="card-{card.pk}"' in html
        if tech == "components":
            assert "<kanban-card-due" in html
            assert 'value="2026-10-12"' in html
            assert 'display="12/10/2026"' in html
            assert 'due="12/10"' in html
        else:
            assert 'id="card-due"' in html
            assert "12/10/2026" in html
            assert 'hx-swap-oob="true"' in html
            assert "12/10" in html

    def test_complete(self, client: Client, card, tech):
        card.due_date = TODAY
        card.save()
        response = patch(
            client, card, {"due_date": "2026-10-10", "completed": "true"}, tech
        )
        assert response.status_code == 200
        card.refresh_from_db()
        assert card.completed is True
        html = response.content.decode()
        if tech == "components":
            assert 'completed="true"' in html
            assert 'due-status="complete"' in html
        else:
            assert "badge--complete" in html

    def test_clear_date_also_clears_completed(self, client: Client, card, tech):
        card.due_date = TODAY
        card.completed = True
        card.save()
        response = patch(client, card, {"due_date": "", "completed": "true"}, tech)
        assert response.status_code == 200
        card.refresh_from_db()
        assert card.due_date is None
        assert card.completed is False
        html = response.content.decode()
        if tech == "components":
            assert "due-status" not in html
            assert "due=" not in html
            assert " completed>" not in html
        else:
            assert "badge--" not in html

    def test_completed_without_date_is_not_stored(self, client: Client, card, tech):
        patch(client, card, {"due_date": "", "completed": "true"}, tech)
        card.refresh_from_db()
        assert card.completed is False

    def test_invalid_date(self, client: Client, card, tech):
        response = patch(client, card, {"due_date": "nope"}, tech)
        assert response.status_code == 400
        assert "Data inválida." in response.content.decode()
        card.refresh_from_db()
        assert card.due_date is None

    def test_missing_card(self, client: Client, tech):
        response = client.patch(
            reverse("card_due", args=[999]),
            urlencode({"due_date": "2026-10-12"}),
            content_type="application/x-www-form-urlencoded",
            **headers(tech),
        )
        assert response.status_code == 404
        assert "Card não encontrado." in response.content.decode()


# -- rendering ------------------------------------------------------------------


@pytest.mark.parametrize("tech", VARIANTS)
@pytest.mark.parametrize(
    ("offset", "completed", "status", "label"),
    [
        (-3, False, "overdue", "Atrasado"),
        (1, False, "soon", "Vence em breve"),
        (20, False, "ok", "Data de entrega"),
        (-3, True, "complete", "Concluído"),
    ],
)
def test_card_front_badge(client: Client, card, tech, offset, completed, status, label):
    card.due_date = TODAY + dt.timedelta(days=offset)
    card.completed = completed
    card.save()
    html = client.get(
        reverse("card_detail", args=[card.pk]), **headers(tech)
    ).content.decode()
    assert f'aria-label="{label}"' in html or f'due-label="{label}"' in html
    assert status in html
    assert card.due_date.strftime("%d/%m") in html


@pytest.mark.parametrize("tech", VARIANTS)
def test_card_front_without_date_has_no_badge(client: Client, card, tech):
    html = client.get(
        reverse("card_detail", args=[card.pk]), **headers(tech)
    ).content.decode()
    assert "badge--" not in html
    assert "due-status" not in html


@pytest.mark.parametrize("tech", VARIANTS)
def test_dialog_has_due_section(client: Client, card, tech):
    card.due_date = TODAY
    card.save()
    html = client.get(
        reverse("card_dialog", args=[card.pk]), **headers(tech)
    ).content.decode()
    if tech == "components":
        assert "<kanban-card-due" in html
    else:
        assert 'id="card-due"' in html
        assert "Data de entrega" in html
        assert "10/10/2026" in html


def test_fixture_has_due_dates():
    from django.core.management import call_command

    call_command("loaddata", "initial_data", verbosity=0)
    assert Card.objects.filter(due_date__isnull=False).exists()
