import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import pytest
from playwright.sync_api import Page, expect

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
    if expand == "card-dialog-described":
        Card.objects.filter(pk=1).update(description="First line\nSecond line")
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()
    if expand == "column-menu":
        board_page.open_column_menu("Column A")
    elif expand == "create-column":
        board_page.open_create_column_form()
    elif expand == "rename-column":
        board_page.open_column_rename("Column A")
    elif expand in ("card-dialog", "card-dialog-described"):
        board_page.open_card_dialog("Card 1")
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
        "card-dialog",
        "card-dialog-described",
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


@pytest.mark.parametrize("tech", TECHS)
def test_rename_column_keeps_cards_draggable(live_server, page: Page, tech):
    Card.objects.create(id=3, column_id=1, title="Card 3", order=1)
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()

    board_page.open_column_rename("Column A")
    column = board_page.column("Column A")
    column.get_by_role("textbox", name="Nome da coluna").fill("Renamed A")
    column.get_by_role("button", name="Salvar nome").click()
    board_page.column("Renamed A").get_by_role(
        "button", name="Opções da coluna"
    ).wait_for()

    assert board_page.card("Card 1").is_visible()
    assert board_page.card("Card 3").is_visible()
    board_page.drag_card_to_column("Card 3", "Column B")
    assert Card.objects.get(pk=3).column_id == 2
    assert Column.objects.get(pk=1).title == "Renamed A"


@pytest.mark.parametrize("tech", TECHS)
def test_recolor_column_keeps_cards_editable(live_server, page: Page, tech):
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()

    board_page.open_column_menu("Column A")
    board_page.column("Column A").get_by_role("button", name="Azul").click()
    # The UI reflects the server response (templates swap, components apply it).
    page.wait_for_function(
        """() => {
            const el = document.querySelector('kanban-column, .column');
            return el && (el.getAttribute('color') === '#3b82f6'
                || el.getAttribute('style')?.includes('#3b82f6'));
        }"""
    )
    assert Column.objects.get(pk=1).color == "#3b82f6"
    assert board_page.card("Card 1").is_visible()

    board_page.open_card_dialog("Card 1")
    board_page.rename_card_in_dialog("Edited 1")
    board_page.close_card_dialog()
    board_page.card("Edited 1").wait_for()
    assert Card.objects.get(pk=1).title == "Edited 1"


@pytest.mark.parametrize("tech", TECHS)
def test_escape_cancels_column_rename(live_server, page: Page, tech):
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()

    board_page.open_column_rename("Column A")
    column = board_page.column("Column A")
    column.get_by_role("textbox", name="Nome da coluna").fill("Never saved")
    page.keyboard.press("Escape")

    column.get_by_role("button", name="Opções da coluna").wait_for()
    assert column.get_by_role("textbox", name="Nome da coluna").count() == 0
    assert Column.objects.get(pk=1).title == "Column A"


@pytest.mark.parametrize("tech", TECHS)
def test_click_away_and_escape_close_column_menu(live_server, page: Page, tech):
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()
    column = board_page.column("Column A")
    edit = column.get_by_role("button", name="Editar nome")

    board_page.open_column_menu("Column A")
    expect(edit).to_be_visible()
    page.get_by_role("heading", level=1).click()
    edit.wait_for(state="hidden")

    board_page.open_column_menu("Column A")
    page.keyboard.press("Escape")
    edit.wait_for(state="hidden")


@pytest.mark.parametrize("tech", TECHS)
def test_create_column_persists_chosen_color(live_server, page: Page, tech):
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()

    board_page.open_create_column_form()
    page.get_by_role("textbox", name="Nome da coluna").fill("Colorful")
    page.get_by_role("button", name="Roxo").click()
    page.get_by_role("button", name="Adicionar", exact=True).click()

    for _ in range(30):
        if Column.objects.filter(title="Colorful").exists():
            break
        page.wait_for_timeout(100)
    assert Column.objects.get(title="Colorful").color == "#8b5cf6"


@pytest.mark.parametrize("tech", TECHS)
def test_invalid_card_title_shows_toast_and_keeps_form_open(
    live_server, page: Page, tech
):
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()

    column = board_page.column("Column A")
    column.get_by_role("button", name="+ Adicionar card").click()
    column.get_by_role("textbox", name="Título do card").fill("   ")
    column.get_by_role("button", name="Adicionar", exact=True).click()

    expect(board_page.toast()).to_have_text("O título é obrigatório.")
    expect(column.get_by_role("textbox", name="Título do card")).to_be_visible()
    assert Card.objects.filter(column_id=1).count() == 1


@pytest.mark.parametrize("tech", TECHS)
def test_toast_auto_dismisses(live_server, page: Page, tech):
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()

    column = board_page.column("Column A")
    column.get_by_role("button", name="+ Adicionar card").click()
    column.get_by_role("textbox", name="Título do card").fill("   ")
    column.get_by_role("button", name="Adicionar", exact=True).click()

    expect(board_page.toast()).to_be_visible()
    expect(board_page.toast()).to_have_count(0, timeout=7000)


@pytest.mark.parametrize("tech", TECHS)
def test_failed_card_move_rolls_back(live_server, page: Page, tech):
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()
    Column.objects.filter(pk=2).delete()  # behind the UI's back

    board_page.drag_card_to_column("Card 1", "Column B")

    expect(board_page.toast()).to_have_text("Coluna não encontrada.")
    assert board_page.column_has_card("Column A", "Card 1")
    assert not board_page.column_has_card("Column B", "Card 1")
    assert Card.objects.get(pk=1).column_id == 1


@pytest.mark.parametrize("tech", TECHS)
def test_failed_column_move_rolls_back(live_server, page: Page, tech):
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()
    Column.objects.filter(pk=1).delete()  # behind the UI's back

    board_page.drag_column_to_column("Column A", "Column B")

    expect(board_page.toast()).to_have_text("Coluna não encontrada.")
    assert board_page.column_titles() == ["Column A", "Column B"]
    assert Column.objects.get(pk=2).order == 1


@pytest.mark.parametrize("tech", TECHS)
def test_description_roundtrip_updates_card_front(live_server, page: Page, tech):
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()
    assert board_page.description_indicator("Column A").count() == 0

    board_page.open_card_dialog("Card 1")
    board_page.edit_description("Some details\nsecond line")
    expect(board_page.description_indicator("Column A")).to_have_count(1)
    assert Card.objects.get(pk=1).description == "Some details\nsecond line"

    # The saved text is what the dialog shows when it is opened again.
    board_page.close_card_dialog()
    board_page.open_card_dialog("Card 1")
    expect(board_page.dialog().get_by_text("Some details")).to_be_visible()

    page.reload()
    board_page.navigate()
    expect(board_page.description_indicator("Column A")).to_have_count(1)


@pytest.mark.parametrize("tech", TECHS)
def test_clearing_description_removes_indicator(live_server, page: Page, tech):
    Card.objects.filter(pk=1).update(description="to be cleared")
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()
    expect(board_page.description_indicator("Column A")).to_have_count(1)

    board_page.open_card_dialog("Card 1")
    board_page.edit_description("", current="to be cleared")
    expect(board_page.description_indicator("Column A")).to_have_count(0)
    assert Card.objects.get(pk=1).description == ""


@pytest.mark.parametrize("tech", TECHS)
def test_rename_in_dialog_updates_card_front(live_server, page: Page, tech):
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()

    board_page.open_card_dialog("Card 1")
    board_page.rename_card_in_dialog("Renamed in dialog")
    board_page.close_card_dialog()

    board_page.card("Renamed in dialog").wait_for()
    assert Card.objects.get(pk=1).title == "Renamed in dialog"
    # The renamed card is still draggable.
    board_page.drag_card_to_column("Renamed in dialog", "Column B")
    assert Card.objects.get(pk=1).column_id == 2


@pytest.mark.parametrize("tech", TECHS)
def test_delete_card_from_dialog(live_server, page: Page, tech):
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()

    board_page.open_card_dialog("Card 1")
    board_page.delete_card_from_dialog()

    expect(board_page.card("Card 1")).to_have_count(0)
    assert not Card.objects.filter(pk=1).exists()


@pytest.mark.parametrize("tech", TECHS)
def test_escape_closes_dialog_and_returns_focus(live_server, page: Page, tech):
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()

    board_page.open_card_dialog("Card 1")
    page.keyboard.press("Escape")
    board_page.dialog().wait_for(state="hidden")
    assert board_page.focused_card_text() == "Card 1"


@pytest.mark.parametrize("tech", TECHS)
def test_backdrop_click_closes_dialog(live_server, page: Page, tech):
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()

    board_page.open_card_dialog("Card 1")
    page.mouse.click(5, 5)  # outside the dialog panel
    board_page.dialog().wait_for(state="hidden")


@pytest.mark.parametrize("tech", TECHS)
def test_dialog_has_the_card_title_as_name(live_server, page: Page, tech):
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()
    board_page.open_card_dialog("Card 1")
    expect(page.get_by_role("dialog", name="Card 1")).to_be_visible()
    expect(board_page.dialog().get_by_text("na coluna Column A")).to_be_visible()


@pytest.mark.parametrize("tech", TECHS)
def test_dragging_a_card_never_opens_the_dialog(live_server, page: Page, tech):
    board_page = ParityBoardPage(page, live_server.url, tech)
    board_page.navigate()

    board_page.drag_card_to_column("Card 1", "Column B")
    assert Card.objects.get(pk=1).column_id == 2
    page.wait_for_timeout(300)
    assert board_page.dialog().count() == 0
