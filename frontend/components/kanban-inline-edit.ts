import { css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { HtmxElement } from "../lib/htmx-element";
import { buttons } from "../styles/buttons";
import { reset } from "../styles/reset";

/**
 * View/edit toggle for a single text value. The view is the default slot;
 * editing shows a form that PATCHes `href` itself (it is the hypermedia
 * control of that value). The server response is not swapped: it is handed
 * to the owner in a `kanban-saved` event (`detail.html`).
 *
 * Enter saves (native submit), Escape cancels, the input gets focus.
 * Owners style the pieces through `::part(form|input|save|cancel)`.
 */
@customElement("kanban-inline-edit")
export class KanbanInlineEdit extends HtmxElement {
	static styles = [
		reset,
		buttons,
		css`
      :host {
        display: block;
      }

      .edit-form {
        display: flex;
        gap: 6px;
        align-items: center;
        width: 100%;
      }

      .edit-input {
        flex-grow: 1;
        min-width: 0;
      }
    `,
	];

	@property()
	href = "";

	@property()
	name = "title";

	@property()
	value = "";

	/** Accessible name of the input. */
	@property()
	label = "";

	@property()
	maxlength = "";

	@property({ attribute: "save-text" })
	saveText = "Salvar";

	@property({ attribute: "cancel-text" })
	cancelText = "Cancelar";

	/** Accessible name of the save button when its text is only an icon. */
	@property({ attribute: "save-label" })
	saveLabel = "";

	@property({ attribute: "cancel-label" })
	cancelLabel = "";

	@property({ type: Boolean, reflect: true })
	editing = false;

	edit() {
		this.editing = true;
		this.focusAfterRender(".edit-input");
	}

	cancel() {
		this.editing = false;
	}

	private onKeyDown = (e: KeyboardEvent) => {
		if (e.key === "Escape") {
			// Cancel the edit only: don't let an enclosing <dialog> close too.
			e.preventDefault();
			e.stopPropagation();
			this.cancel();
		}
	};

	private onAfterRequest = (e: CustomEvent) => {
		const { successful, xhr } = e.detail;
		if (!successful) return;
		this.editing = false;
		this.dispatchEvent(
			new CustomEvent("kanban-saved", {
				bubbles: true,
				composed: true,
				detail: { html: xhr.responseText },
			}),
		);
	};

	override render() {
		if (!this.editing) return html`<slot></slot>`;
		return html`
      <form
        class="edit-form"
        part="form"
        hx-patch=${this.href}
        hx-swap="none"
        @htmx:after-request=${this.onAfterRequest}
        @keydown=${this.onKeyDown}
      >
        <input
          type="text"
          name=${this.name}
          class="edit-input"
          part="input"
          aria-label=${this.label}
          maxlength=${ifDefined(this.maxlength || undefined)}
          required
          .value=${this.value}
        />
        <button
          type="submit"
          class="btn btn-primary edit-btn-save"
          part="save"
          aria-label=${this.saveLabel || this.saveText}
        >${this.saveText}</button>
        <button
          type="button"
          class="btn btn-secondary edit-btn-cancel"
          part="cancel"
          aria-label=${this.cancelLabel || this.cancelText}
          @click=${this.cancel}
        >${this.cancelText}</button>
      </form>
    `;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-inline-edit": KanbanInlineEdit;
	}
}
