import { css, html, LitElement } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { announceCardUpdate } from "../lib/card-update";
import { htmxRequest } from "../lib/htmx-request";
import { reset } from "../styles/reset";

/**
 * "Comentários e atividade" section of the card dialog: composer, details
 * toggle and the timeline (light-DOM `<kanban-comment>` and
 * `<kanban-activity-entry>` children, newest first). Activity entries created
 * by other sections arrive through the dialog (see `kanban-card-dialog`).
 */
@customElement("kanban-card-activity")
export class KanbanCardActivity extends LitElement {
	static styles = [
		reset,
		css`
      :host {
        display: block;
      }

      .header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 8px;
      }

      .section-title {
        margin: 0;
        font-size: var(--font-size-base);
        font-weight: var(--font-weight-semibold);
        color: var(--color-text-light);
      }

      .toggle {
        padding: 4px 8px;
        border: var(--nb-border-sm);
        border-radius: var(--radius-md);
        background: var(--color-bg-column);
        font-size: var(--font-size-sm);
        color: var(--color-text-secondary);
        cursor: pointer;
      }

      .toggle:hover {
        background: var(--color-surface-hover);
      }

      form {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
        margin-bottom: 16px;
      }

      .input {
        display: block;
        width: 100%;
        min-height: 56px;
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

      .btn {
        padding: 6px 12px;
        border: var(--nb-border-sm);
        box-shadow: var(--shadow-sm);
        border-radius: var(--radius-md);
        background: var(--color-primary);
        color: var(--color-on-accent);
        font-size: var(--font-size-base);
        font-weight: var(--font-weight-bold);
        cursor: pointer;
        transition: background var(--transition-normal), transform var(--transition-fast), box-shadow var(--transition-fast);
      }

      .btn:active {
        transform: var(--nb-press);
        box-shadow: none;
      }

      .btn:hover {
        background: var(--color-primary-hover);
      }

      .list {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      :host([hide-details]) ::slotted(kanban-activity-entry) {
        display: none;
      }
    `,
	];

	@property({ attribute: "comments-url" })
	commentsUrl = "";

	@property({ attribute: "hide-details", type: Boolean, reflect: true })
	hideDetails = false;

	@query(".input")
	private input?: HTMLTextAreaElement;

	private onSubmit = async (e: Event) => {
		e.preventDefault();
		const input = this.input;
		if (!input || input.disabled) return;
		const text = input.value;
		input.disabled = true;
		const { successful, html } = await htmxRequest(
			this,
			"post",
			this.commentsUrl,
			{ text },
		);
		input.disabled = false;
		if (!successful) return;
		const template = document.createElement("template");
		template.innerHTML = html.trim();
		const comment = template.content.querySelector("kanban-comment");
		if (comment) this.prepend(comment);
		announceCardUpdate(this, html);
		input.value = "";
	};

	override render() {
		return html`
      <section>
        <div class="header">
          <h3 class="section-title">Comentários e atividade</h3>
          <button type="button" class="toggle" @click=${() => (this.hideDetails = !this.hideDetails)}>
            ${this.hideDetails ? "Mostrar detalhes" : "Ocultar detalhes"}
          </button>
        </div>
        <form @submit=${this.onSubmit}>
          <textarea
            class="input"
            rows="2"
            maxlength="5000"
            required
            placeholder="Escrever um comentário…"
            aria-label="Escrever um comentário…"
          ></textarea>
          <button type="submit" class="btn" aria-label="Salvar comentário">Salvar</button>
        </form>
        <div class="list" role="list"><slot></slot></div>
      </section>
    `;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-card-activity": KanbanCardActivity;
	}
}
