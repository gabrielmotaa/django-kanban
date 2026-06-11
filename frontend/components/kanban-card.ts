import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";
import type { KanbanColumn } from "./kanban-column";
import type { DragState } from "./kanban-board";

@customElement("kanban-card")
export class KanbanCard extends LitElement {

  @property({ attribute: "card-id", type: Number })
  cardId = 0;

  @property({ type: Number, reflect: true })
  order = 0;

  static styles = css`
    :host {
      display: block;
      margin-bottom: 8px;
      padding: 12px;
      border: 1px solid #ddd;
      border-radius: 8px;
      cursor: grab;
      user-select: none;
      background: white;
    }

    :host(.dragging) {
      opacity: 0.4;
    }
  `;

  override connectedCallback() {
    super.connectedCallback();

    this.draggable = true;
    this.addEventListener("dragstart", this.onDragStart);
    this.addEventListener("dragend", this.onDragEnd);
  }

  override disconnectedCallback() {
    super.disconnectedCallback();

    this.removeEventListener("dragstart", this.onDragStart);
    this.removeEventListener("dragend", this.onDragEnd);
  }

  private onDragStart = () => {
    const column = this.closest("kanban-column") as KanbanColumn;
    const cards = [...column.querySelectorAll("kanban-card")];
    const index = cards.indexOf(this);

    this.dispatchEvent(
      new CustomEvent("kanban-dragstart", {
        bubbles: true,
        composed: true,
        detail: {
          type: "card",
          card: this,
          fromColumn: column,
          fromIndex: index,
        } satisfies DragState,
      })
    );

    requestAnimationFrame(() => this.classList.add("dragging"));
  };

  private onDragEnd = () => {
    this.classList.remove("dragging");

    this.dispatchEvent(
      new CustomEvent("kanban-dragend", {
        bubbles: true,
        composed: true,
      })
    );
  };

  override render() {
    return html`<slot></slot>`;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "kanban-card": KanbanCard;
  }
}
