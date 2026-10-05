import { css, html } from "lit";
import { customElement, property, query, state } from "lit/decorators.js";
import { applyServerElement } from "../lib/apply-server-element";
import { announceCardUpdate } from "../lib/card-update";
import { HtmxElement } from "../lib/htmx-element";
import { htmxRequest } from "../lib/htmx-request";
import { buttons } from "../styles/buttons";
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
		buttons,
		css`
      :host {
        display: contents;
      }

      dialog {
        border: var(--nb-border);
        padding: 0;
        width: min(768px, calc(100vw - 32px));
        max-height: calc(100vh - 64px);
        overflow-y: auto;
        border-radius: var(--radius-xl);
        background: var(--color-bg-card);
        color: var(--color-text-primary);
        box-shadow: var(--shadow-dialog);
        font-family: var(--font-family);
      }

      dialog::backdrop {
        background: var(--color-backdrop);
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
        border: var(--nb-border-sm);
        border-radius: var(--radius-md);
        font-size: var(--font-size-xl);
        font-weight: var(--font-weight-semibold);
        outline: none;
        color: var(--color-text-primary);
        background: var(--color-bg-column);
      }

      kanban-inline-edit::part(input):focus {
        box-shadow: var(--shadow-sm);
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

      /* Sections are slotted custom elements: space them like the templates' siblings. */
      ::slotted(:not(:first-child)) {
        margin-top: 24px;
      }

      .section-title {
        margin: 0 0 8px;
        font-size: var(--font-size-base);
        font-weight: var(--font-weight-semibold);
        color: var(--color-text-light);
      }

      .checklist-form {
        display: flex;
        flex-direction: column;
        gap: 8px;
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

      .checklist-form input {
        display: block;
        flex-grow: 1;
        min-width: 0;
        width: 100%;
        padding: 6px 10px;
        border: var(--nb-border-sm);
        border-radius: var(--radius-md);
        font-size: var(--font-size-base);
        outline: none;
        box-sizing: border-box;
      }

      .checklist-form input:focus {
        box-shadow: var(--shadow-sm);
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

      .action--danger {
        margin-top: 8px;
        background: var(--color-danger);
        color: var(--color-on-accent);
      }

      .action--danger:hover {
        background: var(--color-danger-hover);
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

	@property({ attribute: "checklists-url" })
	checklistsUrl = "";

	@state()
	private checklistOpen = false;

	@query("dialog")
	private dialog?: HTMLDialogElement;

	@query("kanban-inline-edit")
	private titleEdit?: KanbanInlineEdit;

	private opener?: HTMLElement;

	override connectedCallback() {
		super.connectedCallback();
		// Any section that announces a card update may carry the activity entry
		// it caused; show it at the top of the timeline (the event goes on to
		// the board for the card front).
		this.addEventListener("kanban-card-updated", this.onCardUpdated, {
			signal: this.signal,
		});
	}

	private onCardUpdated = (e: Event) => {
		const { html } = (e as CustomEvent<{ html: string }>).detail;
		const template = document.createElement("template");
		template.innerHTML = html.trim();
		const entries = template.content.querySelectorAll("kanban-activity-entry");
		const activity = this.querySelector(":scope > kanban-card-activity");
		if (activity && entries.length) activity.prepend(...entries);
	};

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

	private openChecklistForm = () => {
		this.checklistOpen = !this.checklistOpen;
		if (this.checklistOpen) {
			this.updateComplete.then(() =>
				this.renderRoot
					.querySelector<HTMLInputElement>(".checklist-form input")
					?.focus(),
			);
		}
	};

	private onChecklistKeyDown = (e: KeyboardEvent) => {
		if (e.key === "Escape") {
			// Close the popover only: don't let the <dialog> close too.
			e.preventDefault();
			e.stopPropagation();
			this.checklistOpen = false;
		}
	};

	private addChecklist = async (e: Event) => {
		e.preventDefault();
		const input = this.renderRoot.querySelector<HTMLInputElement>(
			".checklist-form input",
		);
		const { successful, html } = await htmxRequest(
			this,
			"post",
			this.checklistsUrl,
			{ title: input?.value ?? "" },
		);
		if (!successful) return;
		const template = document.createElement("template");
		template.innerHTML = html.trim();
		const checklist = template.content.querySelector("kanban-checklist");
		if (checklist) {
			// Keep the section order: after the last checklist, else the description.
			const existing = [...this.querySelectorAll(":scope > kanban-checklist")];
			const anchor =
				existing[existing.length - 1] ??
				this.querySelector(":scope > kanban-card-description");
			if (anchor) anchor.after(checklist);
			else this.append(checklist);
		}
		announceCardUpdate(this, html);
		this.checklistOpen = false;
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
              <div class="checklist-create" @keydown=${this.onChecklistKeyDown}>
                <button
                  type="button"
                  class="action"
                  aria-expanded=${this.checklistOpen ? "true" : "false"}
                  @click=${this.openChecklistForm}
                >Checklist</button>
                ${
									this.checklistOpen
										? html`
                      <form
                        class="checklist-form"
                        role="region"
                        aria-label="Adicionar checklist"
                        @submit=${this.addChecklist}
                      >
                        <input
                          type="text"
                          maxlength="100"
                          aria-label="Título do novo checklist"
                          .value=${"Checklist"}
                        />
                        <button type="submit" class="btn btn-primary">Adicionar</button>
                      </form>
                    `
										: ""
								}
              </div>
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
