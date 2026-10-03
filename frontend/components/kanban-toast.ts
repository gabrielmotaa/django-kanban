import { css, html, LitElement } from "lit";
import { customElement } from "lit/decorators.js";

const DISMISS_AFTER_MS = 4000;

/** Transient error message; the server sends it as `<kanban-toast>text</kanban-toast>`. */
@customElement("kanban-toast")
export class KanbanToast extends LitElement {
	static styles = css`
    :host {
      display: block;
      max-width: 360px;
      padding: 12px 16px;
      border-radius: var(--radius-lg);
      background: var(--color-danger);
      color: white;
      font-size: var(--font-size-base);
      font-weight: var(--font-weight-medium);
      box-shadow: var(--shadow-lg);
    }
  `;

	private timer?: ReturnType<typeof setTimeout>;

	override connectedCallback() {
		super.connectedCallback();
		this.setAttribute("role", "alert");
		this.timer = setTimeout(() => this.remove(), DISMISS_AFTER_MS);
	}

	override disconnectedCallback() {
		super.disconnectedCallback();
		clearTimeout(this.timer);
	}

	override render() {
		return html`<slot></slot>`;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-toast": KanbanToast;
	}
}
