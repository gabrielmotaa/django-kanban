import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import pytest
from playwright.sync_api import Page

from kanban.models import Board, Card, Column
from kanban.tests.parity import ParityBoardPage

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.integration]

TECHS = ["templates", "components"]


@pytest.fixture(autouse=True)
def board_data():
    board, _ = Board.objects.get_or_create(id=1, defaults={"title": "Main Board"})
    col_a = Column.objects.create(
        id=1, board=board, title="Column A", order=0, color="#64748b"
    )
    col_b = Column.objects.create(
        id=2, board=board, title="Column B", order=1, color="#ef4444"
    )
    Card.objects.create(id=1, column=col_a, title="Card 1", order=0)
    Card.objects.create(id=2, column=col_b, title="Card 2", order=0)


def snapshot_for(page: Page, live_server, tech: str, *, expanded: bool) -> str:
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()
    if expanded:
        board_page.open_column_menu("Column A")
        board_page.open_create_column_form()
    return board_page.aria_snapshot()


def test_aria_snapshot_parity_collapsed(live_server, page: Page):
    templates = snapshot_for(page, live_server, "templates", expanded=False)
    components = snapshot_for(page, live_server, "components", expanded=False)
    assert templates == components


def test_aria_snapshot_parity_expanded(live_server, page: Page):
    templates = snapshot_for(page, live_server, "templates", expanded=True)
    components = snapshot_for(page, live_server, "components", expanded=True)
    assert templates == components


@pytest.mark.parametrize("tech", TECHS)
def test_create_card_then_drag(live_server, page: Page, tech):
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()

    board_page.create_card("Column A", "Parity card")
    new_card = Card.objects.get(title="Parity card")
    assert new_card.column_id == 1

    board_page.drag_card_to_column("Parity card", "Column B")
    new_card.refresh_from_db()
    assert new_card.column_id == 2
    board_page.screenshot("create-card-then-drag")
