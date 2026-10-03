import { css, html } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { applyServerElement } from "../lib/apply-server-element";
import { HtmxElement } from "../lib/htmx-element";
import { reset } from "../styles/reset";
import type { KanbanInlineEdit } from "./kanban-inline-edit";

/** The board heading, renamed in place through `<kanban-inline-edit>`. */
@customElement("kanban-board-title")
export class KanbanBoardTitle extends HtmxElement {
	static styles = [
		reset,
		css`
      :host {
        display: block;
      }

      .board-header {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
        min-height: 48px;
      }

      kanban-inline-edit {
        --btn-padding: 8px 16px;
        --btn-font-size: var(--font-size-base);
        --btn-radius: var(--radius-md);
        --btn-secondary-hover-bg: var(--color-border-hover);
      }

      kanban-inline-edit::part(form) {
        gap: 8px;
        width: auto;
      }

      kanban-inline-edit::part(input) {
        flex-grow: 0;
        font-size: var(--font-size-xl);
        font-weight: var(--font-weight-semibold);
        padding: 6px 12px;
        border: 2px solid var(--color-input-border);
        border-radius: var(--radius-md);
        outline: none;
        color: var(--color-text-primary);
        background: var(--color-bg-column);
        transition: border-color var(--transition-normal);
      }

      kanban-inline-edit::part(input):focus {
        border-color: var(--color-primary);
      }

      .view {
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .title {
        font-size: var(--font-size-xxl);
        font-weight: var(--font-weight-bold);
        color: var(--color-text-primary);
        margin: 0;
        letter-spacing: -0.025em;
      }

      .edit-btn {
        background: var(--color-bg-column);
        border: none;
        cursor: pointer;
        padding: 8px;
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background var(--transition-normal), transform var(--transition-fast);
      }

      .edit-btn:hover {
        background: var(--color-border-hover);
        transform: scale(1.05);
      }

      .edit-btn svg {
        fill: var(--color-text-primary);
      }
    `,
	];

	@property({ type: Number, attribute: "board-id" })
	boardId = 0;

	@property({ type: String, reflect: true })
	title = "";

	@property()
	href = "";

	@query("kanban-inline-edit")
	private inlineEdit?: KanbanInlineEdit;

	private onSaved = (e: CustomEvent<{ html: string }>) => {
		e.stopPropagation();
		applyServerElement(this, e.detail.html);
	};

	override render() {
		return html`
      <div class="board-header">
        <kanban-inline-edit
          href=${this.href}
          name="title"
          label="Título do quadro"
          maxlength="100"
          value=${this.title}
          @kanban-saved=${this.onSaved}
        >
          <div class="view">
            <h1 class="title">${this.title}</h1>
            <button
              type="button"
              @click=${() => this.inlineEdit?.edit()}
              class="edit-btn"
              title="Editar título do quadro"
            >
              <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px">
                <path d="M200-200h57l391-391-57-57-391 391v57Zm-80 80v-170l528-527q12-11 26.5-17t30.5-6q16 0 31 6t26 18l55 56q12 11 17.5 26t5.5 30q0 16-5.5 30.5T817-647L290-120H120Zm640-584-56-56 56 56Zm-141 85-28-29 57 57-29-28Z"/>
              </svg>
            </button>
          </div>
        </kanban-inline-edit>
      </div>
    `;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-board-title": KanbanBoardTitle;
	}
}
