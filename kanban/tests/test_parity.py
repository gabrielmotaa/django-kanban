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


def snapshot_for(page: Page, live_server, tech: str, expand: str | None = None) -> str:
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()
    if expand == "column-menu":
        board_page.open_column_menu("Column A")
    elif expand == "create-column":
        board_page.open_create_column_form()
    elif expand == "rename-column":
        board_page.open_column_rename("Column A")
    elif expand == "edit-card":
        board_page.open_card_editor("Card 1")
    elif expand == "edit-board-title":
        board_page.open_board_title_editor()
    return board_page.aria_snapshot()


@pytest.mark.parametrize(
    "expand",
    [
        None,
        "column-menu",
        "create-column",
        "rename-column",
        "edit-card",
        "edit-board-title",
    ],
)
def test_aria_snapshot_parity(live_server, page: Page, expand):
    templates = snapshot_for(page, live_server, "templates", expand)
    components = snapshot_for(page, live_server, "components", expand)
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


@pytest.mark.parametrize("tech", TECHS)
def test_change_color_of_column_with_quotes_in_title(live_server, page: Page, tech):
    title = "Coluna \"aspas\" e 'apóstrofo'"
    Column.objects.filter(pk=1).update(title=title)
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()

    board_page.open_column_menu(title)
    board_page.column(title).get_by_role("button", name="Vermelho").click()

    for _ in range(30):
        column = Column.objects.get(pk=1)
        if column.color == "#ef4444":
            break
        page.wait_for_timeout(100)
    assert column.color == "#ef4444"
    assert column.title == title


def test_components_requests_carry_web_components_header(live_server, page: Page):
    seen: list[str | None] = []
    page.on(
        "request",
        lambda r: (
            seen.append(r.headers.get("x-web-components"))
            if r.method == "POST"
            else None
        ),
    )
    board_page = ParityBoardPage(page, live_server.url, "components")
    board_page.navigate()
    board_page.create_card("Column A", "Header card")
    assert seen == ["true"]


def test_components_drag_requests_carry_web_components_header(live_server, page: Page):
    seen: list[str | None] = []
    page.on(
        "request",
        lambda r: (
            seen.append(r.headers.get("x-web-components"))
            if r.method == "PATCH"
            else None
        ),
    )
    board_page = ParityBoardPage(page, live_server.url, "components")
    board_page.navigate()
    board_page.drag_card_to_column("Card 1", "Column B")
    assert seen == ["true"]
