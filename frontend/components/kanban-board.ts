import { css, html, LitElement } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { type Palette, readPalette } from "../lib/palette";
import { sendWebComponentsHeader } from "../lib/web-components-header";
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

@customElement("kanban-board")
export class KanbanBoard extends LitElement {
	@property({ type: Number, attribute: "board-id" })
	boardId = 0;

	dragState: DragState = null;

	private cleanupController?: AbortController;

	@state()
	private addingColumn = false;

	@state()
	private newColumnTitle = "";

	@state()
	private newColumnColor = "#64748b";

	@property({ attribute: "create-column-url" })
	createColumnUrl = "";

	colorChoices: Palette = [];

	static styles = css`
    input, button, select, textarea {
      font: inherit;
    }

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
    }

    .input {
      width: 100%;
      padding: 8px 12px;
      border: 1px solid var(--color-input-border);
      border-radius: var(--radius-md);
      font-size: var(--font-size-lg);
      margin-bottom: 12px;
      box-sizing: border-box;
      outline: none;
    }

    .input:focus {
      border-color: var(--color-primary);
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

    .color-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      margin-bottom: 16px;
    }

    .color-dot {
      width: 100%;
      aspect-ratio: 1;
      border-radius: 50%;
      border: 3px solid transparent;
      cursor: pointer;
      padding: 0;
      outline: none;
      transition: transform var(--transition-fast);
      background-color: var(--dot-color);
    }

    .color-dot:hover {
      transform: scale(1.1);
    }

    .color-dot--active {
      outline: 3px solid #000;
      outline-offset: -3px;
    }

    .actions {
      display: flex;
      gap: 8px;
      justify-content: flex-end;
    }

    .btn-submit,
    .btn-cancel {
      padding: 6px 12px;
      font-size: var(--font-size-base);
      font-weight: var(--font-weight-medium);
      border-radius: var(--radius-md);
      border: none;
      cursor: pointer;
      transition: background var(--transition-normal);
    }

    .btn-submit {
      background: var(--color-primary);
      color: white;
    }

    .btn-submit:hover {
      background: var(--color-primary-hover);
    }

    .btn-cancel {
      background: var(--color-text-muted);
      color: white;
    }

    .btn-cancel:hover {
      background: var(--color-text-light);
    }
  `;

	override connectedCallback() {
		super.connectedCallback();

		this.cleanupController = new AbortController();
		const { signal } = this.cleanupController;

		this.colorChoices = readPalette(this);
		sendWebComponentsHeader(this, signal);

		this.addEventListener(
			"kanban-card-dragstart",
			this.onCardDragStart as EventListener,
			{ signal },
		);
		this.addEventListener(
			"kanban-card-dragend",
			this.onCardDragEnd as EventListener,
			{ signal },
		);
		this.addEventListener(
			"kanban-column-dragstart",
			this.onColumnDragStart as EventListener,
			{ signal },
		);
		this.addEventListener(
			"kanban-column-dragend",
			this.onColumnDragEnd as EventListener,
			{ signal },
		);
		this.addEventListener("cardmove", this.onCardMove as EventListener, {
			signal,
		});
		this.addEventListener("columnmove", this.onColumnMove as EventListener, {
			signal,
		});
	}

	override disconnectedCallback() {
		super.disconnectedCallback();

		this.cleanupController?.abort();
	}

	override updated() {
		if (this.shadowRoot) {
			// biome-ignore lint: htmx.process() accepts ShadowRoot at runtime but TS types don't reflect it
			window.htmx.process(this.shadowRoot as any);
		}
	}

	private onCardDragStart = (e: CustomEvent) => {
		this.dragState = e.detail;
	};

	private onCardDragEnd = () => {
		this.dragState = null;
	};

	private onColumnDragStart = (e: CustomEvent) => {
		this.dragState = e.detail;
	};

	private onColumnDragEnd = () => {
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

	// Column Adding Handlers
	private onStartColumnAdd = () => {
		this.addingColumn = true;
		this.newColumnTitle = "";
		this.newColumnColor = "#64748b";
		this.updateComplete.then(() => {
			const input = this.shadowRoot?.querySelector(
				".input",
			) as HTMLInputElement;
			input?.focus();
		});
	};

	private onCancelColumnAdd = () => {
		this.addingColumn = false;
	};

	private onAddColumnSuccess = () => {
		this.addingColumn = false;
	};

	private onColumnKeyDown = (e: KeyboardEvent) => {
		if (e.key === "Escape") {
			this.addingColumn = false;
		}
	};

	render() {
		return html`
      <!-- board wrapper -->
      <div class="board-wrapper">
        <div class="board">
          <slot></slot>
        </div>

        <!-- Add Column Section -->
        <div class="create-column">
          ${
						this.addingColumn
							? html`
                <form
                  class="form"
                  hx-post=${this.createColumnUrl}
                  hx-target="host"
                  hx-swap="beforeend"
                  @htmx:after-request=${this.onAddColumnSuccess}
                >
                  <input type="hidden" name="board_id" .value=${this.boardId} />
                  <input
                    type="text"
                    name="title"
                    class="input"
                    placeholder="Nome da coluna..."
                    aria-label="Nome da coluna"
                    required
                    maxlength="100"
                    .value=${this.newColumnTitle}
                    @input=${(e: Event) => (this.newColumnTitle = (e.target as HTMLInputElement).value)}
                    @keydown=${this.onColumnKeyDown}
                  />
                  <input type="hidden" name="color" .value=${this.newColumnColor} />
                  
                  <div>
                    <label class="color-label">Cor da Coluna</label>
                    <div class="color-grid">
                      ${this.colorChoices.map(
												([color, name]) => html`
                        <button
                          type="button"
                          aria-label=${name}
                          class="color-dot ${this.newColumnColor === color ? "color-dot--active" : ""}"
                          style="--dot-color: ${color}"
                          @click=${() => (this.newColumnColor = color)}
                        ></button>
                      `,
											)}
                    </div>
                  </div>

                  <div class="actions">
                    <button type="button" class="btn-cancel" @click=${this.onCancelColumnAdd}>Cancelar</button>
                    <button type="submit" class="btn-submit">Adicionar</button>
                  </div>
                </form>
              `
							: html`
                <button class="trigger" @click=${this.onStartColumnAdd}>
                  + Adicionar coluna
                </button>
              `
					}
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
