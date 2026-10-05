import { css, html, LitElement } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { applyServerElement } from "../lib/apply-server-element";
import { htmxRequest } from "../lib/htmx-request";
import { type LabelDef, readLabels, watchLabels } from "../lib/labels";
import { closestAcrossShadow } from "../lib/palette";
import { buttons } from "../styles/buttons";
import { reset } from "../styles/reset";

type View =
	| { kind: "list" }
	| { kind: "create" }
	| { kind: "edit"; id: number };

/**
 * Label popover of a card: search, toggle labels on the card, and create /
 * edit / delete board labels. Toggling PATCHes the card's labels endpoint and
 * emits `kanban-saved` (the card-labels section applies the response).
 * Label changes return the updated registry as `<kanban-board labels=…>`,
 * which is applied to the board; every card and pill then re-renders.
 */
@customElement("kanban-label-picker")
export class KanbanLabelPicker extends LitElement {
	static styles = [
		reset,
		buttons,
		css`
      :host {
        display: block;
        margin-top: 8px;
        padding: 12px;
        border: var(--nb-border-sm);
        border-radius: var(--radius-lg);
        background: var(--color-bg-card);
        box-shadow: var(--shadow-dropdown);
        box-sizing: border-box;
        --btn-padding: 6px 12px;
        --btn-font-size: var(--font-size-base);
        --btn-radius: var(--radius-md);
      }

      input[type="checkbox"] {
        margin: 0;
      }

      .search,
      .input {
        display: block;
        width: 100%;
        padding: 6px 10px;
        border: var(--nb-border-sm);
        border-radius: var(--radius-md);
        font-size: var(--font-size-base);
        outline: none;
        box-sizing: border-box;
      }

      .search:focus,
      .input:focus {
        box-shadow: var(--shadow-sm);
      }

      .search {
        margin-bottom: 8px;
      }

      .list {
        display: flex;
        flex-direction: column;
        gap: 4px;
        max-height: 200px;
        margin: 0 0 8px;
        padding: 0;
        list-style: none;
        overflow-y: auto;
      }

      .item {
        display: flex;
        align-items: center;
        gap: 6px;
      }

      .toggle {
        display: flex;
        flex-grow: 1;
        align-items: center;
        gap: 8px;
        min-width: 0;
        cursor: pointer;
      }

      .edit {
        padding: 4px 6px;
        border: none;
        border-radius: var(--radius-sm);
        background: none;
        color: var(--color-text-muted);
        font-size: var(--font-size-base);
        cursor: pointer;
      }

      .edit:hover {
        background: var(--color-bg-column);
      }

      .action {
        display: block;
        width: 100%;
        padding: 8px 12px;
        background: var(--color-bg-column);
        border: var(--nb-border-sm);
        box-shadow: var(--shadow-sm);
        border-radius: var(--radius-md);
        font-size: var(--font-size-base);
        color: var(--color-text-secondary);
        text-align: left;
        cursor: pointer;
        transition: background var(--transition-normal), transform var(--transition-fast), box-shadow var(--transition-fast);
      }

      .action:hover {
        background: var(--color-surface-hover);
      }

      .action:active {
        transform: var(--nb-press);
        box-shadow: none;
      }

      form {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .title {
        margin: 0;
        font-size: var(--font-size-base);
        font-weight: var(--font-weight-semibold);
        color: var(--color-text-light);
      }

      kanban-color-picker {
        margin-bottom: -8px;
      }

      .actions {
        display: flex;
        gap: 8px;
      }

      .btn-danger {
        background: none;
        color: var(--color-danger);
      }

      .btn-danger:hover {
        background: var(--color-danger-soft);
      }
    `,
	];

	/** Card labels endpoint: POST attaches, DELETE (?label_id=) detaches. */
	@property()
	href = "";

	@property({ attribute: "create-url" })
	createUrl = "";

	@property({ attribute: "board-id", type: Number })
	boardId = 0;

	@property({ attribute: "card-id", type: Number })
	cardId = 0;

	/** Ids of the labels currently on the card. */
	@property({ attribute: false })
	attached = new Set<number>();

	@state()
	private view: View = { kind: "list" };

	@state()
	private query = "";

	@state()
	private draftName = "";

	@state()
	private draftColor = "#64748b";

	private disposer = new AbortController();

	override connectedCallback() {
		super.connectedCallback();
		this.disposer = new AbortController();
		watchLabels(this, this.disposer.signal);
	}

	override disconnectedCallback() {
		super.disconnectedCallback();
		this.disposer.abort();
	}

	private get board(): Element | null {
		return closestAcrossShadow(this, "kanban-board");
	}

	private emit(name: string, detail?: unknown) {
		this.dispatchEvent(
			new CustomEvent(name, { bubbles: true, composed: true, detail }),
		);
	}

	private toggling: Promise<unknown> = Promise.resolve();

	// Requests are chained so out-of-order replies cannot leave stale state.
	private toggle(label: LabelDef, input: HTMLInputElement) {
		this.toggling = this.toggling.then(() =>
			this.sendToggle(label, input.checked, input),
		);
	}

	private async sendToggle(
		label: LabelDef,
		checked: boolean,
		input: HTMLInputElement,
	) {
		const { successful, html } = checked
			? await htmxRequest(this, "post", this.href, {
					label_id: String(label.id),
				})
			: await htmxRequest(this, "delete", this.href, {
					label_id: String(label.id),
				});
		if (successful) this.emit("kanban-saved", { html });
		else input.checked = !checked;
	}

	private async applyRegistry(
		request: Promise<{ successful: boolean; html: string }>,
	) {
		const { successful, html } = await request;
		const board = this.board;
		if (!successful || !board) return;
		applyServerElement(board, html);
		this.view = { kind: "list" };
	}

	private showEdit(label: LabelDef) {
		this.draftName = label.name;
		this.draftColor = label.color;
		this.view = { kind: "edit", id: label.id };
	}

	private showCreate() {
		this.draftName = "";
		this.draftColor = "#64748b";
		this.view = { kind: "create" };
	}

	private save = (e: Event) => {
		e.preventDefault();
		const values = {
			card_id: String(this.cardId),
			name: this.draftName,
			color: this.draftColor,
		};
		const view = this.view;
		if (view.kind === "create") {
			void this.applyRegistry(
				htmxRequest(this, "post", this.createUrl, {
					...values,
					board_id: String(this.boardId),
				}),
			);
		} else if (view.kind === "edit") {
			const label = readLabels(this).find((l) => l.id === view.id);
			if (label) {
				void this.applyRegistry(htmxRequest(this, "patch", label.href, values));
			}
		}
	};

	private confirmDelete(label: LabelDef) {
		const shown = label.name || label.colorName;
		if (
			!confirm(
				`Excluir a etiqueta '${shown}'? Ela será removida de todos os cards.`,
			)
		) {
			return;
		}
		void this.applyRegistry(
			htmxRequest(this, "delete", label.href, { card_id: String(this.cardId) }),
		);
	}

	private renderList() {
		const query = this.query.toLowerCase();
		const labels = readLabels(this).filter(
			(l) => !query || `${l.name} ${l.colorName}`.toLowerCase().includes(query),
		);
		return html`
      <input
        type="search"
        class="search"
        placeholder="Buscar etiquetas…"
        aria-label="Buscar etiquetas…"
        .value=${this.query}
        @input=${(e: Event) => (this.query = (e.target as HTMLInputElement).value)}
      />
      <ul class="list">
        ${labels.map(
					(label) => html`
            <li class="item">
              <label class="toggle">
                <input
                  type="checkbox"
                  .checked=${this.attached.has(label.id)}
                  @change=${(e: Event) =>
										this.toggle(label, e.target as HTMLInputElement)}
                />
                <kanban-label
                  block
                  name=${label.name}
                  color=${label.color}
                  fg=${label.fg}
                  color-name=${label.colorName}
                ></kanban-label>
              </label>
              <button
                type="button"
                class="edit"
                aria-label="Editar etiqueta ${label.name || label.colorName}"
                @click=${() => this.showEdit(label)}
              >✎</button>
            </li>
          `,
				)}
      </ul>
      <button type="button" class="action" @click=${() => this.showCreate()}>
        Criar uma nova etiqueta
      </button>
    `;
	}

	private renderForm(view: View) {
		const editing =
			view.kind === "edit"
				? readLabels(this).find((l) => l.id === view.id)
				: null;
		return html`
      <form @submit=${this.save}>
        <p class="title">${editing ? "Editar etiqueta" : "Criar etiqueta"}</p>
        <input
          type="text"
          class="input"
          maxlength="30"
          aria-label="Nome da etiqueta"
          .value=${this.draftName}
          @input=${(e: Event) => (this.draftName = (e.target as HTMLInputElement).value)}
        />
        <kanban-color-picker
          variant="form"
          .value=${this.draftColor}
          @change=${(e: CustomEvent<{ value: string }>) => (this.draftColor = e.detail.value)}
        ></kanban-color-picker>
        <div class="actions">
          <button type="submit" class="btn btn-primary">Salvar</button>
          ${
						editing
							? html`<button type="button" class="btn btn-danger" @click=${() => this.confirmDelete(editing)}>Excluir</button>`
							: ""
					}
          <button type="button" class="btn btn-secondary" @click=${() => (this.view = { kind: "list" })}>
            Cancelar
          </button>
        </div>
      </form>
    `;
	}

	override render() {
		return html`
      <div role="region" aria-label="Etiquetas">
        ${this.view.kind === "list" ? this.renderList() : this.renderForm(this.view)}
      </div>
    `;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-label-picker": KanbanLabelPicker;
	}
}
