"""Comments and activity (issue 011)."""

import datetime as dt
from urllib.parse import urlencode

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from kanban.activity import record_activity, render_message
from kanban.admin import ActivityAdmin, CommentAdmin
from kanban.forms import CommentForm
from kanban.models import (
    Activity,
    Board,
    Card,
    Checklist,
    ChecklistItem,
    Column,
    Comment,
    Label,
)

pytestmark = pytest.mark.django_db

VARIANTS = ["templates", "components"]


def headers(tech: str) -> dict:
    return {"HTTP_X_WEB_COMPONENTS": "true"} if tech == "components" else {}


@pytest.fixture
def board() -> Board:
    return Board.objects.create(id=1, title="Board")


@pytest.fixture
def todo(board) -> Column:
    return Column.objects.create(board=board, title="A fazer", order=0)


@pytest.fixture
def doing(board) -> Column:
    return Column.objects.create(board=board, title="Fazendo", order=1)


@pytest.fixture
def card(todo) -> Card:
    return Card.objects.create(column=todo, title="Write docs", order=0)


def patch(client, url, data, tech):
    return client.patch(
        url,
        urlencode(data),
        content_type="application/x-www-form-urlencoded",
        **headers(tech),
    )


def kinds(card) -> list[str]:
    return [a.kind for a in card.activities.order_by("pk")]


# -- record_activity and messages ------------------------------------------------

MESSAGES = [
    ("card_created", {"column": "A fazer"}, "Card criado em “A fazer”"),
    (
        "card_moved",
        {"from": "A fazer", "to": "Fazendo"},
        "Card movido de “A fazer” para “Fazendo”",
    ),
    ("title_renamed", {"old": "A", "new": "B"}, "Título alterado de “A” para “B”"),
    ("description_changed", {}, "Descrição alterada"),
    ("label_added", {"name": "Bug"}, "Etiqueta “Bug” adicionada"),
    ("label_removed", {"name": "Bug"}, "Etiqueta “Bug” removida"),
    ("due_set", {"date": "2026-10-12"}, "Data de entrega definida para 12/10/2026"),
    ("due_removed", {}, "Data de entrega removida"),
    ("due_completed", {}, "Data de entrega marcada como concluída"),
    (
        "checklist_item_completed",
        {"text": "Ship", "checklist": "Steps"},
        "Item “Ship” concluído em “Steps”",
    ),
]


@pytest.mark.parametrize(("kind", "data", "message"), MESSAGES)
def test_record_activity_and_message(card, kind, data, message):
    activity = record_activity(card, kind, **data)
    assert activity.pk
    assert (activity.card, activity.kind, activity.data) == (card, kind, data)
    assert activity.message == message
    assert render_message(kind, data) == message


def test_unknown_kind_is_rejected(card):
    with pytest.raises(ValueError):
        record_activity(card, "nope")


def test_timestamps_are_absolute_and_local(card):
    comment = Comment.objects.create(card=card, text="hi")
    Comment.objects.filter(pk=comment.pk).update(
        created_at=dt.datetime(2026, 10, 2, 14, 5, tzinfo=dt.UTC)
    )
    comment.refresh_from_db()
    assert comment.created_display == "02/10/2026 14:05"


def test_comment_defaults(card):
    comment = Comment.objects.create(card=card, text="hello")
    assert comment.created_at and comment.updated_at
    assert str(comment) == "hello"
    assert card.comment_count == 1
    assert card.comment_label == "1 comentário"
    Comment.objects.create(card=card, text="two")
    assert Card.objects.get(pk=card.pk).comment_label == "2 comentários"


def test_timeline_merges_newest_first(card):
    old = Comment.objects.create(card=card, text="old")
    activity = record_activity(card, "description_changed")
    new = Comment.objects.create(card=card, text="new")
    base = timezone.now()
    Comment.objects.filter(pk=old.pk).update(created_at=base - dt.timedelta(minutes=3))
    Activity.objects.filter(pk=activity.pk).update(
        created_at=base - dt.timedelta(minutes=2)
    )
    Comment.objects.filter(pk=new.pk).update(created_at=base - dt.timedelta(minutes=1))
    card = Card.objects.prefetch_related("comments", "activities").get(pk=card.pk)
    timeline = card.timeline()
    assert [(e["type"], e["obj"].pk) for e in timeline] == [
        ("comment", new.pk),
        ("activity", activity.pk),
        ("comment", old.pk),
    ]


# -- forms / admin ------------------------------------------------------------------


def test_comment_form_requires_text():
    form = CommentForm({"text": "   "})
    assert form.errors["text"] == ["O comentário é obrigatório."]
    assert CommentForm({"text": "ok"}).is_valid()


def test_comment_form_max_length():
    assert (
        "no máximo 5000 caracteres"
        in CommentForm({"text": "x" * 5001}).errors["text"][0]
    )


def test_admin_registered():
    assert CommentAdmin.list_display
    assert ActivityAdmin.list_display
    assert (
        ActivityAdmin(Activity, None).message_preview(
            Activity(kind="description_changed")
        )
        == "Descrição alterada"
    )


# -- activity produced by the existing views ----------------------------------------


@pytest.mark.parametrize("tech", VARIANTS)
class TestActivityFromViews:
    def test_card_created(self, client: Client, todo, tech):
        extra = headers(tech)
        client.post(
            reverse("card_create"), {"column_id": todo.pk, "title": "N"}, **extra
        )
        card = Card.objects.get(title="N")
        assert kinds(card) == ["card_created"]
        assert card.activities.get().data == {"column": "A fazer"}

    def test_move_between_columns(self, client: Client, card, doing, tech):
        patch(
            client,
            reverse("card_detail", args=[card.pk]),
            {"column_id": doing.pk, "order": 0},
            tech,
        )
        assert kinds(card) == ["card_moved"]
        assert card.activities.get().data == {"from": "A fazer", "to": "Fazendo"}

    def test_reorder_in_same_column_records_nothing(
        self, client: Client, card, todo, tech
    ):
        Card.objects.create(column=todo, title="Other", order=1)
        patch(
            client,
            reverse("card_detail", args=[card.pk]),
            {"column_id": todo.pk, "order": 1},
            tech,
        )
        assert kinds(card) == []

    def test_rename(self, client: Client, card, tech):
        response = patch(
            client, reverse("card_detail", args=[card.pk]), {"title": "New"}, tech
        )
        assert kinds(card) == ["title_renamed"]
        assert card.activities.get().data == {"old": "Write docs", "new": "New"}
        assert "Título alterado" in response.content.decode()

    def test_rename_to_same_title_records_nothing(self, client: Client, card, tech):
        patch(
            client,
            reverse("card_detail", args=[card.pk]),
            {"title": "Write docs"},
            tech,
        )
        assert kinds(card) == []

    def test_description(self, client: Client, card, tech):
        url = reverse("card_description", args=[card.pk])
        response = patch(client, url, {"description": "text"}, tech)
        assert kinds(card) == ["description_changed"]
        assert "Descrição alterada" in response.content.decode()
        patch(client, url, {"description": "text"}, tech)  # unchanged: nothing new
        assert kinds(card) == ["description_changed"]

    def test_labels(self, client: Client, card, board, tech):
        label = Label.objects.create(board=board, name="Bug", color="#ef4444")
        url = reverse("card_labels", args=[card.pk])
        extra = headers(tech)
        client.post(url, {"label_id": label.pk}, **extra)
        client.post(url, {"label_id": label.pk}, **extra)  # already attached
        client.delete(f"{url}?label_id={label.pk}", **extra)
        client.delete(f"{url}?label_id={label.pk}", **extra)  # already detached
        assert kinds(card) == ["label_added", "label_removed"]

    def test_due_date_events(self, client: Client, card, tech):
        url = reverse("card_due", args=[card.pk])
        patch(client, url, {"due_date": "2026-10-12", "completed": "false"}, tech)
        patch(client, url, {"due_date": "2026-10-12", "completed": "true"}, tech)
        patch(
            client, url, {"due_date": "2026-10-12", "completed": "false"}, tech
        )  # reopened: none
        patch(client, url, {"due_date": "", "completed": "false"}, tech)
        assert kinds(card) == ["due_set", "due_completed", "due_removed"]
        assert card.activities.first().data == {"date": "2026-10-12"}

    def test_checklist_item_completed(self, client: Client, card, tech):
        checklist = Checklist.objects.create(card=card, title="Steps", order=0)
        item = ChecklistItem.objects.create(checklist=checklist, text="Ship", order=0)
        url = reverse("checklist_item_detail", args=[item.pk])
        patch(client, url, {"done": "true"}, tech)
        patch(client, url, {"done": "false"}, tech)
        patch(client, url, {"text": "Ship it"}, tech)
        assert kinds(card) == ["checklist_item_completed"]
        assert card.activities.get().data == {"text": "Ship", "checklist": "Steps"}


# -- comments -------------------------------------------------------------------------


@pytest.mark.parametrize("tech", VARIANTS)
class TestComments:
    def test_create(self, client: Client, card, tech):
        response = client.post(
            reverse("card_comments", args=[card.pk]),
            {"text": "First!"},
            **headers(tech),
        )
        assert response.status_code == 200
        comment = card.comments.get()
        assert comment.text == "First!"
        html = response.content.decode()
        assert "First!" in html
        assert f'id="card-{card.pk}"' in html
        assert "Você" in html or tech == "components"

    @pytest.mark.parametrize("text", ["", "   "])
    def test_create_empty(self, client: Client, card, text, tech):
        response = client.post(
            reverse("card_comments", args=[card.pk]), {"text": text}, **headers(tech)
        )
        assert response.status_code == 400
        assert "O comentário é obrigatório." in response.content.decode()
        assert not card.comments.exists()

    def test_create_missing_card(self, client: Client, tech):
        response = client.post(
            reverse("card_comments", args=[999]), {"text": "x"}, **headers(tech)
        )
        assert response.status_code == 404
        assert "Card não encontrado." in response.content.decode()

    def test_edit(self, client: Client, card, tech):
        comment = Comment.objects.create(card=card, text="old")
        response = patch(
            client, reverse("comment_detail", args=[comment.pk]), {"text": "new"}, tech
        )
        assert response.status_code == 200
        comment.refresh_from_db()
        assert comment.text == "new"
        assert "new" in response.content.decode()

    def test_edit_empty(self, client: Client, card, tech):
        comment = Comment.objects.create(card=card, text="old")
        response = patch(
            client, reverse("comment_detail", args=[comment.pk]), {"text": ""}, tech
        )
        assert response.status_code == 400
        comment.refresh_from_db()
        assert comment.text == "old"

    def test_edit_missing(self, client: Client, tech):
        response = patch(
            client, reverse("comment_detail", args=[999]), {"text": "x"}, tech
        )
        assert response.status_code == 404
        assert "Comentário não encontrado." in response.content.decode()

    def test_delete(self, client: Client, card, tech):
        comment = Comment.objects.create(card=card, text="bye")
        response = client.delete(
            reverse("comment_detail", args=[comment.pk]), **headers(tech)
        )
        assert response.status_code == 200
        assert not Comment.objects.exists()
        assert f'id="card-{card.pk}"' in response.content.decode()

    def test_delete_missing(self, client: Client, tech):
        response = client.delete(reverse("comment_detail", args=[999]), **headers(tech))
        assert response.status_code == 404


# -- rendering --------------------------------------------------------------------------


@pytest.mark.parametrize("tech", VARIANTS)
def test_card_front_comment_badge(client: Client, card, tech):
    url = reverse("card_detail", args=[card.pk])
    html = client.get(url, **headers(tech)).content.decode()
    assert "comentário" not in html
    Comment.objects.create(card=card, text="a")
    Comment.objects.create(card=card, text="b")
    html = client.get(url, **headers(tech)).content.decode()
    assert "2 comentários" in html
    assert ("💬 2" in html) if tech == "templates" else ('comments="2"' in html)


@pytest.mark.parametrize("tech", VARIANTS)
def test_dialog_shows_timeline_newest_first(client: Client, card, tech):
    record_activity(card, "description_changed")
    Comment.objects.create(card=card, text="a comment")
    html = client.get(
        reverse("card_dialog", args=[card.pk]), **headers(tech)
    ).content.decode()
    assert "Comentários e atividade" in html or "<kanban-card-activity" in html
    assert html.index("a comment") < html.index("Descrição alterada")
    if tech == "templates":
        assert "Escrever um comentário…" in html
        assert "Mostrar detalhes" in html and "Ocultar detalhes" in html
        assert "Você" in html
    else:
        assert "<kanban-card-activity" in html
        assert "<kanban-comment " in html
        assert "<kanban-activity-entry " in html


@pytest.mark.parametrize("tech", VARIANTS)
def test_mutations_return_the_new_activity_entry(client: Client, card, tech):
    response = patch(
        client, reverse("card_description", args=[card.pk]), {"description": "x"}, tech
    )
    html = response.content.decode()
    if tech == "templates":
        assert 'hx-swap-oob="afterbegin:#card-timeline"' in html
    else:
        assert "<kanban-activity-entry" in html
    assert "Descrição alterada" in html
