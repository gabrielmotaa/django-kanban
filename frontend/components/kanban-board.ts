import { css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { HtmxElement } from "../lib/htmx-element";
import { buttons } from "../styles/buttons";
import { forms } from "../styles/forms";
import { reset } from "../styles/reset";
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
	href: string;
	column_id: number;
	order: number;
};

const WEB_COMPONENTS_HEADERS = { "X-Web-Components": "true" };
const DEFAULT_COLUMN_COLOR = "#64748b";

/**
 * The board: owns the drag state shared by cards and columns, sends move
 * requests, hosts the palette (`colors` attribute) and the add-column form.
 */
@customElement("kanban-board")
export class KanbanBoard extends HtmxElement {
	static styles = [
		reset,
		buttons,
		forms,
		css`
      :host {
        display: block;
        width: 100%;
        height: 100%;
      }

      .board-wrapper {
        flex-grow: 1;
        display: flex;
        gap: 16px;
        align-items: flex-start;
        overflow-x: auto;
        overflow-y: hidden;
        padding-bottom: 8px;
        height: 100%;
      }

      .board {
        display: flex;
        gap: 16px;
        align-items: flex-start;
        height: 100%;
      }

      /* Column Create Button & Form */
      .create-column {
        width: 280px;
        flex-shrink: 0;
      }

      .trigger {
        background: var(--color-bg-button-add);
        border: none;
        border-radius: var(--radius-lg);
        padding: 12px 18px;
        font-weight: var(--font-weight-medium);
        color: var(--color-text-light);
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 6px;
        width: 100%;
        justify-content: center;
        transition: background var(--transition-normal);
      }

      .trigger:hover {
        background: var(--color-bg-button-add-hover);
      }

      .form {
        background: var(--color-bg-card);
        padding: 16px;
        border-radius: var(--radius-xl);
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--color-border);
        width: 280px;
        box-sizing: border-box;
        --field-padding: 8px 12px;
        --btn-padding: 6px 12px;
        --btn-font-size: var(--font-size-base);
        --btn-radius: var(--radius-md);
        --btn-secondary-bg: var(--color-text-muted);
        --btn-secondary-fg: white;
        --btn-secondary-hover-bg: var(--color-text-light);
      }

      .input {
        margin-bottom: 12px;
      }

      .color-label {
        display: block;
        font-size: var(--font-size-sm);
        font-weight: var(--font-weight-semibold);
        color: var(--color-text-muted);
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }

      .actions {
        display: flex;
        gap: 8px;
        justify-content: flex-end;
      }
    `,
	];

	@property({ type: Number, attribute: "board-id" })
	boardId = 0;

	@property({ attribute: "create-column-url" })
	createColumnUrl = "";

	dragState: DragState = null;

	@state()
	private newColumnColor = DEFAULT_COLUMN_COLOR;

	override connectedCallback() {
		super.connectedCallback();

		const { signal } = this;
		this.addEventListener(
			"kanban-card-dragstart",
			this.onDragStart as EventListener,
			{ signal },
		);
		this.addEventListener(
			"kanban-card-dragend",
			this.onDragEnd as EventListener,
			{ signal },
		);
		this.addEventListener(
			"kanban-column-dragstart",
			this.onDragStart as EventListener,
			{ signal },
		);
		this.addEventListener(
			"kanban-column-dragend",
			this.onDragEnd as EventListener,
			{ signal },
		);
		this.addEventListener("cardmove", this.onCardMove as EventListener, {
			signal,
		});
		this.addEventListener("columnmove", this.onColumnMove as EventListener, {
			signal,
		});
	}

	private onDragStart = (e: CustomEvent) => {
		this.dragState = e.detail;
	};

	private onDragEnd = () => {
		this.dragState = null;
	};

	private onCardMove = (e: CustomEvent<CardMoveDetail>) => {
		const { href, column_id, order } = e.detail;
		window.htmx.ajax("patch", href, {
			values: { column_id, order },
			headers: WEB_COMPONENTS_HEADERS,
			swap: "none",
		});

		this.dragState = null;
	};

	private onColumnMove = (e: CustomEvent) => {
		const { href, order, fromIndex } = e.detail;
		this.updateColumnOrders();

		if (fromIndex !== order) {
			window.htmx.ajax("patch", href, {
				values: { order },
				headers: WEB_COMPONENTS_HEADERS,
				swap: "none",
			});
		}

		this.dragState = null;
	};

	private updateColumnOrders() {
		const columns = [...this.querySelectorAll("kanban-column")];
		columns.forEach((col, index) => {
			col.order = index;
		});
	}

	render() {
		return html`
      <div class="board-wrapper">
        <div class="board">
          <slot></slot>
        </div>

        <div class="create-column">
          <kanban-add-form
            @add-form-close=${() => (this.newColumnColor = DEFAULT_COLUMN_COLOR)}
          >
            <button slot="trigger" type="button" class="trigger">
              + Adicionar coluna
            </button>
            <form
              class="form"
              hx-post=${this.createColumnUrl}
              hx-target="host"
              hx-swap="beforeend"
            >
              <input type="hidden" name="board_id" .value=${String(this.boardId)} />
              <input
                type="text"
                name="title"
                class="field input"
                placeholder="Nome da coluna..."
                aria-label="Nome da coluna"
                required
                maxlength="100"
              />

              <div>
                <label class="color-label">Cor da Coluna</label>
                <kanban-color-picker
                  variant="form"
                  name="color"
                  .value=${this.newColumnColor}
                  @change=${(e: CustomEvent<{ value: string }>) =>
										(this.newColumnColor = e.detail.value)}
                ></kanban-color-picker>
              </div>

              <div class="actions">
                <button type="button" class="btn btn-secondary btn-cancel" data-add-form-cancel>
                  Cancelar
                </button>
                <button type="submit" class="btn btn-primary btn-submit">Adicionar</button>
              </div>
            </form>
          </kanban-add-form>
        </div>
      </div>
    `;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-board": KanbanBoard;
	}
}
