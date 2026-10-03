"""Checklists (issue 010): models, forms, admin, views and card-front counts."""

import re
from urllib.parse import urlencode

import pytest
from django.contrib.admin.sites import AdminSite
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from kanban.admin import CardAdmin, ChecklistAdmin
from kanban.forms import ChecklistItemCreateForm, ChecklistItemEditForm
from kanban.models import Board, Card, Checklist, ChecklistItem, Column

pytestmark = pytest.mark.django_db

VARIANTS = ["templates", "components"]


def headers(tech: str) -> dict:
    return {"HTTP_X_WEB_COMPONENTS": "true"} if tech == "components" else {}


@pytest.fixture
def card() -> Card:
    board = Board.objects.create(id=1, title="Board")
    column = Column.objects.create(board=board, title="Doing", order=0)
    return Card.objects.create(column=column, title="Write docs", order=0)


@pytest.fixture
def checklist(card) -> Checklist:
    return Checklist.objects.create(card=card, title="Steps", order=0)


@pytest.fixture
def item(checklist) -> ChecklistItem:
    return ChecklistItem.objects.create(checklist=checklist, text="First", order=0)


def send(client, tech, method, url, data=None):
    extra = headers(tech)
    if method == "post":
        return client.post(url, data or {}, **extra)
    if method == "delete":
        return client.delete(url, **extra)
    return client.patch(
        url,
        urlencode(data or {}),
        content_type="application/x-www-form-urlencoded",
        **extra,
    )


# -- models ----------------------------------------------------------------------


def test_checklist_defaults_and_ordering(card):
    first = Checklist.objects.create(card=card)
    assert first.title == "Checklist"
    second = Checklist.objects.create(card=card, title="B", order=1)
    third = Checklist.objects.create(card=card, title="A", order=1)
    assert list(card.checklists.all()) == [first, second, third]
    assert str(second) == "B"


def test_item_defaults_and_ordering(checklist):
    a = ChecklistItem.objects.create(checklist=checklist, text="a", order=1)
    b = ChecklistItem.objects.create(checklist=checklist, text="b", order=0)
    assert a.done is False
    assert list(checklist.items.all()) == [b, a]
    assert str(a) == "a"


def test_progress_numbers(checklist):
    assert (checklist.done_count, checklist.total_count, checklist.percent) == (0, 0, 0)
    for i, done in enumerate([True, True, False]):
        ChecklistItem.objects.create(
            checklist=checklist, text=str(i), done=done, order=i
        )
    checklist = Checklist.objects.prefetch_related("items").get(pk=checklist.pk)
    assert (checklist.done_count, checklist.total_count) == (2, 3)
    assert checklist.percent == 67


@pytest.mark.parametrize(
    ("done", "total", "percent"), [(1, 8, 13), (1, 2, 50), (0, 3, 0), (3, 3, 100)]
)
def test_percent_rounds_half_up(checklist, done, total, percent):
    for i in range(total):
        ChecklistItem.objects.create(
            checklist=checklist, text=str(i), done=i < done, order=i
        )
    assert Checklist.objects.get(pk=checklist.pk).percent == percent


def test_card_totals_sum_all_checklists(card, checklist):
    other = Checklist.objects.create(card=card, title="Other", order=1)
    ChecklistItem.objects.create(checklist=checklist, text="a", done=True, order=0)
    ChecklistItem.objects.create(checklist=checklist, text="b", order=1)
    ChecklistItem.objects.create(checklist=other, text="c", done=True, order=0)
    card = Card.objects.prefetch_related("checklists__items").get(pk=card.pk)
    assert (card.checklist_done, card.checklist_total) == (2, 3)
    assert card.checklist_label == "Checklist 2 de 3"


def test_card_without_checklists_has_no_totals(card):
    assert (card.checklist_done, card.checklist_total) == (0, 0)
    assert card.checklist_label == ""


def test_deleting_card_cascades(card, checklist, item):
    card.delete()
    assert not Checklist.objects.exists()
    assert not ChecklistItem.objects.exists()


# -- forms ----------------------------------------------------------------------


def test_item_create_form_requires_text():
    form = ChecklistItemCreateForm({"text": "  "})
    assert not form.is_valid()
    assert form.errors["text"] == ["O texto do item é obrigatório."]


def test_item_create_form_max_length():
    form = ChecklistItemCreateForm({"text": "x" * 201})
    assert "no máximo 200 caracteres" in form.errors["text"][0]


def test_item_edit_form_done_is_tri_state():
    def cleaned(data):
        form = ChecklistItemEditForm(data)
        assert form.is_valid(), form.errors
        return form.cleaned_data

    assert cleaned({"done": "true"})["done"] is True
    assert cleaned({"done": "false"})["done"] is False
    assert cleaned({"text": "x"})["done"] is None


def test_item_edit_form_needs_something_to_change():
    assert not ChecklistItemEditForm({}).is_valid()


# -- admin ----------------------------------------------------------------------


def test_admin_registered_with_inlines():
    admin_instance = ChecklistAdmin(Checklist, AdminSite())
    assert [inline.model for inline in admin_instance.inlines] == [ChecklistItem]
    assert any(inline.model is Checklist for inline in CardAdmin.inlines)


# -- checklist views ------------------------------------------------------------


@pytest.mark.parametrize("tech", VARIANTS)
class TestChecklistViews:
    def test_create_with_default_title(self, client: Client, card, tech):
        url = reverse("card_checklists", args=[card.pk])
        response = send(client, tech, "post", url, {})
        assert response.status_code == 200
        created = card.checklists.get()
        assert (created.title, created.order) == ("Checklist", 0)
        html = response.content.decode()
        assert f'id="card-{card.pk}"' in html
        assert (
            ("<kanban-checklist " in html)
            if tech == "components"
            else (f'id="checklist-{created.pk}"' in html)
        )

    def test_create_with_title_and_order(self, client: Client, card, checklist, tech):
        url = reverse("card_checklists", args=[card.pk])
        send(client, tech, "post", url, {"title": "Second"})
        assert [c.title for c in card.checklists.all()] == ["Steps", "Second"]

    def test_create_title_too_long(self, client: Client, card, tech):
        url = reverse("card_checklists", args=[card.pk])
        response = send(client, tech, "post", url, {"title": "x" * 101})
        assert response.status_code == 400
        assert "no máximo 100 caracteres" in response.content.decode()

    def test_create_missing_card(self, client: Client, tech):
        response = send(client, tech, "post", reverse("card_checklists", args=[999]))
        assert response.status_code == 404
        assert "Card não encontrado." in response.content.decode()

    def test_rename(self, client: Client, checklist, tech):
        url = reverse("checklist_detail", args=[checklist.pk])
        response = send(client, tech, "patch", url, {"title": "Renamed"})
        assert response.status_code == 200
        checklist.refresh_from_db()
        assert checklist.title == "Renamed"
        assert "Renamed" in response.content.decode()

    def test_rename_blank_rejected(self, client: Client, checklist, tech):
        url = reverse("checklist_detail", args=[checklist.pk])
        response = send(client, tech, "patch", url, {"title": " "})
        assert response.status_code == 400
        assert "O título é obrigatório." in response.content.decode()

    def test_rename_missing(self, client: Client, tech):
        response = send(
            client,
            tech,
            "patch",
            reverse("checklist_detail", args=[999]),
            {"title": "x"},
        )
        assert response.status_code == 404
        assert "Checklist não encontrado." in response.content.decode()

    def test_delete_returns_card_front(
        self, client: Client, card, checklist, item, tech
    ):
        response = send(
            client, tech, "delete", reverse("checklist_detail", args=[checklist.pk])
        )
        assert response.status_code == 200
        assert not Checklist.objects.exists()
        assert not ChecklistItem.objects.exists()
        assert f'id="card-{card.pk}"' in response.content.decode()

    def test_delete_missing(self, client: Client, tech):
        response = send(client, tech, "delete", reverse("checklist_detail", args=[999]))
        assert response.status_code == 404


# -- item views -----------------------------------------------------------------


@pytest.mark.parametrize("tech", VARIANTS)
class TestItemViews:
    def test_add_item(self, client: Client, card, checklist, tech):
        url = reverse("checklist_items", args=[checklist.pk])
        response = send(client, tech, "post", url, {"text": "Do it"})
        assert response.status_code == 200
        created = checklist.items.get()
        assert (created.text, created.done, created.order) == ("Do it", False, 0)
        html = response.content.decode()
        assert "Do it" in html
        assert f'id="card-{card.pk}"' in html
        if tech == "templates":
            assert f'id="checklist-progress-{checklist.pk}"' in html
            assert "0%" in html

    def test_add_item_orders_after_existing(
        self, client: Client, checklist, item, tech
    ):
        url = reverse("checklist_items", args=[checklist.pk])
        send(client, tech, "post", url, {"text": "Second"})
        assert [i.text for i in checklist.items.all()] == ["First", "Second"]

    def test_add_item_after_deletions_goes_last(self, client: Client, checklist, tech):
        for position, text in enumerate("ABC"):
            ChecklistItem.objects.create(checklist=checklist, text=text, order=position)
        checklist.items.filter(text__in=["A", "B"]).delete()
        url = reverse("checklist_items", args=[checklist.pk])
        send(client, tech, "post", url, {"text": "D"})
        assert [i.text for i in checklist.items.all()] == ["C", "D"]

    def test_checklist_after_deletions_goes_last(self, client: Client, card, tech):
        first = Checklist.objects.create(card=card, title="A", order=0)
        Checklist.objects.create(card=card, title="B", order=1)
        first.delete()
        send(
            client,
            tech,
            "post",
            reverse("card_checklists", args=[card.pk]),
            {"title": "C"},
        )
        assert [c.title for c in card.checklists.all()] == ["B", "C"]

    @pytest.mark.parametrize("text", ["", "   "])
    def test_add_item_empty(self, client: Client, checklist, text, tech):
        url = reverse("checklist_items", args=[checklist.pk])
        response = send(client, tech, "post", url, {"text": text})
        assert response.status_code == 400
        assert "O texto do item é obrigatório." in response.content.decode()
        assert not checklist.items.exists()

    def test_add_item_too_long(self, client: Client, checklist, tech):
        url = reverse("checklist_items", args=[checklist.pk])
        response = send(client, tech, "post", url, {"text": "x" * 201})
        assert response.status_code == 400
        assert "no máximo 200 caracteres" in response.content.decode()

    def test_add_item_to_deleted_checklist(self, client: Client, tech):
        response = send(
            client, tech, "post", reverse("checklist_items", args=[999]), {"text": "x"}
        )
        assert response.status_code == 404
        assert "Checklist não encontrado." in response.content.decode()

    def test_toggle_done_updates_progress(
        self, client: Client, card, checklist, item, tech
    ):
        other = ChecklistItem.objects.create(
            checklist=checklist, text="Second", order=1
        )
        url = reverse("checklist_item_detail", args=[item.pk])
        response = send(client, tech, "patch", url, {"done": "true"})
        assert response.status_code == 200
        item.refresh_from_db()
        assert item.done is True
        assert other.done is False
        html = response.content.decode()
        if tech == "templates":
            assert "50%" in html
        else:
            assert 'done="true"' in html
        assert f'id="card-{card.pk}"' in html
        if tech == "templates":
            assert "1/2" in html
        else:
            assert 'checklist-done="1" checklist-total="2"' in html

    def test_untoggle(self, client: Client, item, tech):
        item.done = True
        item.save()
        url = reverse("checklist_item_detail", args=[item.pk])
        send(client, tech, "patch", url, {"done": "false"})
        item.refresh_from_db()
        assert item.done is False

    def test_edit_text_keeps_done(self, client: Client, item, tech):
        item.done = True
        item.save()
        url = reverse("checklist_item_detail", args=[item.pk])
        response = send(client, tech, "patch", url, {"text": "Changed"})
        assert response.status_code == 200
        item.refresh_from_db()
        assert (item.text, item.done) == ("Changed", True)

    def test_edit_text_blank_rejected(self, client: Client, item, tech):
        url = reverse("checklist_item_detail", args=[item.pk])
        response = send(client, tech, "patch", url, {"text": " "})
        assert response.status_code == 400
        assert "O texto do item é obrigatório." in response.content.decode()
        item.refresh_from_db()
        assert item.text == "First"

    def test_patch_without_fields_rejected(self, client: Client, item, tech):
        url = reverse("checklist_item_detail", args=[item.pk])
        response = send(client, tech, "patch", url, {})
        assert response.status_code == 400

    def test_patch_missing_item(self, client: Client, tech):
        response = send(
            client,
            tech,
            "patch",
            reverse("checklist_item_detail", args=[999]),
            {"done": "true"},
        )
        assert response.status_code == 404
        assert "Item não encontrado." in response.content.decode()

    def test_delete_item(self, client: Client, card, checklist, item, tech):
        response = send(
            client, tech, "delete", reverse("checklist_item_detail", args=[item.pk])
        )
        assert response.status_code == 200
        assert not ChecklistItem.objects.exists()
        assert f'id="card-{card.pk}"' in response.content.decode()

    def test_delete_missing_item(self, client: Client, tech):
        response = send(
            client, tech, "delete", reverse("checklist_item_detail", args=[999])
        )
        assert response.status_code == 404


# -- rendering ------------------------------------------------------------------


def filled(card):
    checklist = Checklist.objects.create(card=card, title="Steps", order=0)
    for i, done in enumerate([True, True, False]):
        ChecklistItem.objects.create(
            checklist=checklist, text=f"Item {i}", done=done, order=i
        )
    return checklist


@pytest.mark.parametrize("tech", VARIANTS)
def test_card_front_badge(client: Client, card, tech):
    html = client.get(
        reverse("card_detail", args=[card.pk]), **headers(tech)
    ).content.decode()
    assert "2/3" not in html
    assert "checklist-total" not in html
    filled(card)
    html = client.get(
        reverse("card_detail", args=[card.pk]), **headers(tech)
    ).content.decode()
    assert "Checklist 2 de 3" in html
    if tech == "templates":
        assert "2/3" in html
    else:
        assert 'checklist-done="2" checklist-total="3"' in html


@pytest.mark.parametrize("tech", VARIANTS)
def test_card_front_badge_is_complete_when_all_done(client: Client, card, tech):
    checklist = Checklist.objects.create(card=card, title="C", order=0)
    ChecklistItem.objects.create(checklist=checklist, text="a", done=True, order=0)
    html = client.get(
        reverse("card_detail", args=[card.pk]), **headers(tech)
    ).content.decode()
    assert (
        ("badge--complete" in html)
        if tech == "templates"
        else ('checklist-status="complete"' in html)
    )


@pytest.mark.parametrize("tech", VARIANTS)
def test_empty_checklists_show_no_badge(client: Client, card, checklist, tech):
    html = client.get(
        reverse("card_detail", args=[card.pk]), **headers(tech)
    ).content.decode()
    assert "Checklist 0" not in html
    assert "checklist-total" not in html


@pytest.mark.parametrize("tech", VARIANTS)
def test_dialog_lists_checklists_and_items(client: Client, card, tech):
    checklist = filled(card)
    html = client.get(
        reverse("card_dialog", args=[card.pk]), **headers(tech)
    ).content.decode()
    assert "Steps" in html
    assert "Item 0" in html
    if tech == "templates":
        assert f'id="checklist-{checklist.pk}"' in html
        assert "67%" in html
        assert 'id="card-checklists"' in html
    else:
        assert "<kanban-checklist " in html
        assert html.count("<kanban-checklist-item ") == 3
        assert "checklists-url=" in html


@pytest.mark.parametrize("tech", VARIANTS)
def test_board_page_query_count_is_flat(client: Client, card, tech):
    Board.objects.get(pk=1)

    def count() -> int:
        with CaptureQueriesContext(connection) as ctx:
            assert client.get(reverse("index", args=[tech])).status_code == 200
        return len(ctx)

    filled(card)
    baseline = count()
    for n in range(5):
        extra = Card.objects.create(column=card.column, title=f"c{n}", order=n + 1)
        filled(extra)
    assert count() == baseline


def test_percent_in_html_is_integer(client: Client, card):
    filled(card)
    html = client.get(reverse("card_dialog", args=[card.pk])).content.decode()
    assert re.search(r"\b67%", html)
