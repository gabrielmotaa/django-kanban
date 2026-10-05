import { css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { HtmxElement } from "../lib/htmx-element";
import { resolveLabels, watchLabels } from "../lib/labels";
import { reset } from "../styles/reset";
import type { DragState } from "./kanban-board";
import type { KanbanColumn } from "./kanban-column";

/** The front of a card: title and badges. Draggable; opens the dialog on click. */
@customElement("kanban-card")
export class KanbanCard extends HtmxElement {
	static styles = [
		reset,
		css`
      :host {
        display: block;
      }

      .card {
        background: var(--color-bg-card);
        border: var(--nb-border-sm);
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
        transform: translate(-1px, -1px);
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

      :host(:focus-visible) .card {
        outline: 2px solid var(--color-primary);
        outline-offset: 2px;
      }

      .labels {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        margin-bottom: 8px;
      }

      .badges {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 8px;
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

	@property({ attribute: "dialog-href" })
	dialogHref = "";

	@property({ attribute: "has-description", type: Boolean })
	hasDescription = false;

	@property()
	due = "";

	@property({ attribute: "due-status" })
	dueStatus = "";

	@property({ attribute: "due-label" })
	dueLabel = "";

	@property({ type: Boolean })
	completed = false;

	@property({ type: Number })
	comments = 0;

	@property({ attribute: "comments-label" })
	commentsLabel = "";

	@property({ attribute: "checklist-done", type: Number })
	checklistDone = 0;

	@property({ attribute: "checklist-total", type: Number })
	checklistTotal = 0;

	@property({ attribute: "checklist-status" })
	checklistStatus = "";

	@property({ attribute: "checklist-label" })
	checklistLabel = "";

	/** Ids of the attached labels ("3,5"); definitions come from the board. */
	@property()
	labels = "";

	private isDragging = false;

	override firstUpdated() {
		if (!this.title) {
			this.title = this.textContent?.trim() || "";
		}
	}

	override connectedCallback() {
		super.connectedCallback();

		this.draggable = true;
		this.tabIndex = 0;
		const { signal } = this;
		watchLabels(this, signal);
		this.addEventListener("dragstart", this.onDragStart, { signal });
		this.addEventListener("dragend", this.onDragEnd, { signal });
		this.addEventListener("click", this.onCardClick, { signal });
		this.addEventListener("keydown", this.onKeyDown, { signal });
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

	private openDialog() {
		this.dispatchEvent(
			new CustomEvent("kanban-card-open", {
				bubbles: true,
				composed: true,
				detail: { card: this },
			}),
		);
	}

	private onCardClick = () => {
		if (this.isDragging) return;
		this.openDialog();
	};

	private onKeyDown = (e: KeyboardEvent) => {
		if (e.key === "Enter" && e.target === this) this.openDialog();
	};

	override render() {
		const labels = resolveLabels(this, this.labels);
		return html`
      <div class="card">
        ${
					labels.length
						? html`<div class="labels">${labels.map(
								(label) => html`<kanban-label
                    name=${label.name}
                    color=${label.color}
                    fg=${label.fg}
                    color-name=${label.colorName}
                  ></kanban-label>`,
							)}</div>`
						: ""
				}
        <div class="title-view">${this.title}</div>
        ${
					this.hasDescription ||
					this.due ||
					this.checklistTotal ||
					this.comments
						? html`<div class="badges">
              ${this.hasDescription ? html`<kanban-badge icon="≡" label="Este card tem descrição"></kanban-badge>` : ""}
              ${this.due ? html`<kanban-due-badge due=${this.due} status=${this.dueStatus} label=${this.dueLabel}></kanban-due-badge>` : ""}
              ${
								this.checklistTotal
									? html`<kanban-badge
                      icon="☑"
                      text="${this.checklistDone}/${this.checklistTotal}"
                      label=${this.checklistLabel}
                      variant=${this.checklistStatus === "complete" ? "complete" : "neutral"}
                    ></kanban-badge>`
									: ""
							}
              ${this.comments ? html`<kanban-badge icon="💬" text=${String(this.comments)} label=${this.commentsLabel}></kanban-badge>` : ""}
            </div>`
						: ""
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
