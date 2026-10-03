import { css, html, LitElement } from "lit";
import { customElement, property } from "lit/decorators.js";

/**
 * "+ Adicionar …" trigger that expands into a form.
 *
 * - `slot="trigger"`: the button that opens it;
 * - default slot: the `<form>` (owned by the parent so that its fields,
 *   including a form-associated `<kanban-color-picker>`, live in the same
 *   tree as the form and submit with it);
 * - any element with `data-add-form-cancel` closes it.
 *
 * Escape closes it; a successful htmx request inside closes it and resets the
 * form. Emits `add-form-close` when it closes.
 */
@customElement("kanban-add-form")
export class KanbanAddForm extends LitElement {
	static styles = css`
    :host {
      display: block;
    }

    [hidden] {
      display: none;
    }
  `;

	@property({ type: Boolean, reflect: true })
	open = false;

	override connectedCallback() {
		super.connectedCallback();
		this.addEventListener("click", this.onClick);
		this.addEventListener("keydown", this.onKeyDown);
		this.addEventListener("htmx:after-request", this.onAfterRequest);
	}

	override disconnectedCallback() {
		super.disconnectedCallback();
		this.removeEventListener("click", this.onClick);
		this.removeEventListener("keydown", this.onKeyDown);
		this.removeEventListener("htmx:after-request", this.onAfterRequest);
	}

	show() {
		this.open = true;
		this.updateComplete.then(() => {
			this.querySelector<HTMLElement>(
				"input:not([type=hidden]), textarea",
			)?.focus();
		});
	}

	close() {
		if (!this.open) return;
		this.open = false;
		this.querySelector("form")?.reset();
		this.dispatchEvent(new CustomEvent("add-form-close", { bubbles: true }));
	}

	private onClick = (e: MouseEvent) => {
		const path = e.composedPath();
		const trigger = this.querySelector('[slot="trigger"]');
		if (trigger && path.includes(trigger)) {
			this.show();
		} else if (
			path.some(
				(el) =>
					el instanceof Element && el.hasAttribute("data-add-form-cancel"),
			)
		) {
			this.close();
		}
	};

	private onKeyDown = (e: KeyboardEvent) => {
		if (e.key === "Escape" && this.open) this.close();
	};

	private onAfterRequest = (e: Event) => {
		if ((e as CustomEvent).detail?.successful) this.close();
	};

	override render() {
		return html`
      <div ?hidden=${this.open}><slot name="trigger"></slot></div>
      <div ?hidden=${!this.open}><slot></slot></div>
    `;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-add-form": KanbanAddForm;
	}
}
