import { LitElement, html, css } from "lit";
import { customElement } from "lit/decorators.js";
import type { KanbanCard } from "./kanban-card";
import type { KanbanColumn } from "./kanban-column";

export interface CardMoveDetail {
  cardId: string;
  from: string | null;
  to: string | null;
  index: number;
}

export interface ColumnState {
  columnId: string | null;
  cards: { id: string | null; order: number; title: string }[];
}

@customElement("kanban-board")
export class KanbanBoard extends LitElement {
  static override styles = css`
    :host {
      display: flex;
      gap: 16px;
      align-items: flex-start;
    }
  `;

  /** The card currently being dragged. Set by KanbanCard. */
  draggingCard: KanbanCard | null = null;

  /** The column the drag originated from. Set by KanbanCard. */
  sourceColumn: Element | null = null;

  override connectedCallback() {
    super.connectedCallback();

    this.updateOrders();

    this.addEventListener("cardmove", (e: Event) => {
      const detail = (e as CustomEvent<CardMoveDetail>).detail;
      this.dispatchEvent(
        new CustomEvent<CardMoveDetail>("kanban-cardmove", {
          bubbles: true,
          composed: true,
          detail,
        })
      );
    });
  }

  /** Stamps order attributes onto every card in every column. */
  updateOrders() {
    this.querySelectorAll<KanbanColumn>("kanban-column").forEach((column) => {
      [...column.querySelectorAll<KanbanCard>("kanban-card")].forEach(
        (card, index) => {
          card.setAttribute("order", String(index));
          card.order = index;
        }
      );
    });
  }

  override render() {
    return html`<slot></slot>`;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "kanban-board": KanbanBoard;
  }
}
