import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";
import type { KanbanBoard } from "./kanban-board";
import type { KanbanCard } from "./kanban-card";

@customElement("kanban-column")
export class KanbanColumn extends LitElement {
  static override styles = css`
    :host {
      display: block;
      width: 280px;
      background: white;
      border-radius: 10px;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
      padding: 12px;
      box-sizing: border-box;
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
      background: white;
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 8px;
      cursor: grab;
      user-select: none;
    }

    ::slotted(kanban-card.dragging) {
      opacity: 0.4;
    }
  `;

  @property({ attribute: "column-id", type: String })
  columnId = "";

  @property({ type: String })
  override title = "";

  override connectedCallback() {
    super.connectedCallback();

    this.addEventListener("dragenter", this._onDragEnter);
    this.addEventListener("dragleave", this._onDragLeave);
    this.addEventListener("dragover", this._onDragOver);
    this.addEventListener("drop", this._onDrop);
  }

  override disconnectedCallback() {
    super.disconnectedCallback();

    this.removeEventListener("dragenter", this._onDragEnter);
    this.removeEventListener("dragleave", this._onDragLeave);
    this.removeEventListener("dragover", this._onDragOver);
    this.removeEventListener("drop", this._onDrop);
  }

  private _onDragEnter = () => {
    this.classList.add("drag-over");
  };

  private _onDragLeave = (e: DragEvent) => {
    if (!this.contains(e.relatedTarget as Node)) {
      this.classList.remove("drag-over");
    }
  };

  private _onDragOver = (e: DragEvent) => {
    e.preventDefault();

    const board = this.closest("kanban-board") as KanbanBoard | null;
    const dragging = board?.draggingCard as KanbanCard | null;
    if (!dragging) return;

    const after = this._getCardAfterPosition(e.clientY);

    if (!after) {
      this.appendChild(dragging);
    } else {
      this.insertBefore(dragging, after);
    }
  };

  private _onDrop = () => {
    this.classList.remove("drag-over");
  };

  private _getCardAfterPosition(mouseY: number): Element | null {
    const cards = [
      ...this.querySelectorAll<KanbanCard>("kanban-card:not(.dragging)"),
    ];

    let closestOffset = Number.NEGATIVE_INFINITY;
    let closestElement: Element | null = null;

    for (const card of cards) {
      const box = card.getBoundingClientRect();
      const offset = mouseY - box.top - box.height / 2;

      if (offset < 0 && offset > closestOffset) {
        closestOffset = offset;
        closestElement = card;
      }
    }

    return closestElement;
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
