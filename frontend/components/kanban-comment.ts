import { css, html, LitElement } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { announceCardUpdate } from "../lib/card-update";
import { htmxRequest } from "../lib/htmx-request";
import { reset } from "../styles/reset";

/**
 * A comment. The text is the element's text content; it owns its endpoint
 * (`href`) for editing and deleting. The author is the fixed label "Você"
 * (the app has no authentication) and `created` is formatted by the server.
 */
@customElement("kanban-comment")
export class KanbanComment extends LitElement {
	static styles = [
		reset,
		css`
      :host {
        display: block;
        padding: 8px 12px;
        border: 1px solid var(--color-border);
        border-radius: var(--radius-md);
      }

      [hidden] {
        display: none !important;
      }

      .meta {
        margin: 0 0 4px;
        font-size: var(--font-size-sm);
        color: var(--color-text-muted);
      }

      .meta strong {
        color: var(--color-text-primary);
        font-weight: bold;
      }

      .text {
        margin: 0;
        font-size: var(--font-size-base);
        white-space: pre-wrap;
        word-break: break-word;
        text-wrap: pretty;
        overflow-wrap: break-word;
      }

      .actions {
        display: flex;
        gap: 8px;
        margin-top: 4px;
      }

      .action {
        padding: 0;
        border: none;
        background: none;
        font-size: var(--font-size-sm);
        color: var(--color-text-muted);
        text-decoration: underline;
        cursor: pointer;
      }

      .action:hover {
        color: var(--color-text-primary);
      }

      form {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
      }

      .input {
        display: block;
        width: 100%;
        min-height: 56px;
        padding: 8px 12px;
        border: 1px solid var(--color-input-border);
        border-radius: var(--radius-md);
        font-size: var(--font-size-base);
        outline: none;
        box-sizing: border-box;
        resize: vertical;
      }

      .input:focus {
        border-color: var(--color-primary);
      }

      .buttons {
        display: flex;
        gap: 8px;
        margin-top: 8px;
      }

      .btn {
        padding: 6px 12px;
        border: none;
        border-radius: var(--radius-md);
        font-size: var(--font-size-base);
        font-weight: var(--font-weight-medium);
        cursor: pointer;
        transition: background var(--transition-normal);
      }

      .btn--primary {
        background: var(--color-primary);
        color: white;
      }

      .btn--primary:hover {
        background: var(--color-primary-hover);
      }

      .btn--secondary {
        background: var(--color-border);
        color: var(--color-text-light);
      }

      .btn--secondary:hover {
        background: var(--color-border-hover);
      }
    `,
	];

	@property()
	href = "";

	@property()
	created = "";

	@state()
	private editing = false;

	@state()
	private text = "";

	override connectedCallback() {
		super.connectedCallback();
		this.setAttribute("role", "listitem");
		this.text = this.textContent ?? "";
	}

	private edit = () => {
		this.editing = true;
		this.updateComplete.then(() =>
			this.renderRoot.querySelector<HTMLTextAreaElement>(".input")?.focus(),
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
		const input = this.renderRoot.querySelector<HTMLTextAreaElement>(".input");
		const { successful, html } = await htmxRequest(this, "patch", this.href, {
			text: input?.value ?? "",
		});
		if (!successful) return;
		const template = document.createElement("template");
		template.innerHTML = html.trim();
		const incoming = template.content.querySelector(this.localName);
		this.text = incoming?.textContent ?? this.text;
		this.textContent = this.text;
		this.editing = false;
	};

	private delete_ = async () => {
		if (!confirm("Excluir comentário?")) return;
		const { successful, html } = await htmxRequest(this, "delete", this.href);
		if (!successful) return;
		announceCardUpdate(this, html);
		this.remove();
	};

	override render() {
		return html`
      <p class="meta"><strong>Você</strong> <span>${this.created}</span></p>
      <div ?hidden=${this.editing}>
        <p class="text"><slot></slot></p>
        <div class="actions">
          <button type="button" class="action" aria-label="Editar comentário" @click=${this.edit}>Editar</button>
          <button type="button" class="action" aria-label="Excluir comentário" @click=${this.delete_}>Excluir</button>
        </div>
      </div>
      ${
				this.editing
					? html`
            <form @submit=${this.save} @keydown=${this.onKeyDown}>
              <textarea
                class="input"
                rows="2"
                maxlength="5000"
                required
                aria-label="Editar comentário"
                .value=${this.text}
              ></textarea>
              <div class="buttons">
                <button type="submit" class="btn btn--primary">Salvar</button>
                <button type="button" class="btn btn--secondary" @click=${this.cancel}>Cancelar</button>
              </div>
            </form>
          `
					: ""
			}
    `;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-comment": KanbanComment;
	}
}
