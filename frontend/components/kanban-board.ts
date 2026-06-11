import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";
import type { KanbanCard } from "./kanban-card";
import type { KanbanColumn } from "./kanban-column";

export type DragState =
  | {
    type: "card";
    card: KanbanCard;
    fromColumn: KanbanColumn;
    fromIndex: number;
  }
  | {
    type: "column";
    column: KanbanColumn;
    fromIndex: number;
  }
  | null;

export type CardMoveDetail = {
  card_id: number;
  column_id: number;
  order: number;
}

@customElement("kanban-board")
export class KanbanBoard extends LitElement {

  @property({ attribute: "move-card-url" })
  moveCardUrl = "";

  @property({ attribute: "move-column-url" })
  moveColumnUrl = "";

  dragState: DragState = null;

  static styles = css`
    :host {
      display: flex;
      gap: 16px;
      align-items: flex-start;
    }
  `;

  override connectedCallback() {
    super.connectedCallback();

    this.addEventListener("kanban-dragstart", this.onDragStart as EventListener);
    this.addEventListener("kanban-dragend", this.onDragEnd as EventListener);
    this.addEventListener("cardmove", this.onCardMove as EventListener);
  }

  private onDragStart = (e: CustomEvent) => {
    this.dragState = e.detail;
  };

  private onDragEnd = () => {
    this.dragState = null;
  };

  private onCardMove = (e: CustomEvent<CardMoveDetail>) => {
    window.htmx.ajax("post", this.moveCardUrl, {
      values: e.detail,
      swap: "none",
    });

    this.dragState = null;
  };

  render() {
    return html`<slot></slot>`;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "kanban-board": KanbanBoard;
  }
}
