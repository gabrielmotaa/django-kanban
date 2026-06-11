import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";
import type { KanbanBoard } from "./kanban-board";
import type { KanbanCard } from "./kanban-card";

@customElement("kanban-column")
export class KanbanColumn extends LitElement {
  static styles = css`
    :host {
      display: block;
      width: 280px;
      background: white;
      border-radius: 10px;
      padding: 12px;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    }

    .title {
      font-weight: 600;
      margin-bottom: 12px;
    }

    .content {
      min-height: 120px;
    }

    :host(.drag-over) {
      outline: 2px solid dodgerblue;
    }

    ::slotted(kanban-card) {
      display: block;
    }
  `;

  @property({ attribute: "column-id", type: Number })
  columnId = 0;

  @property()
  title = "";

  override connectedCallback() {
    super.connectedCallback();

    this.addEventListener("dragenter", this.onDragEnter);
    this.addEventListener("dragleave", this.onDragLeave);
    this.addEventListener("dragover", this.onDragOver);
    this.addEventListener("drop", this.onDrop);
  }

  override disconnectedCallback() {
    super.disconnectedCallback();

    this.removeEventListener("dragenter", this.onDragEnter);
    this.removeEventListener("dragleave", this.onDragLeave);
    this.removeEventListener("dragover", this.onDragOver);
    this.removeEventListener("drop", this.onDrop);
  }

  private get board(): KanbanBoard {
    return this.closest("kanban-board") as KanbanBoard;
  }

  private get dragState() {
    return this.board.dragState;
  }

  updateOrders() {
    const cards = [...this.querySelectorAll("kanban-card")];
    cards.forEach((card, index) => {
      card.order = index;
    });
  }

  private onDragEnter = () => {
    this.classList.add("drag-over");
  };

  private onDragLeave = (e: DragEvent) => {
    if (!this.contains(e.relatedTarget as Node)) {
      this.classList.remove("drag-over");
    }
  };

  private onDragOver = (e: DragEvent) => {
    e.preventDefault();

    const state = this.dragState;
    if (!state || state.type !== "card") return;

    const after = this.getCardAfterPosition(e.clientY);

    if (!after) {
      this.appendChild(state.card);
    } else {
      this.insertBefore(state.card, after);
    }
  };

  private onDrop = () => {
    this.classList.remove("drag-over");

    const state = this.board.dragState;
    if (!state || state.type !== "card") return;

    const cards = [...this.querySelectorAll("kanban-card")];
    const toIndex = cards.indexOf(state.card);

    // Early return if the card was dropped in the same position
    if (state.fromColumn === this && state.fromIndex === toIndex) {
      return;
    }

    // Update kanban-cards order in columns
    if (state.fromColumn !== this) {
      state.fromColumn.updateOrders();
      this.updateOrders();
    } else {
      this.updateOrders();
    }

    this.dispatchEvent(
      new CustomEvent("cardmove", {
        bubbles: true,
        composed: true,
        detail: {
          card_id: state.card.cardId,
          column_id: this.columnId,
          order: toIndex,
        },
      })
    );
  };

  private getCardAfterPosition(mouseY: number): Element | null {
    const cards = [
      ...this.querySelectorAll<KanbanCard>("kanban-card:not(.dragging)"),
    ];

    let closest: Element | null = null;
    let closestOffset = Number.NEGATIVE_INFINITY;

    for (const card of cards) {
      const box = card.getBoundingClientRect();
      const offset = mouseY - box.top - box.height / 2;

      if (offset < 0 && offset > closestOffset) {
        closestOffset = offset;
        closest = card;
      }
    }

    return closest;
  }

  override render() {
    return html`
      <div class="title">${this.title}</div>
      <div class="content">
        <slot></slot>
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "kanban-column": KanbanColumn;
  }
}
