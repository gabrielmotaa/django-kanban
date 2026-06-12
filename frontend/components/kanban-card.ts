import { css, html, LitElement } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { DragState } from "./kanban-board";
import type { KanbanColumn } from "./kanban-column";

@customElement("kanban-card")
export class KanbanCard extends LitElement {
  @property({ attribute: "card-id", type: Number })
  cardId = 0;

  @property({ type: Number, reflect: true })
  order = 0;

  @property()
  title = "";

  @state()
  private editing = false;

  private isDragging = false;

  static styles = css`
    :host {
      display: block;
    }

    input, button, select, textarea {
      font: inherit;
    }

    .card {
      background: var(--color-bg-card);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-lg);
      padding: 12px;
      margin-bottom: 8px;
      cursor: grab;
      user-select: none;
      box-shadow: var(--shadow-sm);
      transition: box-shadow var(--transition-normal), border-color var(--transition-normal), transform var(--transition-fast);
    }

    .card:hover {
      box-shadow: var(--shadow-md);
      border-color: var(--color-border-hover);
    }

    :host(.dragging) .card {
      opacity: 0.4;
    }

    .title-view {
      color: var(--color-text-primary);
      font-size: var(--font-size-lg);
      font-weight: var(--font-weight-medium);
      line-height: 1.5;
      word-break: break-word;
    }

    .edit-form {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .edit-input {
      width: 100%;
      padding: 8px 12px;
      border: 1px solid var(--color-input-border);
      border-radius: var(--radius-md);
      font-size: var(--font-size-lg);
      outline: none;
      box-sizing: border-box;
      color: var(--color-text-primary);
    }

    .edit-input:focus {
      border-color: var(--color-primary);
    }

    .edit-actions {
      display: flex;
      justify-content: flex-end;
      align-items: center;
      gap: 6px;
    }

    .btn-save,
    .btn-cancel,
    .btn-delete {
      padding: 6px 10px;
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
      border-radius: var(--radius-sm);
      border: none;
      cursor: pointer;
      transition: background var(--transition-normal), color var(--transition-normal);
    }

    .btn-save {
      background: var(--color-primary);
      color: white;
    }

    .btn-save:hover {
      background: var(--color-primary-hover);
    }

    .btn-cancel {
      background: var(--color-border);
      color: var(--color-text-light);
    }

    .btn-cancel:hover {
      background: var(--color-border-hover);
    }

    .btn-delete {
      background: none;
      color: var(--color-danger);
      margin-right: auto;
      padding-left: 0;
      padding-right: 0;
      font-weight: var(--font-weight-medium);
      border: none;
    }

    .btn-delete:hover {
      text-decoration: underline;
    }
  `;

  get editUrl(): string {
    return window.urls.cardDetail.replace("/0/", `/${this.cardId}/`);
  }

  get deleteUrl(): string {
    return window.urls.cardDetail.replace("/0/", `/${this.cardId}/`);
  }

  override updated() {
    if (this.shadowRoot) {
      // biome-ignore lint: htmx.process() accepts ShadowRoot at runtime but TS types don't reflect it
      window.htmx.process(this.shadowRoot as any);
    }
  }

  override firstUpdated() {
    if (!this.title) {
      this.title = this.textContent?.trim() || "";
    }
  }

  override connectedCallback() {
    super.connectedCallback();

    this.draggable = true;
    this.addEventListener("dragstart", this.onDragStart);
    this.addEventListener("dragend", this.onDragEnd);
    this.addEventListener("click", this.onCardClick);
  }

  override disconnectedCallback() {
    super.disconnectedCallback();

    this.removeEventListener("dragstart", this.onDragStart);
    this.removeEventListener("dragend", this.onDragEnd);
    this.removeEventListener("click", this.onCardClick);
  }

  private onDragStart = () => {
    const column = this.closest("kanban-column") as KanbanColumn;
    const cards = [...column.querySelectorAll("kanban-card")];
    const index = cards.indexOf(this);

    this.dispatchEvent(
      new CustomEvent("kanban-card-dragstart", {
        bubbles: true,
        composed: true,
        detail: {
          type: "card",
          card: this,
          fromColumn: column,
          fromIndex: index,
        } satisfies DragState,
      }),
    );

    this.isDragging = true;
    requestAnimationFrame(() => this.classList.add("dragging"));
  };

  private onDragEnd = () => {
    this.classList.remove("dragging");
    setTimeout(() => {
      this.isDragging = false;
    }, 0);

    this.dispatchEvent(
      new CustomEvent("kanban-card-dragend", {
        bubbles: true,
        composed: true,
      }),
    );
  };

  private onCardClick = () => {
    if (this.editing) return;
    if (this.isDragging) return;
    this.editing = true;
    this.updateComplete.then(() => {
      const input = this.shadowRoot?.querySelector(
        ".edit-input",
      ) as HTMLInputElement;
      input?.focus();
    });
  };

  private onCancel = (e: Event) => {
    e.preventDefault();
    e.stopPropagation();
    this.editing = false;
  };

  private onKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Escape") {
      this.editing = false;
    }
  };

  override render() {
    return html`
      <div class="card">
        ${this.editing
        ? html`
              <form class="edit-form" hx-patch=${this.editUrl} hx-target="host" hx-swap="outerHTML" @click=${(e: Event) => e.stopPropagation()}>
                <input
                  type="text"
                  name="title"
                  .value=${this.title}
                  class="edit-input"
                  maxlength="200"
                  @keydown=${this.onKeyDown}
                />
                <div class="edit-actions">
                  <button
                    type="button"
                    class="btn-delete"
                    hx-delete=${this.deleteUrl}
                    hx-target="host"
                    hx-swap="outerHTML"
                    hx-confirm="Deletar este card?"
                  >
                    Deletar
                  </button>
                  <button type="button" class="btn-cancel" @click=${this.onCancel}>
                    Cancelar
                  </button>
                  <button type="submit" class="btn-save">Salvar</button>
                </div>
              </form>
            `
        : html`<div class="title-view">${this.title}</div>`
      }
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "kanban-card": KanbanCard;
  }
}
