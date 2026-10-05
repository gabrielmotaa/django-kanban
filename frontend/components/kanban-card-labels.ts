import { css, html, LitElement } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { applyServerElement } from "../lib/apply-server-element";
import { announceCardUpdate } from "../lib/card-update";
import { resolveLabels, watchLabels } from "../lib/labels";
import { reset } from "../styles/reset";

/**
 * Labels section of the card dialog: the card's pills, the "+" button and the
 * label popover. `card-labels="3,5"` holds the attached ids (resolved against
 * the board's registry); label responses are applied here and the card front
 * is announced to the board.
 */
@customElement("kanban-card-labels")
export class KanbanCardLabels extends LitElement {
	static styles = [
		reset,
		css`
      :host {
        display: block;
      }

      .section-title {
        margin: 0 0 8px;
        font-size: var(--font-size-base);
        font-weight: var(--font-weight-semibold);
        color: var(--color-text-light);
      }

      .row {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 6px;
      }

      .pills {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }

      .add {
        width: 28px;
        height: 28px;
        padding: 0;
        border: var(--nb-border-sm);
        border-radius: var(--radius-md);
        background: var(--color-bg-column);
        color: var(--color-text-secondary);
        font-size: 18px;
        line-height: 1;
        cursor: pointer;
      }

      .add:hover {
        background: var(--color-surface-hover);
      }
    `,
	];

	@property()
	href = "";

	@property({ attribute: "create-url" })
	createUrl = "";

	@property({ attribute: "board-id", type: Number })
	boardId = 0;

	@property({ attribute: "card-id", type: Number })
	cardId = 0;

	@property({ attribute: "card-labels" })
	cardLabels = "";

	@state()
	private open = false;

	private disposer = new AbortController();

	override connectedCallback() {
		super.connectedCallback();
		this.disposer = new AbortController();
		watchLabels(this, this.disposer.signal);
		this.addEventListener("keydown", this.onKeyDown, {
			signal: this.disposer.signal,
		});
	}

	override disconnectedCallback() {
		super.disconnectedCallback();
		this.disposer.abort();
	}

	private onKeyDown = (e: KeyboardEvent) => {
		if (e.key === "Escape" && this.open) {
			// Close the popover only: don't let the enclosing <dialog> close too.
			e.preventDefault();
			e.stopPropagation();
			this.open = false;
		}
	};

	private onSaved = (e: CustomEvent<{ html: string }>) => {
		e.stopPropagation();
		applyServerElement(this, e.detail.html);
		announceCardUpdate(this, e.detail.html);
	};

	override render() {
		const attached = resolveLabels(this, this.cardLabels);
		return html`
      <section>
        <h3 class="section-title">Etiquetas</h3>
        <div class="row">
          <div class="pills">
            ${attached.map(
							(label) => html`
                <kanban-label
                  name=${label.name}
                  color=${label.color}
                  fg=${label.fg}
                  color-name=${label.colorName}
                ></kanban-label>
              `,
						)}
          </div>
          <button
            type="button"
            class="add"
            aria-label="Adicionar etiqueta"
            aria-expanded=${this.open ? "true" : "false"}
            @click=${() => (this.open = !this.open)}
          >+</button>
        </div>
        ${
					this.open
						? html`
              <kanban-label-picker
                href=${this.href}
                create-url=${this.createUrl}
                board-id=${this.boardId}
                card-id=${this.cardId}
                .attached=${new Set(attached.map((l) => l.id))}
                @kanban-saved=${this.onSaved}
              ></kanban-label-picker>
            `
						: ""
				}
      </section>
    `;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-card-labels": KanbanCardLabels;
	}
}
