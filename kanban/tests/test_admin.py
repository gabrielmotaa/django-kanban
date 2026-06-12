import pytest
from django.contrib.admin.sites import AdminSite

from kanban.admin import CardAdmin, ColumnAdmin
from kanban.models import Board, Card, Column

pytestmark = pytest.mark.django_db


def test_column_admin_board_link():
    site = AdminSite()
    admin_instance = ColumnAdmin(Column, site)

    board = Board.objects.create(title="Test Board")
    column = Column.objects.create(board=board, title="Test Column", order=0)

    link = admin_instance.board_link(column)
    assert f"/admin/kanban/board/{board.pk}/change/" in link
    assert "Test Board" in link


def test_column_admin_color_preview():
    site = AdminSite()
    admin_instance = ColumnAdmin(Column, site)

    board = Board.objects.create(title="Test Board")
    column = Column.objects.create(
        board=board, title="Test Column", order=0, color="#10b981"
    )

    preview = admin_instance.color_preview(column)
    assert "#10b981" in preview


def test_card_admin_column_link():
    site = AdminSite()
    admin_instance = CardAdmin(Card, site)

    board = Board.objects.create(title="Test Board")
    column = Column.objects.create(board=board, title="Test Column", order=0)
    card = Card.objects.create(column=column, title="Test Card", order=0)

    link = admin_instance.column_link(card)
    assert f"/admin/kanban/column/{column.pk}/change/" in link
    assert "Test Column" in link


def test_card_admin_board_link():
    site = AdminSite()
    admin_instance = CardAdmin(Card, site)

    board = Board.objects.create(title="Test Board")
    column = Column.objects.create(board=board, title="Test Column", order=0)
    card = Card.objects.create(column=column, title="Test Card", order=0)

    link = admin_instance.board_link(card)
    assert f"/admin/kanban/board/{board.pk}/change/" in link
    assert "Test Board" in link
