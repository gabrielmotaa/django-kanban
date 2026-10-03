import { css, html, LitElement } from "lit";
import { customElement, property } from "lit/decorators.js";

/**
 * Due-date badge on the card front. All values come from the server: the
 * display text (`due`, dd/mm), the status (`status`: complete | overdue |
 * soon | ok) and the accessible name (`label`). Reuses `<kanban-badge>`.
 */
@customElement("kanban-due-badge")
export class KanbanDueBadge extends LitElement {
	static styles = css`
    :host {
      display: inline-flex;
    }
  `;

	@property()
	due = "";

	@property()
	status = "ok";

	@property()
	label = "";

	override render() {
		return html`<kanban-badge
      icon="◷"
      text=${this.due}
      label=${this.label}
      variant=${this.status}
    ></kanban-badge>`;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-due-badge": KanbanDueBadge;
	}
}
