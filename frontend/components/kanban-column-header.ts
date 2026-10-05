import { css, html, LitElement } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { htmxRequest } from "../lib/htmx-request";
import { menuItems } from "../styles/menu";
import { reset } from "../styles/reset";
import type { KanbanInlineEdit } from "./kanban-inline-edit";
import type { KanbanMenu } from "./kanban-menu";

/**
 * Colored header of a column: title (with inline rename), options menu with
 * the color picker and delete. It never mutates the column itself; it emits
 * `kanban-saved` (server element, `detail.html`) and `kanban-column-deleted`
 * for the column to apply, and `kanban-column-grab` / `-release` while the
 * title is pressed (the column becomes draggable).
 */
@customElement("kanban-column-header")
export class KanbanColumnHeader extends LitElement {
	static styles = [
		reset,
		menuItems,
		css`
      :host {
        display: block;
      }

      .header-bg {
        background-color: var(--column-color, var(--color-text-muted));
        color: var(--column-fg, #ffffff);
        padding: 12px 16px;
        border-bottom: var(--nb-border);
        /* Inner radius: the column's own border sits outside this strip */
        border-top-left-radius: calc(var(--radius-xl) - var(--border-width));
        border-top-right-radius: calc(var(--radius-xl) - var(--border-width));
        transition: background-color var(--transition-normal);
      }

      .header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        position: relative;
      }

      .title-text {
        font-size: var(--font-size-lg);
        font-weight: var(--font-weight-bold);
        color: inherit;
        padding: 4px 0;
        flex-grow: 1;
        cursor: grab;
        user-select: none;
      }

      .title-text:active {
        cursor: grabbing;
      }

      kanban-inline-edit::part(input) {
        padding: 6px 10px;
        border: var(--nb-border-sm);
        border-radius: var(--radius-md);
        font-size: var(--font-size-lg);
        outline: none;
        background-color: var(--color-bg-card);
        color: var(--color-text-primary);
        font-weight: var(--font-weight-medium);
        transition: background-color var(--transition-normal), border-color var(--transition-normal);
      }

      kanban-inline-edit::part(input):focus {
        box-shadow: var(--shadow-sm);
      }

      kanban-inline-edit::part(save),
      kanban-inline-edit::part(cancel) {
        flex-shrink: 0;
        padding: 6px 10px;
        border-radius: var(--radius-md);
        font-size: var(--font-size-base);
        font-weight: var(--font-weight-bold);
        transition: opacity var(--transition-normal), transform var(--transition-fast), box-shadow var(--transition-fast);
      }

      kanban-inline-edit::part(save):hover,
      kanban-inline-edit::part(cancel):hover {
        opacity: 0.9;
      }

      kanban-inline-edit::part(save) {
        background-color: var(--color-bg-card);
        color: var(--color-text-primary);
      }

      kanban-inline-edit::part(cancel) {
        background-color: var(--color-surface-muted);
        color: var(--color-text-primary);
      }
    `,
	];

	@property()
	title = "";

	@property()
	color = "#64748b";

	@property({ attribute: "fg-color" })
	fgColor = "#ffffff";

	@property()
	href = "";

	@query("kanban-inline-edit")
	private inlineEdit?: KanbanInlineEdit;

	@query("kanban-menu")
	private menu?: KanbanMenu;

	private emit(name: string, detail?: unknown) {
		this.dispatchEvent(
			new CustomEvent(name, { bubbles: true, composed: true, detail }),
		);
	}

	private startRename = () => {
		this.menu?.close();
		this.inlineEdit?.edit();
	};

	private onColorChange = async (e: CustomEvent<{ value: string }>) => {
		const { successful, html } = await htmxRequest(this, "patch", this.href, {
			color: e.detail.value,
		});
		if (!successful) return;
		this.menu?.close();
		this.emit("kanban-saved", { html });
	};

	private onDelete = async () => {
		this.menu?.close();
		if (
			!confirm(
				`Deseja realmente apagar a coluna '${this.title}' e todos os seus cards?`,
			)
		) {
			return;
		}
		const { successful } = await htmxRequest(this, "delete", this.href);
		if (successful) this.emit("kanban-column-deleted");
	};

	override render() {
		return html`
      <div class="header-bg" style="--column-color: ${this.color}; --column-fg: ${this.fgColor};">
        <div class="title">
          <kanban-inline-edit
            href=${this.href}
            name="title"
            label="Nome da coluna"
            value=${this.title}
            save-text="✓"
            cancel-text="✗"
            save-label="Salvar nome"
            cancel-label="Cancelar edição"
          >
            <div class="header">
              <span
                class="title-text"
                @mousedown=${() => this.emit("kanban-column-grab")}
                @mouseup=${() => this.emit("kanban-column-release")}
              >
                ${this.title}
              </span>

              <kanban-menu label="Opções da coluna">
                <button type="button" class="menu-btn" @click=${this.startRename}>
                  Editar nome
                </button>

                <div class="menu-divider"></div>

                <div>
                  <div class="menu-section-title">Cor da Coluna</div>
                  <kanban-color-picker
                    variant="menu"
                    .value=${this.color}
                    @change=${this.onColorChange}
                  ></kanban-color-picker>
                </div>

                <div class="menu-divider"></div>

                <button type="button" class="menu-btn menu-btn--danger" @click=${this.onDelete}>
                  Apagar coluna
                </button>
              </kanban-menu>
            </div>
          </kanban-inline-edit>
        </div>
      </div>
    `;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-column-header": KanbanColumnHeader;
	}
}
