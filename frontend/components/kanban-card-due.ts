import { css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { applyServerElement } from "../lib/apply-server-element";
import { announceCardUpdate } from "../lib/card-update";
import { HtmxElement } from "../lib/htmx-element";
import { htmxRequest } from "../lib/htmx-request";
import { reset } from "../styles/reset";

/**
 * Due-date section of the card dialog. All values are server-sent: `value`
 * (ISO, for the date input), `display` (dd/mm/aaaa), `status`, `chip` and
 * `completed` ("true" | "false"). Changes PATCH `href`; the response is this
 * element's new state plus the card front, which is announced to the board.
 */
@customElement("kanban-card-due")
export class KanbanCardDue extends HtmxElement {
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
        gap: 12px;
      }

      .done {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: var(--font-size-base);
        cursor: pointer;
      }

      input[type="checkbox"] {
        margin: 0;
      }

      .date {
        padding: 6px 10px;
        border: none;
        border-radius: var(--radius-md);
        background: var(--color-bg-column);
        color: var(--color-text-primary);
        font-size: var(--font-size-base);
        cursor: pointer;
      }

      .date:hover {
        background: var(--color-border-hover);
      }

      .date--empty {
        color: var(--color-text-muted);
      }

      .chip {
        padding: 2px 6px;
        border-radius: var(--radius-sm);
        font-size: var(--font-size-sm);
        font-weight: var(--font-weight-medium);
      }

      .chip--overdue {
        background: var(--color-danger);
        color: white;
      }

      .chip--soon {
        background: #f59e0b;
        color: #1e293b;
      }

      form {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-top: 8px;
        padding: 12px;
        border: 1px solid var(--color-border);
        border-radius: var(--radius-lg);
        background: var(--color-bg-card);
        box-shadow: var(--shadow-dropdown);
        box-sizing: border-box;
      }

      .input {
        display: block;
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

      .actions {
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

      .btn--danger {
        background: none;
        color: var(--color-danger);
      }

      .btn--danger:hover {
        background: #fef2f2;
      }
    `,
	];

	@property()
	href = "";

	@property()
	value = "";

	@property()
	display = "";

	@property()
	status = "";

	@property()
	chip = "";

	@property()
	completed = "false";

	@state()
	private open = false;

	override connectedCallback() {
		super.connectedCallback();
		this.addEventListener("keydown", this.onKeyDown, { signal: this.signal });
	}

	private onKeyDown = (e: KeyboardEvent) => {
		if (e.key === "Escape" && this.open) {
			// Close the popover only: don't let the enclosing <dialog> close too.
			e.preventDefault();
			e.stopPropagation();
			this.open = false;
		}
	};

	private async send(values: Record<string, string>) {
		const { successful, html } = await htmxRequest(
			this,
			"patch",
			this.href,
			values,
		);
		if (!successful) return false;
		applyServerElement(this, html);
		announceCardUpdate(this, html);
		this.open = false;
		return true;
	}

	private toggleCompleted = async (e: Event) => {
		const input = e.target as HTMLInputElement;
		const ok = await this.send({
			due_date: this.value,
			completed: String(input.checked),
		});
		if (!ok) input.checked = !input.checked;
	};

	private save = (e: Event) => {
		e.preventDefault();
		const input = this.renderRoot.querySelector<HTMLInputElement>(".input");
		void this.send({
			due_date: input?.value ?? "",
			completed: this.completed,
		});
	};

	private clearDate = () => {
		void this.send({ due_date: "", completed: "false" });
	};

	override render() {
		const hasDate = this.value !== "";
		return html`
      <section>
        <h3 class="section-title">Data de entrega</h3>
        <div class="row">
          ${
						hasDate
							? html`
                <label class="done">
                  <input
                    type="checkbox"
                    .checked=${this.completed === "true"}
                    @change=${this.toggleCompleted}
                  />
                  Concluído
                </label>
                <button
                  type="button"
                  class="date"
                  aria-expanded=${this.open ? "true" : "false"}
                  @click=${() => (this.open = !this.open)}
                >${this.display}</button>
                ${this.chip ? html`<span class="chip chip--${this.status}">${this.chip}</span>` : ""}
              `
							: html`
                <button
                  type="button"
                  class="date date--empty"
                  aria-expanded=${this.open ? "true" : "false"}
                  @click=${() => (this.open = !this.open)}
                >Adicionar data</button>
              `
					}
        </div>
        ${
					this.open
						? html`
              <form role="region" aria-label="Alterar data de entrega" @submit=${this.save}>
                <input type="date" class="input" aria-label="Data" .value=${this.value} />
                <div class="actions">
                  <button type="submit" class="btn btn--primary">Salvar</button>
                  ${hasDate ? html`<button type="button" class="btn btn--danger" @click=${this.clearDate}>Remover</button>` : ""}
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
		"kanban-card-due": KanbanCardDue;
	}
}
