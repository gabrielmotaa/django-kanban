import { css, html, LitElement } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { applyServerElement } from "../lib/apply-server-element";
import { announceCardUpdate } from "../lib/card-update";
import { htmxRequest } from "../lib/htmx-request";
import { buttons } from "../styles/buttons";
import { reset } from "../styles/reset";
import type { KanbanInlineEdit } from "./kanban-inline-edit";

/**
 * A card checklist. Its items are light-DOM `<kanban-checklist-item>`
 * children and the progress is derived from them (no server-side counter to
 * keep in sync); only the card front comes back from the server and is
 * announced to the board.
 */
@customElement("kanban-checklist")
export class KanbanChecklist extends LitElement {
	static styles = [
		reset,
		buttons,
		css`
      :host {
        display: block;
      }

      .header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
      }

      kanban-inline-edit {
        flex-grow: 1;
        --btn-padding: 6px 12px;
        --btn-font-size: var(--font-size-base);
        --btn-radius: var(--radius-md);
      }

      kanban-inline-edit::part(form) {
        gap: 8px;
      }

      kanban-inline-edit::part(input) {
        padding: 6px 10px;
        border: 1px solid var(--color-input-border);
        border-radius: var(--radius-md);
        font-size: var(--font-size-base);
        outline: none;
      }

      kanban-inline-edit::part(input):focus {
        border-color: var(--color-primary);
      }

      .title {
        margin: 0;
        font-size: var(--font-size-base);
        font-weight: var(--font-weight-semibold);
        color: var(--color-text-light);
      }

      .title-btn {
        display: block;
        width: 100%;
        margin: 0;
        padding: 4px 8px;
        background: none;
        border: none;
        border-radius: var(--radius-md);
        color: inherit;
        text-align: left;
        cursor: text;
        word-break: break-word;
      }

      .title-btn:hover {
        background: var(--color-bg-column);
      }

      .delete {
        padding: 4px 8px;
        background: var(--color-bg-column);
        border: none;
        border-radius: var(--radius-md);
        font-size: var(--font-size-sm);
        color: var(--color-text-secondary);
        cursor: pointer;
      }

      .delete:hover {
        background: var(--color-border-hover);
      }

      .progress {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
      }

      .percent {
        min-width: 36px;
        font-size: var(--font-size-sm);
        color: var(--color-text-muted);
      }

      .bar {
        flex-grow: 1;
        height: 8px;
        border-radius: 4px;
        background: var(--color-border);
        overflow: hidden;
      }

      .fill {
        height: 100%;
        background: var(--color-primary);
        transition: width var(--transition-normal);
      }

      .items {
        display: flex;
        flex-direction: column;
        gap: 4px;
        margin: 0 0 8px;
      }

      .add {
        display: flex;
        align-items: center;
        gap: 8px;
        --btn-padding: 6px 12px;
        --btn-font-size: var(--font-size-base);
        --btn-radius: var(--radius-md);
      }

      .input {
        display: block;
        flex-grow: 1;
        min-width: 0;
        width: 100%;
        padding: 6px 10px;
        border: 1px solid var(--color-input-border);
        border-radius: var(--radius-md);
        font-size: var(--font-size-base);
        outline: none;
        box-sizing: border-box;
      }

      .input:focus {
        border-color: var(--color-primary);
      }
    `,
	];

	@property()
	title = "";

	@property()
	href = "";

	@property({ attribute: "items-url" })
	itemsUrl = "";

	@query("kanban-inline-edit")
	private titleEdit?: KanbanInlineEdit;

	@query(".add .input")
	private newItemInput?: HTMLInputElement;

	private observer = new MutationObserver(() => this.requestUpdate());

	override connectedCallback() {
		super.connectedCallback();
		this.observer.observe(this, {
			childList: true,
			attributes: true,
			attributeFilter: ["done"],
			subtree: true,
		});
	}

	override disconnectedCallback() {
		super.disconnectedCallback();
		this.observer.disconnect();
	}

	private get counts() {
		const items = [...this.querySelectorAll(":scope > kanban-checklist-item")];
		const done = items.filter((i) => i.getAttribute("done") === "true").length;
		// Round half up, like the server (`int(100 * done / total + 0.5)`).
		const percent = items.length
			? Math.floor((100 * done) / items.length + 0.5)
			: 0;
		return { done, total: items.length, percent };
	}

	private onTitleSaved = (e: CustomEvent<{ html: string }>) => {
		e.stopPropagation();
		applyServerElement(this, e.detail.html);
	};

	private onDelete = async () => {
		if (!confirm(`Excluir a checklist '${this.title}'?`)) return;
		const { successful, html } = await htmxRequest(this, "delete", this.href);
		if (!successful) return;
		announceCardUpdate(this, html);
		this.remove();
	};

	private onAddItem = async (e: Event) => {
		e.preventDefault();
		const input = this.newItemInput;
		if (!input || input.disabled) return;
		const text = input.value;
		input.disabled = true;
		const { successful, html } = await htmxRequest(
			this,
			"post",
			this.itemsUrl,
			{ text },
		);
		input.disabled = false;
		if (!successful) {
			input.focus();
			return;
		}
		const template = document.createElement("template");
		template.innerHTML = html.trim();
		const item = template.content.querySelector("kanban-checklist-item");
		if (item) this.append(item);
		announceCardUpdate(this, html);
		input.value = "";
		input.focus();
	};

	override render() {
		const { percent } = this.counts;
		return html`
      <section aria-label=${this.title}>
        <div class="header">
          <kanban-inline-edit
            href=${this.href}
            name="title"
            label="Título do checklist"
            maxlength="100"
            value=${this.title}
            @kanban-saved=${this.onTitleSaved}
          >
            <h3 class="title">
              <button type="button" class="title-btn" @click=${() => this.titleEdit?.edit()}>${this.title}</button>
            </h3>
          </kanban-inline-edit>
          <button type="button" class="delete" @click=${this.onDelete}>Excluir</button>
        </div>
        <div class="progress">
          <span class="percent">${percent}%</span>
          <div
            class="bar"
            role="progressbar"
            aria-label="Progresso de ${this.title}"
            aria-valuemin="0"
            aria-valuemax="100"
            aria-valuenow=${percent}
          ><div class="fill" style="width: ${percent}%;"></div></div>
        </div>
        <div class="items" role="list"><slot></slot></div>
        <form class="add" @submit=${this.onAddItem}>
          <input
            type="text"
            class="input"
            maxlength="200"
            required
            placeholder="Adicionar um item"
            aria-label="Adicionar um item"
          />
          <button type="submit" class="btn btn-primary">Adicionar</button>
        </form>
      </section>
    `;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-checklist": KanbanChecklist;
	}
}
