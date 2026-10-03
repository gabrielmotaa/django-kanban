import { css, html, LitElement } from "lit";
import { customElement, property } from "lit/decorators.js";

/**
 * One automatic history entry. The message is the text content and the
 * absolute timestamp (`created`) is formatted by the server, so there is no
 * client-side date logic that could diverge from the other version.
 */
@customElement("kanban-activity-entry")
export class KanbanActivityEntry extends LitElement {
	static styles = css`
    :host {
      display: block;
      padding: 0 12px;
      font-size: var(--font-size-sm);
      color: var(--color-text-muted);
    }

    .time {
      margin-left: 8px;
    }
  `;

	@property()
	created = "";

	override connectedCallback() {
		super.connectedCallback();
		this.setAttribute("role", "listitem");
	}

	override render() {
		return html`<span class="message"><slot></slot></span> <span class="time">${this.created}</span>`;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-activity-entry": KanbanActivityEntry;
	}
}
