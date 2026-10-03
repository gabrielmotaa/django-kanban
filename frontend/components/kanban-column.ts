import { css, html, LitElement } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { KanbanBoard } from "./kanban-board";
import type { KanbanCard } from "./kanban-card";

@customElement("kanban-column")
export class KanbanColumn extends LitElement {
	static styles = css`
    input, button, select, textarea {
      font: inherit;
    }

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

    .header-bg {
      background-color: var(--column-color, var(--color-text-muted));
      color: var(--column-fg, #ffffff);
      padding: 12px 16px;
      border-top-left-radius: var(--radius-xl);
      border-top-right-radius: var(--radius-xl);
      transition: background-color var(--transition-normal);
    }

    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      position: relative;
    }

    .title-text {
      font-size: var(--font-size-lg);
      font-weight: var(--font-weight-semibold);
      color: inherit;
      padding: 4px 0;
      flex-grow: 1;
      cursor: grab;
      user-select: none;
    }

    .title-text:active {
      cursor: grabbing;
    }

    .menu-wrapper {
      position: relative;
      display: inline-block;
    }

    .menu-trigger {
      background: none;
      border: none;
      font-size: 18px;
      font-weight: var(--font-weight-bold);
      cursor: pointer;
      color: inherit;
      padding: 4px 8px;
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      justify-content: center;
      line-height: 1;
      transition: background-color var(--transition-normal), opacity var(--transition-normal);
      opacity: 0.85;
    }

    .menu-trigger:hover {
      background-color: rgba(0, 0, 0, 0.08);
      opacity: 1;
    }

    .menu-dropdown {
      position: absolute;
      right: 0;
      top: 100%;
      margin-top: 4px;
      background: white;
      border: 1px solid var(--color-border);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-dropdown);
      z-index: 100;
      min-width: 160px;
      padding: 6px 0;
    }

    .menu-btn {
      display: flex;
      align-items: center;
      gap: 8px;
      width: 100%;
      text-align: left;
      padding: 8px 12px;
      background: none;
      border: none;
      cursor: pointer;
      font-size: var(--font-size-base);
      color: var(--color-text-secondary);
      font-family: inherit;
      transition: background var(--transition-normal);
    }

    .menu-btn:hover {
      background: var(--color-bg-body);
    }

    .menu-btn--danger {
      color: var(--color-danger);
    }

    .menu-btn--danger:hover {
      background: #fef2f2;
    }

    .menu-divider {
      border-top: 1px solid var(--color-border);
      margin: 6px 0;
    }

    .menu-section-title {
      font-size: var(--font-size-xs);
      color: var(--color-text-muted);
      font-weight: var(--font-weight-semibold);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 8px;
      padding: 0 12px;
    }

    .color-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 6px;
      padding: 0 12px;
    }

    .color-dot {
      width: 22px;
      height: 22px;
      border-radius: 50%;
      border: 2px solid transparent;
      cursor: pointer;
      padding: 0;
      transition: transform var(--transition-fast);
      background-color: var(--dot-color);
    }

    .color-dot:hover {
      transform: scale(1.15);
    }

    .color-dot--active {
      border-color: var(--color-text-secondary);
    }

    .edit-form {
      display: flex;
      gap: 6px;
      align-items: center;
      width: 100%;
    }

    .edit-input {
      flex-grow: 1;
      min-width: 0;
      padding: 6px 10px;
      border: 1.5px solid rgba(255, 255, 255, 0.3);
      border-radius: var(--radius-md);
      font-size: var(--font-size-lg);
      outline: none;
      background-color: rgba(255, 255, 255, 0.2);
      color: inherit;
      font-weight: var(--font-weight-medium);
      transition: background-color var(--transition-normal), border-color var(--transition-normal);
    }

    .edit-input:focus {
      background-color: white;
      color: var(--color-text-primary);
      border-color: white;
    }

    .edit-btn-save,
    .edit-btn-cancel {
      flex-shrink: 0;
      padding: 6px 10px;
      border: none;
      border-radius: var(--radius-md);
      cursor: pointer;
      font-size: var(--font-size-base);
      font-weight: var(--font-weight-semibold);
      transition: opacity var(--transition-normal), transform var(--transition-fast);
    }

    .edit-btn-save:hover,
    .edit-btn-cancel:hover {
      opacity: 0.9;
    }

    .edit-btn-save {
      background-color: white;
      color: var(--column-color, var(--color-text-muted));
    }

    .edit-btn-cancel {
      background-color: rgba(0, 0, 0, 0.15);
      color: inherit;
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

    .add-card-input {
      width: 100%;
      padding: 8px;
      border: 1px solid var(--color-input-border);
      border-radius: var(--radius-md);
      font-size: var(--font-size-lg);
      outline: none;
      box-sizing: border-box;
    }

    .add-card-input:focus {
      border-color: var(--color-primary);
    }

    .add-card-actions {
      display: flex;
      justify-content: flex-end;
      gap: 6px;
    }

    .add-card-submit,
    .add-card-cancel {
      padding: 6px 10px;
      font-size: var(--font-size-md);
      font-weight: var(--font-weight-medium);
      border-radius: var(--radius-sm);
      border: none;
      cursor: pointer;
      transition: background var(--transition-normal);
    }

    .add-card-submit {
      background: var(--color-primary);
      color: white;
    }

    .add-card-submit:hover {
      background: var(--color-primary-hover);
    }

    .add-card-cancel {
      background: var(--color-border);
      color: var(--color-text-light);
    }

    .add-card-cancel:hover {
      background: var(--color-border-hover);
    }

    ::slotted(kanban-card) {
      display: block;
    }
  `;

	@property({ attribute: "column-id", type: Number })
	columnId = 0;

	@property()
	title = "";

	@property()
	color = "#64748b";

	@property({ type: Number, reflect: true })
	order = 0;

	@state()
	private editingTitle = false;

	@state()
	private menuOpen = false;

	@state()
	private addingCard = false;

	private cleanupController?: AbortController;

	colorChoices = window.colorChoices;

	get fgColor(): string {
		const map: Record<string, string> = {
			"#f59e0b": "#1e293b",
		};
		return map[this.color] || "#ffffff";
	}

	get editUrl(): string {
		return window.urls.columnDetail.replace("/0/", `/${this.columnId}/`);
	}

	get deleteUrl(): string {
		return window.urls.columnDetail.replace("/0/", `/${this.columnId}/`);
	}

	get createCardUrl(): string {
		return window.urls.cardCreate;
	}

	override connectedCallback() {
		super.connectedCallback();

		this.cleanupController = new AbortController();
		const { signal } = this.cleanupController;

		this.addEventListener("dragenter", this.onDragEnter, { signal });
		this.addEventListener("dragleave", this.onDragLeave, { signal });
		this.addEventListener("dragover", this.onDragOver, { signal });
		this.addEventListener("drop", this.onDrop, { signal });

		// Column dragging listeners
		this.addEventListener("dragstart", this.onColumnDragStart, { signal });
		this.addEventListener("dragend", this.onColumnDragEnd, { signal });

		// Document click to close menu on click away
		document.addEventListener("click", this.onDocumentClick, { signal });
	}

	override disconnectedCallback() {
		super.disconnectedCallback();
		this.cleanupController?.abort();
	}

	private get board(): KanbanBoard {
		return this.closest("kanban-board") as KanbanBoard;
	}

	private get dragState() {
		return this.board.dragState;
	}

	updateOrders() {
		const cards = [...this.querySelectorAll("kanban-card")];
		cards.forEach((card, index) => {
			card.order = index;
		});
	}

	private onDragEnter = () => {
		if (this.dragState?.type !== "card") return;
		this.classList.add("drag-over");
	};

	private onDragLeave = (e: DragEvent) => {
		if (this.dragState?.type !== "card") return;
		if (!this.contains(e.relatedTarget as Node)) {
			this.classList.remove("drag-over");
		}
	};

	private onDragOver = (e: DragEvent) => {
		e.preventDefault();

		const state = this.dragState;
		if (!state) return;

		if (state.type === "card") {
			const after = this.getCardAfterPosition(e.clientY);

			if (!after) {
				this.appendChild(state.card);
			} else {
				this.insertBefore(state.card, after);
			}
		} else if (state.type === "column") {
			const draggedCol = state.column;
			if (draggedCol === this) return;

			const box = this.getBoundingClientRect();
			const mouseX = e.clientX;
			const middleX = box.left + box.width / 2;
			const board = this.board;

			if (mouseX < middleX) {
				board.insertBefore(draggedCol, this);
			} else {
				board.insertBefore(draggedCol, this.nextElementSibling);
			}
		}
	};

	private onDrop = () => {
		this.classList.remove("drag-over");

		const state = this.board.dragState;
		if (!state) return;

		if (state.type === "card") {
			const cards = [...this.querySelectorAll("kanban-card")];
			const toIndex = cards.indexOf(state.card);

			if (state.fromColumn === this && state.fromIndex === toIndex) {
				return;
			}

			if (state.fromColumn !== this) {
				state.fromColumn.updateOrders();
				this.updateOrders();
			} else {
				this.updateOrders();
			}

			this.dispatchEvent(
				new CustomEvent("cardmove", {
					bubbles: true,
					composed: true,
					detail: {
						card_id: state.card.cardId,
						column_id: this.columnId,
						order: toIndex,
					},
				}),
			);
		} else if (state.type === "column") {
			const column = state.column;
			const columns = [...this.board.querySelectorAll("kanban-column")];
			const toIndex = columns.indexOf(column);

			this.dispatchEvent(
				new CustomEvent("columnmove", {
					bubbles: true,
					composed: true,
					detail: {
						column_id: column.columnId,
						order: toIndex,
						fromIndex: state.fromIndex,
					},
				}),
			);
		}
	};

	private getCardAfterPosition(mouseY: number): Element | null {
		const cards = [
			...this.querySelectorAll<KanbanCard>("kanban-card:not(.dragging)"),
		];

		let closest: Element | null = null;
		let closestOffset = Number.NEGATIVE_INFINITY;

		for (const card of cards) {
			const box = card.getBoundingClientRect();
			const offset = mouseY - box.top - box.height / 2;

			if (offset < 0 && offset > closestOffset) {
				closestOffset = offset;
				closest = card;
			}
		}

		return closest;
	}

	override updated() {
		this.setAttribute("role", "group");
		this.setAttribute("aria-label", this.title);
		if (this.shadowRoot) {
			// biome-ignore lint/suspicious/noExplicitAny: htmx.process() accepts ShadowRoot at runtime but TS types don't reflect it
			window.htmx.process(this.shadowRoot as any);
		}
	}

	// Column Drag Handlers
	private onTitleMouseDown = () => {
		this.draggable = true;
	};

	private onTitleMouseUp = () => {
		this.draggable = false;
	};

	private onColumnDragStart = (e: DragEvent) => {
		if (e.target !== this) return;

		const columns = [...this.board.querySelectorAll("kanban-column")];
		const index = columns.indexOf(this);

		this.dispatchEvent(
			new CustomEvent("kanban-column-dragstart", {
				bubbles: true,
				composed: true,
				detail: {
					type: "column",
					column: this,
					fromIndex: index,
				},
			}),
		);

		requestAnimationFrame(() => this.classList.add("dragging-col"));
	};

	private onColumnDragEnd = () => {
		this.classList.remove("dragging-col");
		this.removeAttribute("draggable");

		this.dispatchEvent(
			new CustomEvent("kanban-column-dragend", {
				bubbles: true,
				composed: true,
			}),
		);
	};

	// Document Click Away Menu Handler
	private onDocumentClick = (e: MouseEvent) => {
		if (this.menuOpen) {
			const path = e.composedPath();
			const trigger = this.shadowRoot?.querySelector(".menu-trigger");
			const dropdown = this.shadowRoot?.querySelector(".menu-dropdown");
			if (
				trigger &&
				!path.includes(trigger) &&
				dropdown &&
				!path.includes(dropdown)
			) {
				this.menuOpen = false;
			}
		}
	};

	private onRenameCancel = (e: Event) => {
		e.preventDefault();
		e.stopPropagation();
		this.editingTitle = false;
	};

	private onAddCardSuccess = () => {
		this.addingCard = false;
	};

	override render() {
		return html`
      <div class="header-bg" style="--column-color: ${this.color}; --column-fg: ${this.fgColor};">
        <div class="title">
          ${
						this.editingTitle
							? html`
                <form class="edit-form" hx-patch=${this.editUrl} hx-target="host" hx-swap="outerHTML">
                  <input
                    type="text"
                    name="title"
                    aria-label="Nome da coluna"
                    class="edit-input"
                    .value=${this.title}
                    required
                  />
                  <input type="hidden" name="color" .value=${this.color} />
                  <button type="submit" class="edit-btn-save" aria-label="Salvar nome">✓</button>
                  <button type="button" class="edit-btn-cancel" aria-label="Cancelar edição" @click=${this.onRenameCancel}>✗</button>
                </form>
              `
							: html`
                <div class="header">
                  <span
                    class="title-text"
                    @mousedown=${this.onTitleMouseDown}
                    @mouseup=${this.onTitleMouseUp}
                  >
                    ${this.title}
                  </span>
                  
                  <div class="menu-wrapper">
                    <button
                      type="button"
                      class="menu-trigger"
                      aria-label="Opções da coluna"
                      @click=${() => (this.menuOpen = !this.menuOpen)}
                    >
                      ⋮
                    </button>
                    
                    ${
											this.menuOpen
												? html`
                          <div class="menu-dropdown">
                            <button
                              type="button"
                              class="menu-btn"
                              @click=${() => {
																this.editingTitle = true;
																this.menuOpen = false;
																this.updateComplete.then(() => {
																	const input = this.shadowRoot?.querySelector(
																		".edit-input",
																	) as HTMLInputElement;
																	input?.focus();
																});
															}}
                            >
                              Editar nome
                            </button>
                            
                            <div class="menu-divider"></div>
                            
                            <div>
                              <div class="menu-section-title">Cor da Coluna</div>
                              <div class="color-grid">
                                ${this.colorChoices.map(
																	([hex, name]) => html`
                                    <button
                                      type="button"
                                      title=${name}
                                      class="color-dot ${this.color === hex ? "color-dot--active" : ""}"
                                      style="--dot-color: ${hex};"
                                      hx-patch=${this.editUrl}
                                      hx-vals='{"color": "${hex}", "title": "${this.title}"}'
                                      hx-target="host"
                                      hx-swap="outerHTML"
                                    ></button>
                                `,
																)}
                              </div>
                            </div>
                            
                            <div class="menu-divider"></div>
                            
                            <button
                              type="button"
                              class="menu-btn menu-btn--danger"
                              hx-delete=${this.deleteUrl}
                              hx-target="host"
                              hx-swap="outerHTML"
                              hx-confirm="Deseja realmente apagar a coluna '${this.title}' e todos os seus cards?"
                            >
                              Apagar coluna
                            </button>
                          </div>
                        `
												: ""
										}
                  </div>
                </div>
              `
					}
        </div>
      </div>
      
      <div class="body">
        <div class="cards">
          <slot></slot>
        </div>
        
        <div>
          ${
						this.addingCard
							? html`
                <form class="add-card-form" hx-post=${this.createCardUrl} hx-target="host" hx-swap="beforeend" @htmx:after-request=${this.onAddCardSuccess}>
                  <input type="hidden" name="column_id" .value=${this.columnId} />
                  <input
                    type="text"
                    name="title"
                    class="add-card-input"
                    placeholder="Título do card..."
                    aria-label="Título do card"
                    required
                    maxlength="200"
                    @keydown=${(e: KeyboardEvent) => {
											if (e.key === "Escape") this.addingCard = false;
										}}
                  />
                  <div class="add-card-actions">
                    <button
                      type="button"
                      class="add-card-cancel"
                      @click=${() => (this.addingCard = false)}
                    >
                      Cancelar
                    </button>
                    <button type="submit" class="add-card-submit">
                      Adicionar
                    </button>
                  </div>
                </form>
              `
							: html`
                <button
                  class="add-card-trigger"
                  @click=${() => {
										this.addingCard = true;
										this.updateComplete.then(() => {
											const input = this.shadowRoot?.querySelector(
												".add-card-input",
											) as HTMLInputElement;
											input?.focus();
										});
									}}
                >
                  + Adicionar card
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
		"kanban-column": KanbanColumn;
	}
}
