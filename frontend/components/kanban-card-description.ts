import { css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { announceCardUpdate } from "../lib/card-update";
import { HtmxElement } from "../lib/htmx-element";
import { reset } from "../styles/reset";

/**
 * Description section of the card dialog. The text is the element's text
 * content (line breaks preserved, no Markdown); it PATCHes `href` itself and
 * keeps the response's text. Saving also refreshes the card front: the
 * response carries the card out-of-band and htmx applies it.
 */
@customElement("kanban-card-description")
export class KanbanCardDescription extends HtmxElement {
	static styles = [
		reset,
		css`
      :host {
        display: block;
      }

      [hidden] {
        display: none !important;
      }

      .section-title {
        margin: 0 0 8px;
        font-size: var(--font-size-base);
        font-weight: var(--font-weight-semibold);
        color: var(--color-text-light);
      }

      .view {
        display: block;
        width: 100%;
        min-height: 56px;
        padding: 8px 12px;
        background: var(--color-bg-column);
        border: var(--nb-border-sm);
        border-radius: var(--radius-md);
        font-size: var(--font-size-base);
        color: var(--color-text-primary);
        text-align: left;
        white-space: pre-wrap;
        word-break: break-word;
        cursor: pointer;
      }

      .view:hover {
        background: var(--color-surface-hover);
      }

      .view--empty {
        color: var(--color-text-muted);
      }

      .input {
        display: block;
        width: 100%;
        min-height: 96px;
        padding: 8px 12px;
        border: var(--nb-border-sm);
        border-radius: var(--radius-md);
        font-size: var(--font-size-base);
        outline: none;
        box-sizing: border-box;
        resize: vertical;
      }

      .input:focus {
        box-shadow: var(--shadow-sm);
      }

      .actions {
        display: flex;
        gap: 8px;
        margin-top: 8px;
      }

      .btn {
        padding: 6px 12px;
        border: var(--nb-border-sm);
        box-shadow: var(--shadow-sm);
        border-radius: var(--radius-md);
        font-size: var(--font-size-base);
        font-weight: var(--font-weight-bold);
        cursor: pointer;
        transition: background var(--transition-normal), transform var(--transition-fast), box-shadow var(--transition-fast);
      }

      .btn:active {
        transform: var(--nb-press);
        box-shadow: none;
      }

      .btn--primary {
        background: var(--color-primary);
        color: var(--color-on-accent);
      }

      .btn--primary:hover {
        background: var(--color-primary-hover);
      }

      .btn--secondary {
        background: var(--color-surface-muted);
        color: var(--color-text-light);
      }

      .btn--secondary:hover {
        background: var(--color-surface-hover);
      }
    `,
	];

	@property()
	href = "";

	@state()
	private editing = false;

	@state()
	private text = "";

	override connectedCallback() {
		super.connectedCallback();
		this.text = this.textContent ?? "";
	}

	private edit = () => {
		this.editing = true;
		this.focusAfterRender(".input");
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

	private onAfterRequest = (e: CustomEvent) => {
		const { successful, xhr } = e.detail;
		if (!successful) return;
		const template = document.createElement("template");
		template.innerHTML = xhr.responseText.trim();
		const incoming = template.content.querySelector(this.localName);
		this.text = incoming?.textContent ?? "";
		this.textContent = this.text;
		this.editing = false;
		announceCardUpdate(this, xhr.responseText);
	};

	override render() {
		return html`
      <section>
        <h3 class="section-title">Descrição</h3>
        <button
          type="button"
          class="view"
          ?hidden=${this.editing || !this.text}
          @click=${this.edit}
        ><slot></slot></button>
        <button
          type="button"
          class="view view--empty"
          ?hidden=${this.editing || !!this.text}
          @click=${this.edit}
        >Adicione uma descrição mais detalhada…</button>
        ${
					this.editing
						? html`
              <form
                hx-patch=${this.href}
                hx-swap="none"
                @htmx:after-request=${this.onAfterRequest}
                @keydown=${this.onKeyDown}
              >
                <textarea
                  class="input"
                  name="description"
                  rows="4"
                  maxlength="5000"
                  aria-label="Descrição"
                  .value=${this.text}
                ></textarea>
                <div class="actions">
                  <button type="submit" class="btn btn--primary">Salvar</button>
                  <button type="button" class="btn btn--secondary" @click=${this.cancel}>Cancelar</button>
                </div>
              </form>
            `
						: ""
				}
      </section>
    `;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-card-description": KanbanCardDescription;
	}
}
