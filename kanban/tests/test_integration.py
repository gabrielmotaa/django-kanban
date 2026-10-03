import os
import time

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import pytest
from playwright.sync_api import Page

from kanban.models import Board, Card, Column

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.integration]


@pytest.fixture(autouse=True)
def setup_board():
    # Board with pk=1 is required by kanban views.py
    board, _ = Board.objects.get_or_create(id=1, defaults={"title": "Main Board"})
    col_a = Column.objects.create(
        id=1, board=board, title="Column A", order=0, color="#64748b"
    )
    col_b = Column.objects.create(
        id=2, board=board, title="Column B", order=1, color="#ef4444"
    )
    card_1 = Card.objects.create(id=1, column=col_a, title="Card 1", order=0)
    card_2 = Card.objects.create(id=2, column=col_b, title="Card 2", order=0)
    return board, col_a, col_b, card_1, card_2


# Retry-based database assertions to prevent race conditions
def assert_card_column(card_id: int, expected_col_id: int, timeout: float = 3.0):
    start = time.time()
    while time.time() - start < timeout:
        card = Card.objects.get(pk=card_id)
        if card.column_id == expected_col_id:
            return
        time.sleep(0.1)
    card = Card.objects.get(pk=card_id)
    assert card.column_id == expected_col_id


def assert_column_order(col_id: int, expected_order: int, timeout: float = 3.0):
    start = time.time()
    while time.time() - start < timeout:
        col = Column.objects.get(pk=col_id)
        if col.order == expected_order:
            return
        time.sleep(0.1)
    col = Column.objects.get(pk=col_id)
    assert col.order == expected_order


def assert_card_deleted(card_id: int, timeout: float = 3.0):
    start = time.time()
    while time.time() - start < timeout:
        if not Card.objects.filter(pk=card_id).exists():
            return
        time.sleep(0.1)
    assert not Card.objects.filter(pk=card_id).exists()


def assert_column_deleted(col_id: int, timeout: float = 3.0):
    start = time.time()
    while time.time() - start < timeout:
        if not Column.objects.filter(pk=col_id).exists():
            return
        time.sleep(0.1)
    assert not Column.objects.filter(pk=col_id).exists()


class BoardPage:
    def __init__(self, page: Page, live_server_url: str, tech: str):
        self.page = page
        self.tech = tech
        self.url = f"{live_server_url}/{tech}/"
        # Enable console logging for debugging
        self.page.on(
            "console",
            lambda msg: print(f"BROWSER CONSOLE [{self.tech}]: {msg.type}: {msg.text}"),
        )

    def navigate(self):
        self.page.goto(self.url)
        if self.tech == "templates":
            self.page.wait_for_selector(".board-wrapper")
        else:
            self.page.wait_for_selector("kanban-board")
        self.page.wait_for_timeout(300)

    def col_locator(self, col_id: int):
        if self.tech == "templates":
            return self.page.locator(f'[data-column-id="{col_id}"]')
        else:
            return self.page.locator(f'kanban-column[column-id="{col_id}"]')

    def col_header_locator(self, col_id: int):
        if self.tech == "templates":
            return self.page.locator(f'[data-column-id="{col_id}"] .column__title-text')
        else:
            return self.page.locator(f'kanban-column[column-id="{col_id}"] .title-text')

    def card_locator(self, card_id: int):
        if self.tech == "templates":
            return self.page.locator(f'[data-card-id="{card_id}"]')
        else:
            return self.page.locator(f'kanban-card[card-id="{card_id}"]')

    def drag_card_to_column(self, card_id: int, target_col_id: int):
        card = self.card_locator(card_id)
        column = self.col_locator(target_col_id)

        # Robust HTML5 drag-and-drop sequence
        card.hover()
        self.page.mouse.down()
        column.hover()
        box = column.bounding_box()
        if box:
            self.page.mouse.move(
                box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=5
            )
        self.page.mouse.up()
        self.page.wait_for_timeout(500)

    def drag_column_to_column(self, col_id: int, target_col_id: int):
        col = self.col_locator(col_id)
        target_col = self.col_locator(target_col_id)

        # Drag from header center of source to header center of target
        col.drag_to(
            target_col,
            source_position={"x": 140, "y": 20},
            target_position={"x": 140, "y": 20},
        )
        self.page.wait_for_timeout(500)

    def edit_column_title(self, col_id: int, new_title: str):
        col = self.col_locator(col_id)
        if self.tech == "templates":
            col.locator(".column__menu-trigger").click()
            col.locator('.column__menu-btn:has-text("Editar nome")').click()
            input_el = col.locator(".column__edit-input")
            input_el.fill(new_title)
            col.locator(".column__edit-btn-save").click()
        else:
            col.locator(".menu-trigger").click()
            col.locator('.menu-btn:has-text("Editar nome")').click()
            input_el = col.locator(".edit-input")
            input_el.fill(new_title)
            col.locator(".edit-btn-save").click()
        self.page.wait_for_timeout(500)

    def delete_column(self, col_id: int):
        col = self.col_locator(col_id)
        self.page.once("dialog", lambda dialog: dialog.accept())
        if self.tech == "templates":
            col.locator(".column__menu-trigger").click()
            col.locator('.column__menu-btn--danger:has-text("Apagar coluna")').click()
        else:
            col.locator(".menu-trigger").click()
            col.locator('.menu-btn--danger:has-text("Apagar coluna")').click()
        self.page.wait_for_timeout(500)

    def create_column(self, title: str):
        if self.tech == "templates":
            self.page.locator(".column-create__trigger").click()
            self.page.locator(".column-create__input").fill(title)
            self.page.locator(".column-create__btn-submit").click()
        else:
            self.page.locator("kanban-board .trigger").click()
            self.page.locator("kanban-board .input").fill(title)
            self.page.locator("kanban-board .btn-submit").click()
        self.page.wait_for_timeout(500)

    def create_card(self, col_id: int, title: str):
        col = self.col_locator(col_id)
        if self.tech == "templates":
            col.locator(".column__add-card-trigger").click()
            col.locator(".column__add-card-input").fill(title)
            col.locator(".column__add-card-submit").click()
        else:
            col.locator(".add-card-trigger").click()
            col.locator(".add-card-input").fill(title)
            col.locator(".add-card-submit").click()
        self.page.wait_for_timeout(500)

    def edit_card_title(self, card_id: int, new_title: str):
        self.card_locator(card_id).click()
        dialog = self.page.get_by_role("dialog")
        dialog.get_by_role("heading", level=2).get_by_role("button").click()
        dialog.get_by_role("textbox", name="Título do card").fill(new_title)
        dialog.get_by_role("button", name="Salvar").click()
        dialog.get_by_role("heading", level=2, name=new_title).wait_for()
        dialog.get_by_role("button", name="Fechar").click()
        dialog.wait_for(state="hidden")

    def delete_card(self, card_id: int):
        self.card_locator(card_id).click()
        dialog = self.page.get_by_role("dialog")
        self.page.once("dialog", lambda d: d.accept())
        dialog.get_by_role("button", name="Excluir card").click()
        dialog.wait_for(state="hidden")


@pytest.mark.parametrize("tech", ["templates", "components"])
def test_drag_card(live_server, page: Page, tech):
    board_page = BoardPage(page, live_server.url, tech)
    board_page.navigate()

    # Move Card 1 (starts in col_a = id 1) to col_b = id 2
    board_page.drag_card_to_column(1, 2)
    assert_card_column(1, 2)

    # Move Card 1 back to col_a = id 1
    board_page.drag_card_to_column(1, 1)
    assert_card_column(1, 1)


@pytest.mark.parametrize("tech", ["templates", "components"])
def test_create_card_then_drag(live_server, page: Page, tech):
    board_page = BoardPage(page, live_server.url, tech)
    board_page.navigate()

    # Create a new card in col_a (id 1)
    board_page.create_card(1, "New Card")

    # Assert DB
    new_card = Card.objects.get(title="New Card")
    assert new_card.column_id == 1

    # Check that drag-and-drop still works for the new card
    board_page.drag_card_to_column(new_card.pk, 2)
    assert_card_column(new_card.pk, 2)

    # Check that drag-and-drop still works for the original card
    board_page.drag_card_to_column(1, 2)
    assert_card_column(1, 2)


@pytest.mark.parametrize("tech", ["templates", "components"])
def test_edit_card_then_drag(live_server, page: Page, tech):
    board_page = BoardPage(page, live_server.url, tech)
    board_page.navigate()

    # Edit Card 1 title
    board_page.edit_card_title(1, "Edited Card Title")
    card_1 = Card.objects.get(pk=1)
    assert card_1.title == "Edited Card Title"

    # Verify drag still works for the edited card
    board_page.drag_card_to_column(1, 2)
    assert_card_column(1, 2)


@pytest.mark.parametrize("tech", ["templates", "components"])
def test_delete_card_then_drag(live_server, page: Page, tech):
    board_page = BoardPage(page, live_server.url, tech)
    board_page.navigate()

    # Delete Card 1
    board_page.delete_card(1)
    assert_card_deleted(1)

    # Verify drag still works for Card 2 (starts in col_b = id 2)
    board_page.drag_card_to_column(2, 1)
    assert_card_column(2, 1)


@pytest.mark.parametrize("tech", ["templates", "components"])
def test_drag_column(live_server, page: Page, tech):
    board_page = BoardPage(page, live_server.url, tech)
    board_page.navigate()

    # Move Column A (starts at order 0) to Column B (order 1)
    board_page.drag_column_to_column(1, 2)
    assert_column_order(1, 1)
    assert_column_order(2, 0)

    # Move Column A back
    board_page.drag_column_to_column(2, 1)
    assert_column_order(1, 0)
    assert_column_order(2, 1)


@pytest.mark.parametrize("tech", ["templates", "components"])
def test_create_column_then_drag(live_server, page: Page, tech):
    board_page = BoardPage(page, live_server.url, tech)
    board_page.navigate()

    # Create new column
    board_page.create_column("New Column")
    new_col = Column.objects.get(title="New Column")
    assert new_col.order == 2

    # Verify drag works by dragging col_a (id 1) to new_col
    board_page.drag_column_to_column(1, new_col.pk)
    assert_column_order(1, 2)

    # Verify card drag still works
    board_page.drag_card_to_column(1, new_col.pk)
    assert_card_column(1, new_col.pk)


@pytest.mark.parametrize("tech", ["templates", "components"])
def test_edit_column_then_drag(live_server, page: Page, tech):
    board_page = BoardPage(page, live_server.url, tech)
    board_page.navigate()

    # Edit Column A title
    board_page.edit_column_title(1, "Renamed Column A")
    col_a = Column.objects.get(pk=1)
    assert col_a.title == "Renamed Column A"

    # Verify drag column still works
    board_page.drag_column_to_column(1, 2)
    assert_column_order(1, 1)
    assert_column_order(2, 0)

    # Verify drag card still works
    board_page.drag_card_to_column(1, 2)
    assert_card_column(1, 2)


@pytest.mark.parametrize("tech", ["templates", "components"])
def test_delete_column_then_drag(live_server, page: Page, tech):
    board_page = BoardPage(page, live_server.url, tech)
    board_page.navigate()

    # Delete Column A (id 1)
    board_page.delete_column(1)
    assert_column_deleted(1)
    assert_card_deleted(1)

    # Create a new column C so we have at least 2 columns to test dragging
    board_page.create_column("Column C")
    col_c = Column.objects.get(title="Column C")

    # Verify column drag works with Column B and Column C
    board_page.drag_column_to_column(2, col_c.pk)
    assert_column_order(2, 1)
    assert_column_order(col_c.pk, 0)

    # Verify card drag works with Column C
    board_page.drag_card_to_column(2, col_c.pk)
    assert_card_column(2, col_c.pk)
