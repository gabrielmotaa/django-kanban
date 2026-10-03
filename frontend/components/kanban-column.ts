import { css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { applyServerElement } from "../lib/apply-server-element";
import { CardDropController } from "../lib/drag/card-drop-controller";
import { ColumnReorderController } from "../lib/drag/column-reorder-controller";
import { HtmxElement } from "../lib/htmx-element";
import { buttons } from "../styles/buttons";
import { forms } from "../styles/forms";
import { reset } from "../styles/reset";

/**
 * A board column: layout, the cards slot and the add-card form. The header is
 * `<kanban-column-header>`; drag and drop is delegated to controllers.
 */
@customElement("kanban-column")
export class KanbanColumn extends HtmxElement {
	static styles = [
		reset,
		buttons,
		forms,
		css`
      :host {
        display: block;
        width: 280px;
        flex-shrink: 0;
        background: var(--color-bg-column);
        border-radius: var(--radius-xl);
        box-shadow: var(--shadow-md);
        padding: 0;
        box-sizing: border-box;
        max-height: 100%;
        display: flex;
        flex-direction: column;
        border: 1px solid var(--color-border);
        min-height: 150px;
      }

      :host(.drag-over) {
        outline: 2px solid var(--color-primary);
        outline-offset: -2px;
      }

      :host(.dragging-col) {
        opacity: 0.4;
      }

      .body {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 12px;
        flex-grow: 1;
        min-height: 0;
      }

      .cards {
        flex-grow: 1;
        overflow-y: auto;
        min-height: 0;
        padding: 0;
      }

      .add-card-trigger {
        width: 100%;
        background: rgba(255, 255, 255, 0.2);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-lg);
        padding: 12px;
        text-align: left;
        color: var(--color-text-light);
        font-weight: var(--font-weight-medium);
        cursor: pointer;
        transition: background var(--transition-normal), color var(--transition-normal);
      }

      .add-card-trigger:hover {
        background: var(--color-border-hover);
        color: var(--color-text-primary);
      }

      .add-card-form {
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 4px;
      }

      .add-card-actions {
        display: flex;
        justify-content: flex-end;
        gap: 6px;
      }

      ::slotted(kanban-card) {
        display: block;
      }
    `,
	];

	@property({ attribute: "column-id", type: Number })
	columnId = 0;

	@property()
	title = "";

	@property()
	color = "#64748b";

	@property({ type: Number, reflect: true })
	order = 0;

	@property({ attribute: "fg-color" })
	fgColor = "#ffffff";

	@property()
	href = "";

	@property({ attribute: "create-card-url" })
	createCardUrl = "";

	constructor() {
		super();
		this.addController(new CardDropController(this));
		this.addController(new ColumnReorderController(this));
	}

	updateOrders() {
		const cards = [...this.querySelectorAll("kanban-card")];
		cards.forEach((card, index) => {
			card.order = index;
		});
	}

	// The header emits the server's (minimal) column element after a PATCH.
	private onSaved = (e: CustomEvent<{ html: string }>) => {
		e.stopPropagation();
		applyServerElement(this, e.detail.html);
	};

	private onDeleted = (e: Event) => {
		e.stopPropagation();
		this.remove();
	};

	protected override updated(changed: Map<string, unknown>) {
		super.updated(changed);
		this.setAttribute("role", "group");
		this.setAttribute("aria-label", this.title);
	}

	override render() {
		return html`
      <kanban-column-header
        .title=${this.title}
        .color=${this.color}
        .fgColor=${this.fgColor}
        .href=${this.href}
        @kanban-saved=${this.onSaved}
        @kanban-column-deleted=${this.onDeleted}
      ></kanban-column-header>

      <div class="body">
        <div class="cards">
          <slot></slot>
        </div>

        <kanban-add-form>
          <button slot="trigger" type="button" class="add-card-trigger">
            + Adicionar card
          </button>
          <form
            class="add-card-form"
            hx-post=${this.createCardUrl}
            hx-target="host"
            hx-swap="beforeend"
          >
            <input type="hidden" name="column_id" .value=${String(this.columnId)} />
            <input
              type="text"
              name="title"
              class="field add-card-input"
              placeholder="Título do card..."
              aria-label="Título do card"
              required
              maxlength="200"
            />
            <div class="add-card-actions">
              <button type="button" class="btn btn-secondary add-card-cancel" data-add-form-cancel>
                Cancelar
              </button>
              <button type="submit" class="btn btn-primary add-card-submit">
                Adicionar
              </button>
            </div>
          </form>
        </kanban-add-form>
      </div>
    `;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-column": KanbanColumn;
	}
}
