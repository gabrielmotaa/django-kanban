import { css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { HtmxElement } from "../lib/htmx-element";
import { buttons } from "../styles/buttons";
import { forms } from "../styles/forms";
import { reset } from "../styles/reset";
import type { DragState } from "./kanban-board";
import type { KanbanColumn } from "./kanban-column";

/** A card on the board; draggable, edited inline until the dialog (007). */
@customElement("kanban-card")
export class KanbanCard extends HtmxElement {
	static styles = [
		reset,
		buttons,
		forms,
		css`
      :host {
        display: block;
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
        --field-padding: 8px 12px;
        --btn-font-size: var(--font-size-sm);
      }

      .edit-input {
        color: var(--color-text-primary);
      }

      .edit-actions {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 6px;
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
    `,
	];

	@property({ attribute: "card-id", type: Number })
	cardId = 0;

	@property({ type: Number, reflect: true })
	order = 0;

	@property()
	title = "";

	@property()
	href = "";

	@state()
	private editing = false;

	private isDragging = false;

	override firstUpdated() {
		if (!this.title) {
			this.title = this.textContent?.trim() || "";
		}
	}

	override connectedCallback() {
		super.connectedCallback();

		this.draggable = true;
		const { signal } = this;
		this.addEventListener("dragstart", this.onDragStart, { signal });
		this.addEventListener("dragend", this.onDragEnd, { signal });
		this.addEventListener("click", this.onCardClick, { signal });
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
		this.focusAfterRender(".edit-input");
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
        ${
					this.editing
						? html`
              <form class="edit-form" hx-patch=${this.href} hx-target="host" hx-swap="outerHTML" @click=${(e: Event) => e.stopPropagation()}>
                <input
                  type="text"
                  name="title"
                  .value=${this.title}
                  aria-label="Título do card"
                  class="field edit-input"
                  maxlength="200"
                  @keydown=${this.onKeyDown}
                />
                <div class="edit-actions">
                  <button
                    type="button"
                    class="btn btn-delete"
                    hx-delete=${this.href}
                    hx-target="host"
                    hx-swap="outerHTML"
                    hx-confirm="Deletar este card?"
                  >
                    Deletar
                  </button>
                  <button type="button" class="btn btn-secondary btn-cancel" @click=${this.onCancel}>
                    Cancelar
                  </button>
                  <button type="submit" class="btn btn-primary btn-save">Salvar</button>
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
