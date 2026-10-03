import { css, html, LitElement } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { announceCardUpdate } from "../lib/card-update";
import { htmxRequest } from "../lib/htmx-request";
import { buttons } from "../styles/buttons";
import { reset } from "../styles/reset";

/**
 * One checklist entry. The text is the element's text content, `done` is
 * "true" | "false". It owns its endpoint (`href`): toggling, editing the text
 * and removing PATCH/DELETE it, and the response (this item + the card front)
 * is applied here; the card front is announced to the board.
 */
@customElement("kanban-checklist-item")
export class KanbanChecklistItem extends LitElement {
	static styles = [
		reset,
		buttons,
		css`
      :host {
        display: block;
      }

      [hidden] {
        display: none !important;
      }

      .item {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      input[type="checkbox"] {
        margin: 0;
      }

      .text {
        flex-grow: 1;
        padding: 4px 8px;
        background: none;
        border: none;
        border-radius: var(--radius-md);
        font-size: var(--font-size-base);
        color: var(--color-text-primary);
        text-align: left;
        cursor: text;
        word-break: break-word;
      }

      .text:hover {
        background: var(--color-bg-column);
      }

      :host([done="true"]) .text {
        color: var(--color-text-muted);
        text-decoration: line-through;
      }

      form {
        display: flex;
        flex-grow: 1;
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

      .remove {
        padding: 2px 8px;
        background: none;
        border: none;
        border-radius: var(--radius-sm);
        font-size: 18px;
        line-height: 1;
        color: var(--color-text-muted);
        cursor: pointer;
      }

      .remove:hover {
        background: var(--color-bg-column);
        color: var(--color-danger);
      }
    `,
	];

	@property()
	href = "";

	@property({ reflect: true })
	done = "false";

	@state()
	private editing = false;

	@state()
	private text = "";

	override connectedCallback() {
		super.connectedCallback();
		this.setAttribute("role", "listitem");
		this.text = this.textContent?.trim() ?? "";
	}

	/** Applies the item element from a response and announces the card front. */
	private apply(responseHtml: string) {
		const template = document.createElement("template");
		template.innerHTML = responseHtml.trim();
		const incoming = template.content.querySelector(this.localName);
		if (incoming) {
			this.done = incoming.getAttribute("done") ?? this.done;
			this.text = incoming.textContent?.trim() ?? this.text;
			this.textContent = this.text;
		}
		announceCardUpdate(this, responseHtml);
	}

	private toggle = async (e: Event) => {
		const input = e.target as HTMLInputElement;
		const { successful, html } = await htmxRequest(this, "patch", this.href, {
			done: String(input.checked),
		});
		if (successful) this.apply(html);
		else input.checked = !input.checked;
	};

	private edit = () => {
		this.editing = true;
		this.updateComplete.then(() =>
			this.renderRoot.querySelector<HTMLInputElement>(".input")?.focus(),
		);
	};

	private cancel = () => {
		this.editing = false;
	};

	private onKeyDown = (e: KeyboardEvent) => {
		if (e.key === "Escape") {
			// Cancel the edit only: don't let the enclosing <dialog> close too.
			e.preventDefault();
			e.stopPropagation();
			this.cancel();
		}
	};

	private save = async (e: Event) => {
		e.preventDefault();
		const input = this.renderRoot.querySelector<HTMLInputElement>(".input");
		const { successful, html } = await htmxRequest(this, "patch", this.href, {
			text: input?.value ?? "",
		});
		if (!successful) return;
		this.apply(html);
		this.editing = false;
	};

	private remove_ = async () => {
		const { successful, html } = await htmxRequest(this, "delete", this.href);
		if (!successful) return;
		announceCardUpdate(this, html);
		this.remove();
	};

	override render() {
		return html`
      <div class="item">
        <input
          type="checkbox"
          aria-label=${this.text}
          .checked=${this.done === "true"}
          @change=${this.toggle}
        />
        <button type="button" class="text" ?hidden=${this.editing} @click=${this.edit}><slot></slot></button>
        ${
					this.editing
						? html`
              <form @submit=${this.save} @keydown=${this.onKeyDown}>
                <input
                  type="text"
                  class="input"
                  maxlength="200"
                  required
                  aria-label="Texto do item"
                  .value=${this.text}
                />
                <button type="submit" class="btn btn-primary">Salvar</button>
                <button type="button" class="btn btn-secondary" @click=${this.cancel}>Cancelar</button>
              </form>
            `
						: ""
				}
        <button type="button" class="remove" aria-label="Remover item" @click=${this.remove_}>×</button>
      </div>
    `;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-checklist-item": KanbanChecklistItem;
	}
}
