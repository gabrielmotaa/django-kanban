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
        return self.page.get_by_text(title, exact=True)

    # -- actions ------------------------------------------------------------

    def create_card(self, column_title: str, title: str) -> None:
        column = self.column(column_title)
        column.get_by_role("button", name="+ Adicionar card").click()
        column.get_by_label("Título do card").fill(title)
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

    def open_column_menu(self, column_title: str) -> None:
        self.column(column_title).get_by_role("button", name="Opções da coluna").click()

    def open_create_column_form(self) -> None:
        self.page.get_by_role("button", name="+ Adicionar coluna").click()

    # -- snapshots ----------------------------------------------------------

    def aria_snapshot(self) -> str:
        """Whitespace-normalized aria snapshot of the whole page body."""
        raw = self.page.locator("body").aria_snapshot()
        return "\n".join(
            re.sub(r"\s+", " ", line).rstrip() for line in raw.splitlines()
        )

    def screenshot(self, name: str) -> None:
        """Save ``<PARITY_SCREENSHOTS_DIR>/<name>-<tech>.png`` when the env var is set."""
        directory = os.environ.get("PARITY_SCREENSHOTS_DIR")
        if not directory:
            return
        Path(directory).mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=str(Path(directory) / f"{name}-{self.tech}.png"))
