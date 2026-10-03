import { css, html } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { applyServerElement } from "../lib/apply-server-element";
import { announceCardUpdate } from "../lib/card-update";
import { HtmxElement } from "../lib/htmx-element";
import { htmxRequest } from "../lib/htmx-request";
import { reset } from "../styles/reset";
import type { KanbanInlineEdit } from "./kanban-inline-edit";

/**
 * Modal shell of a card (native `<dialog>`): editable title, column name,
 * a slot for the feature sections (server-rendered light-DOM children) and
 * the actions. It is opened with `open(opener)`; closing (×, Escape, backdrop)
 * returns focus to the card that opened it and removes the element.
 */
@customElement("kanban-card-dialog")
export class KanbanCardDialog extends HtmxElement {
	static styles = [
		reset,
		css`
      :host {
        display: contents;
      }

      dialog {
        border: none;
        padding: 0;
        width: min(768px, calc(100vw - 32px));
        max-height: calc(100vh - 64px);
        overflow-y: auto;
        border-radius: var(--radius-xl);
        background: var(--color-bg-card);
        color: var(--color-text-primary);
        box-shadow: var(--shadow-lg);
        font-family: var(--font-family);
      }

      dialog::backdrop {
        background: rgba(15, 23, 42, 0.5);
      }

      .body {
        position: relative;
        padding: 24px;
      }

      .close {
        position: absolute;
        top: 12px;
        right: 12px;
        width: 32px;
        height: 32px;
        background: none;
        border: none;
        border-radius: var(--radius-md);
        font-size: 24px;
        line-height: 1;
        color: var(--color-text-muted);
        cursor: pointer;
      }

      .close:hover {
        background: var(--color-bg-column);
      }

      header {
        margin-bottom: 20px;
        padding-right: 40px;
      }

      .heading {
        margin: 0;
        font-size: var(--font-size-xl);
        font-weight: var(--font-weight-semibold);
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

      kanban-inline-edit {
        --btn-padding: 6px 12px;
        --btn-font-size: var(--font-size-base);
        --btn-radius: var(--radius-md);
      }

      kanban-inline-edit::part(form) {
        gap: 8px;
      }

      kanban-inline-edit::part(input) {
        padding: 6px 12px;
        border: 2px solid var(--color-input-border);
        border-radius: var(--radius-md);
        font-size: var(--font-size-xl);
        font-weight: var(--font-weight-semibold);
        outline: none;
        color: var(--color-text-primary);
        background: var(--color-bg-column);
      }

      kanban-inline-edit::part(input):focus {
        border-color: var(--color-primary);
      }

      .column {
        margin: 4px 0 0;
        padding: 0 8px;
        font-size: var(--font-size-sm);
        color: var(--color-text-muted);
      }

      .layout {
        display: grid;
        grid-template-columns: 1fr 168px;
        gap: 24px;
      }

      @media (max-width: 720px) {
        .layout {
          grid-template-columns: 1fr;
        }
      }

      .section-title {
        margin: 0 0 8px;
        font-size: var(--font-size-base);
        font-weight: var(--font-weight-semibold);
        color: var(--color-text-light);
      }

      .action {
        display: block;
        width: 100%;
        padding: 8px 12px;
        background: var(--color-bg-column);
        border: none;
        border-radius: var(--radius-md);
        font-size: var(--font-size-base);
        color: var(--color-text-secondary);
        text-align: left;
        cursor: pointer;
        transition: background var(--transition-normal);
      }

      .action:hover {
        background: var(--color-border-hover);
      }

      .action--danger {
        color: var(--color-danger);
      }
    `,
	];

	@property({ attribute: "card-id", type: Number })
	cardId = 0;

	@property()
	title = "";

	@property({ attribute: "column-title" })
	columnTitle = "";

	@property()
	href = "";

	@query("dialog")
	private dialog?: HTMLDialogElement;

	@query("kanban-inline-edit")
	private titleEdit?: KanbanInlineEdit;

	private opener?: HTMLElement;

	async open(opener: HTMLElement) {
		this.opener = opener;
		await this.updateComplete;
		this.dialog?.showModal();
	}

	close() {
		this.dialog?.close();
	}

	private onBackdropClick = (e: MouseEvent) => {
		// Only the backdrop (outside the padded body) targets the dialog itself.
		if (e.target === this.dialog) this.close();
	};

	// The card front may have been replaced (renamed), so look it up by id.
	private get card(): HTMLElement | null {
		const board = (this.getRootNode() as ShadowRoot).host;
		return board?.querySelector(`#card-${this.cardId}`) ?? this.opener ?? null;
	}

	private onClosed = () => {
		this.card?.focus();
		this.remove();
	};

	private onTitleSaved = (e: CustomEvent<{ html: string }>) => {
		e.stopPropagation();
		applyServerElement(this, e.detail.html);
		announceCardUpdate(this, e.detail.html);
	};

	private onDelete = async () => {
		if (!confirm("Deletar este card?")) return;
		const { successful } = await htmxRequest(this, "delete", this.href);
		if (!successful) return;
		this.card?.remove();
		this.close();
	};

	override render() {
		return html`
      <dialog
        aria-label=${this.title}
        @click=${this.onBackdropClick}
        @close=${this.onClosed}
      >
        <div class="body">
          <button type="button" class="close" aria-label="Fechar" @click=${() => this.close()}>×</button>

          <header>
            <kanban-inline-edit
              href=${this.href}
              name="title"
              label="Título do card"
              maxlength="200"
              value=${this.title}
              @kanban-saved=${this.onTitleSaved}
            >
              <h2 class="heading">
                <button type="button" class="title-btn" @click=${() => this.titleEdit?.edit()}>${this.title}</button>
              </h2>
            </kanban-inline-edit>
            <p class="column">na coluna ${this.columnTitle}</p>
          </header>

          <div class="layout">
            <div class="main"><slot></slot></div>
            <aside>
              <h3 class="section-title">Ações</h3>
              <button type="button" class="action action--danger" @click=${this.onDelete}>
                Excluir card
              </button>
            </aside>
          </div>
        </div>
      </dialog>
    `;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-card-dialog": KanbanCardDialog;
	}
}
