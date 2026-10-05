import { css, html, type PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { applyCardUpdate } from "../lib/card-update";
import { HtmxElement } from "../lib/htmx-element";
import { htmxRequest } from "../lib/htmx-request";
import type { LabelDef } from "../lib/labels";
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
        border: var(--nb-border);
        box-shadow: var(--shadow-md);
        border-radius: var(--radius-lg);
        padding: 12px 18px;
        font-weight: var(--font-weight-bold);
        color: var(--color-text-primary);
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
        border: var(--nb-border-sm);
        width: 280px;
        box-sizing: border-box;
        --field-padding: 8px 12px;
        --btn-padding: 6px 12px;
        --btn-font-size: var(--font-size-base);
        --btn-radius: var(--radius-md);
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

	/** Label registry (definitions in label order), served as JSON by the server. */
	@property({
		converter: {
			fromAttribute: (value: string | null): LabelDef[] =>
				value ? JSON.parse(value) : [],
		},
	})
	labels: LabelDef[] = [];

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
		this.addEventListener(
			"kanban-card-updated",
			this.onCardUpdated as EventListener,
			{ signal },
		);
		this.addEventListener(
			"kanban-card-open",
			this.onCardOpen as EventListener,
			{ signal },
		);
		this.addEventListener("cardmove", this.onCardMove as EventListener, {
			signal,
		});
		this.addEventListener("columnmove", this.onColumnMove as EventListener, {
			signal,
		});
	}

	protected override updated(changed: PropertyValues) {
		super.updated(changed);
		if (changed.has("labels")) {
			this.dispatchEvent(new CustomEvent("kanban-labels-changed"));
		}
	}

	private onDragStart = (e: CustomEvent) => {
		this.dragState = e.detail;
	};

	private onDragEnd = () => {
		this.dragState = null;
	};

	// The dialog is loaded on demand into a host inside the board's shadow root.
	private onCardOpen = (e: CustomEvent<{ card: KanbanCard }>) => {
		void this.openDialog(e.detail.card);
	};

	private onCardUpdated = (e: CustomEvent<{ html: string }>) => {
		e.stopPropagation();
		applyCardUpdate(this, e.detail.html);
	};

	private dialogRequest = 0;

	private async openDialog(card: KanbanCard) {
		const request = ++this.dialogRequest;
		const { successful, html } = await htmxRequest(
			card,
			"get",
			card.dialogHref,
		);
		const host = this.renderRoot.querySelector(".dialog-host");
		// Ignore stale responses (double click) and a dialog that is already open.
		if (!successful || !host || request !== this.dialogRequest) return;
		host.innerHTML = html;
		host.querySelector("kanban-card-dialog")?.open(card);
	}

	private onCardMove = (e: CustomEvent<CardMoveDetail>) => {
		void this.moveCard(e.detail);
	};

	private async moveCard({ href, column_id, order }: CardMoveDetail) {
		const state = this.dragState;
		this.dragState = null;
		if (state?.type !== "card") return;

		const toColumn = state.card.closest("kanban-column");
		const { successful } = await htmxRequest(state.card, "patch", href, {
			column_id: String(column_id),
			order: String(order),
		});
		if (successful) return;

		// Roll the optimistic move back to where the card came from.
		const { card, fromColumn, fromIndex } = state;
		const siblings = [...fromColumn.querySelectorAll("kanban-card")].filter(
			(c) => c !== card,
		);
		fromColumn.insertBefore(card, siblings[fromIndex] ?? null);
		fromColumn.updateOrders();
		toColumn?.updateOrders();
	}

	private onColumnMove = (e: CustomEvent) => {
		void this.moveColumn(e.detail);
	};

	private async moveColumn({
		href,
		order,
		fromIndex,
	}: {
		href: string;
		order: number;
		fromIndex: number;
	}) {
		const state = this.dragState;
		this.dragState = null;
		this.updateColumnOrders();
		if (state?.type !== "column" || fromIndex === order) return;

		const { successful } = await htmxRequest(state.column, "patch", href, {
			order: String(order),
		});
		if (successful) return;

		const siblings = [...this.querySelectorAll("kanban-column")].filter(
			(c) => c !== state.column,
		);
		this.insertBefore(state.column, siblings[state.fromIndex] ?? null);
		this.updateColumnOrders();
	}

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
      <div class="dialog-host"></div>
    `;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-board": KanbanBoard;
	}
}
