"""Role-based page object shared by both UI versions.

Every locator is built from accessible roles and names, so the very same test
body runs against ``/templates/`` and ``/components/``. The technology only
appears in the URL; if a method here ever needs ``if tech == ...`` that is a
parity defect to fix in the UI, not a reason to branch.
"""

import os
import re
from pathlib import Path

from playwright.sync_api import Locator, Page

VIEWPORT = {"width": 1280, "height": 800}


class ParityBoardPage:
    def __init__(self, page: Page, base_url: str, tech: str):
        self.page = page
        self.tech = tech
        self.url = f"{base_url}/{tech}/"
        self.page.set_viewport_size(VIEWPORT)

    def navigate(self) -> None:
        self.page.goto(self.url)
        self.page.get_by_role("heading", level=1).wait_for()
        self.page.wait_for_function("window.htmx !== undefined")
        # Let custom elements upgrade and htmx process their markup.
        self.page.wait_for_timeout(300)

    # -- locators -----------------------------------------------------------

    def column(self, title: str) -> Locator:
        return self.page.get_by_role("group", name=title, exact=True)

    def card(self, title: str) -> Locator:
        # Scoped to columns so an open dialog showing the same title is ignored.
        return self.page.get_by_role("group").get_by_text(title, exact=True)

    # -- actions ------------------------------------------------------------

    def create_card(self, column_title: str, title: str) -> None:
        column = self.column(column_title)
        column.get_by_role("button", name="+ Adicionar card").click()
        column.get_by_role("textbox", name="Título do card").fill(title)
        column.get_by_role("button", name="Adicionar", exact=True).click()
        self.card(title).wait_for()

    def drag_card_to_column(self, card_title: str, column_title: str) -> None:
        card = self.card(card_title)
        column = self.column(column_title)
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

    def drag_column_to_column(self, source_title: str, target_title: str) -> None:
        self.column(source_title).drag_to(
            self.column(target_title),
            source_position={"x": 140, "y": 20},
            target_position={"x": 140, "y": 20},
        )
        self.page.wait_for_timeout(500)

    def column_titles(self) -> list[str]:
        return self.page.get_by_role("group").evaluate_all(
            "els => els.map(e => e.getAttribute('aria-label'))"
        )

    def column_has_card(self, column_title: str, card_title: str) -> bool:
        return self.column(column_title).get_by_text(card_title, exact=True).count() > 0

    def toast(self) -> Locator:
        return self.page.get_by_role("alert")

    def open_column_menu(self, column_title: str) -> None:
        self.column(column_title).get_by_role("button", name="Opções da coluna").click()

    def open_column_rename(self, column_title: str) -> None:
        self.open_column_menu(column_title)
        column = self.column(column_title)
        column.get_by_role("button", name="Editar nome").click()
        column.get_by_role("textbox", name="Nome da coluna").wait_for()

    # -- card dialog --------------------------------------------------------

    def dialog(self) -> Locator:
        return self.page.get_by_role("dialog")

    def open_card_dialog(self, card_title: str) -> None:
        self.card(card_title).click()
        self.dialog().get_by_role("button", name="Fechar").wait_for()

    def close_card_dialog(self) -> None:
        self.dialog().get_by_role("button", name="Fechar").click()
        self.dialog().wait_for(state="hidden")

    def rename_card_in_dialog(self, new_title: str) -> None:
        dialog = self.dialog()
        dialog.get_by_role("heading", level=2).get_by_role("button").click()
        dialog.get_by_role("textbox", name="Título do card").fill(new_title)
        dialog.get_by_role("button", name="Salvar", exact=True).click()
        dialog.get_by_role("heading", level=2, name=new_title).wait_for()

    def edit_description(self, text: str, current: str | None = None) -> None:
        # Page-level locators: in the components version the description is a
        # slotted light-DOM child of the dialog host, not a DOM descendant of
        # the <dialog> element, so a dialog-scoped locator would miss it.
        page = self.page
        label = current or "Adicione uma descrição mais detalhada…"
        page.get_by_role("button", name=label, exact=True).click()
        page.get_by_role("textbox", name="Descrição").fill(text)
        page.get_by_role("button", name="Salvar", exact=True).click()
        page.get_by_role("textbox", name="Descrição").wait_for(state="hidden")

    def description_button(self, text: str) -> Locator:
        return self.page.get_by_role("button", name=text)

    # -- labels (page-level locators: see edit_description) ------------------

    def open_label_popover(self) -> None:
        self.page.get_by_role("button", name="Adicionar etiqueta").click()
        self.page.get_by_role("searchbox", name="Buscar etiquetas…").wait_for()

    def toggle_label(self, name: str, checked: bool) -> None:
        self.page.get_by_role("checkbox", name=name, exact=True).set_checked(checked)

    def label_checkbox(self, name: str) -> Locator:
        return self.page.get_by_role("checkbox", name=name, exact=True)

    def start_editing_label(self, name: str) -> None:
        self.page.get_by_role("button", name=f"Editar etiqueta {name}").click()
        self.page.get_by_role("textbox", name="Nome da etiqueta").wait_for()

    def save_label_form(self, name: str | None = None, color: str | None = None):
        if name is not None:
            self.page.get_by_role("textbox", name="Nome da etiqueta").fill(name)
        if color is not None:
            self.page.get_by_role("button", name=color, exact=True).click()
        self.page.get_by_role("button", name="Salvar", exact=True).click()

    def delete_label_in_form(self) -> None:
        self.page.once("dialog", lambda d: d.accept())
        self.page.get_by_role("button", name="Excluir", exact=True).click()

    def card_label_count(self, column_title: str, label_name: str) -> int:
        return self.column(column_title).get_by_text(label_name, exact=True).count()

    # -- due date (page-level locators: see edit_description) -----------------

    def open_due_popover(self) -> None:
        # The trigger is "Adicionar data" or the formatted date; both live in
        # the "Data de entrega" section, the only button there that is not
        # the completion checkbox.
        self.page.get_by_role(
            "button", name=re.compile(r"^(Adicionar data|\d{2}\/\d{2}\/\d{4})$")
        ).click()
        self.page.get_by_role("region", name="Alterar data de entrega").wait_for()

    def set_due_date(self, iso: str) -> None:
        self.open_due_popover()
        self.page.get_by_label("Data", exact=True).fill(iso)
        self.page.get_by_role("button", name="Salvar", exact=True).click()
        self.page.get_by_role("region", name="Alterar data de entrega").wait_for(
            state="hidden"
        )

    def remove_due_date(self) -> None:
        self.open_due_popover()
        self.page.get_by_role("button", name="Remover", exact=True).click()
        self.page.get_by_role("button", name="Adicionar data").wait_for()

    def completed_checkbox(self) -> Locator:
        return self.page.get_by_role("checkbox", name="Concluído", exact=True)

    def due_badge(self, column_title: str, label: str) -> Locator:
        return self.column(column_title).get_by_role("img", name=label)

    # -- checklists (page-level locators: see edit_description) ---------------

    def add_checklist(self, title: str | None = None) -> None:
        self.page.get_by_role("button", name="Checklist", exact=True).click()
        popover = self.page.get_by_role("region", name="Adicionar checklist")
        popover.wait_for()
        if title is not None:
            popover.get_by_role("textbox", name="Título do novo checklist").fill(title)
        popover.get_by_role("button", name="Adicionar", exact=True).click()
        popover.wait_for(state="hidden")

    def checklist_region(self, title: str) -> Locator:
        return self.page.get_by_role("region", name=title, exact=True)

    def add_item(self, text: str) -> None:
        box = self.page.get_by_role("textbox", name="Adicionar um item")
        box.fill(text)
        box.press("Enter")
        self.item_checkbox(text).wait_for()

    def item_checkbox(self, text: str) -> Locator:
        return self.page.get_by_role("checkbox", name=text, exact=True)

    def item_row(self, text: str) -> Locator:
        return self.page.get_by_role("listitem").filter(has=self.item_checkbox(text))

    def remove_item(self, text: str) -> None:
        row = self.item_row(text)
        row.get_by_role("button", name="Remover item").click()
        row.wait_for(state="detached")

    def progress(self, title: str = "Checklist") -> Locator:
        return self.page.get_by_role("progressbar", name=f"Progresso de {title}")

    def checklist_badge(self, column_title: str) -> Locator:
        return self.column(column_title).get_by_role(
            "img", name=re.compile(r"^Checklist \d+ de \d+$")
        )

    # -- comments and activity (page-level locators: see edit_description) -----

    def add_comment(self, text: str) -> None:
        box = self.page.get_by_role("textbox", name="Escrever um comentário…")
        box.fill(text)
        self.page.get_by_role("button", name="Salvar comentário").click()
        self.timeline_item(text).wait_for()

    def timeline_item(self, text: str) -> Locator:
        return self.page.get_by_role("listitem").filter(has_text=text)

    def comment_badge(self, column_title: str) -> Locator:
        return self.column(column_title).get_by_role(
            "img", name=re.compile(r"comentários?$")
        )

    def delete_card_from_dialog(self) -> None:
        self.page.once("dialog", lambda d: d.accept())
        self.dialog().get_by_role("button", name="Excluir card").click()
        self.dialog().wait_for(state="hidden")

    def description_indicator(self, column_title: str) -> Locator:
        return self.column(column_title).get_by_role(
            "img", name="Este card tem descrição"
        )

    def wait_for_focused_card(self, text: str) -> None:
        """Focus is restored right after the dialog's close event: poll for it."""
        self.page.wait_for_function(
            """(text) => {
                const el = document.activeElement;
                const card = el && el.closest('.card, kanban-card');
                return !!card && card.textContent.trim().startsWith(text);
            }""",
            arg=text,
        )

    def focused_card_text(self) -> str:
        return self.page.evaluate(
            """() => {
                const el = document.activeElement;
                const card = el && el.closest('.card, kanban-card');
                return card ? card.textContent.trim() : '';
            }"""
        )

    def open_board_title_editor(self) -> None:
        self.page.get_by_role("button", name="Editar título do quadro").click()
        self.page.get_by_role("textbox", name="Título do quadro").wait_for()

    def open_create_column_form(self) -> None:
        self.page.get_by_role("button", name="+ Adicionar coluna").click()
        self.page.get_by_role("textbox", name="Nome da coluna").wait_for()

    # -- snapshots ----------------------------------------------------------

    def aria_snapshot(self) -> str:
        """Whitespace-normalized aria snapshot of the whole page body.

        Playwright also reports light-DOM text that a shadow root does not
        slot (the components cards carry their title as text content *and*
        render it from the ``title`` property), so a ``text: X X`` line where
        both halves are identical is collapsed to ``text: X``. Browsers do not
        expose the unslotted text, so this is a tooling artifact, not a
        difference a user can perceive. The same applies to the leftover text
        shown next to the card title textbox while editing (dropped below).
        """
        raw = self._stable_snapshot()
        lines = [re.sub(r"\s+", " ", line).rstrip() for line in raw.splitlines()]
        lines = [re.sub(r"^(\s*- text: )(.+) \2$", r"\1\2", line) for line in lines]
        # Same artifact with the rendered card front in between (labels, badges):
        # "text: Card 1 Bug Card 1" -> "text: Bug Card 1".
        lines = [
            re.sub(
                r"^(\s*- text: )(?P<t>.+?) (?P<mid>.+) (?P=t)$",
                r"\1\g<mid> \g<t>",
                line,
            )
            for line in lines
        ]
        # While a card is being edited the component's unslotted light-DOM
        # title is the only leftover; it sits right before the title textbox.
        return "\n".join(
            line
            for line, nxt in zip(lines, [*lines[1:], ""], strict=True)
            if not (
                line.strip().startswith("- text: ")
                and nxt.strip().endswith(f": {line.strip()[8:]}")
            )
        )

    def _stable_snapshot(self) -> str:
        """Take snapshots until two consecutive ones match (UI settled)."""
        previous = self.page.locator("body").aria_snapshot()
        for _ in range(20):
            self.page.wait_for_timeout(100)
            current = self.page.locator("body").aria_snapshot()
            if current == previous:
                return current
            previous = current
        return previous

    def screenshot(self, name: str) -> None:
        """Save ``<PARITY_SCREENSHOTS_DIR>/<name>-<tech>.png`` when the env var is set."""
        directory = os.environ.get("PARITY_SCREENSHOTS_DIR")
        if not directory:
            return
        Path(directory).mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=str(Path(directory) / f"{name}-{self.tech}.png"))
