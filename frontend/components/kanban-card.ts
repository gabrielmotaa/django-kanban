import { LitElement } from "lit";
import { customElement, property } from "lit/decorators.js";
import type { KanbanBoard } from "./kanban-board";

@customElement("kanban-card")
export class KanbanCard extends LitElement {
  // Cards are slotted into kanban-column's shadow DOM, so we intentionally
  // disable shadow root so that the parent column's ::slotted() rules apply.
  protected override createRenderRoot() {
    return this;
  }

  @property({ attribute: "card-id", type: String })
  cardId = "";

  @property({ type: Number })
  order = 0;

  override connectedCallback() {
    super.connectedCallback();
    this.draggable = true;

    this.addEventListener("dragstart", this._onDragStart);
    this.addEventListener("dragend", this._onDragEnd);
  }

  override disconnectedCallback() {
    super.disconnectedCallback();
    this.removeEventListener("dragstart", this._onDragStart);
    this.removeEventListener("dragend", this._onDragEnd);
  }

  private _onDragStart = () => {
    const board = this.closest("kanban-board") as KanbanBoard | null;
    if (!board) return;

    board.draggingCard = this;
    board.sourceColumn = this.closest("kanban-column");

    requestAnimationFrame(() => {
      this.classList.add("dragging");
    });
  };

  private _onDragEnd = () => {
    this.classList.remove("dragging");

    const board = this.closest("kanban-board") as KanbanBoard | null;
    if (!board) return;

    const destinationColumn = this.closest("kanban-column");
    const cards = [
      ...(destinationColumn?.querySelectorAll("kanban-card") ?? []),
    ] as KanbanCard[];

    const index = cards.indexOf(this);

    board.updateOrders();

    board.dispatchEvent(
      new CustomEvent("cardmove", {
        detail: {
          cardId: this.cardId,
          from: board.sourceColumn?.getAttribute("column-id"),
          to: destinationColumn?.getAttribute("column-id"),
          index,
        },
      })
    );

    board.draggingCard = null;
    board.sourceColumn = null;
  };


}

declare global {
  interface HTMLElementTagNameMap {
    "kanban-card": KanbanCard;
  }
}
