import { css, html, LitElement } from "lit";
import { customElement, property } from "lit/decorators.js";

/**
 * Small status chip on the card front. `icon` is the visible glyph/text,
 * `label` its accessible name, `variant` the color scheme
 * (`neutral` by default; `complete`, `overdue`, `soon`).
 */
@customElement("kanban-badge")
export class KanbanBadge extends LitElement {
	static styles = css`
    :host {
      display: inline-flex;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 6px;
      border-radius: var(--radius-sm);
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
      color: var(--color-text-light);
      line-height: 1.4;
    }

    :host([variant="complete"]) .badge {
      background: var(--color-success);
      color: var(--color-on-accent);
      border: var(--nb-border-sm);
    }

    :host([variant="overdue"]) .badge {
      background: var(--color-danger);
      color: var(--color-on-accent);
      border: var(--nb-border-sm);
    }

    :host([variant="soon"]) .badge {
      background: var(--color-warning);
      color: var(--color-on-accent);
      border: var(--nb-border-sm);
    }
  `;

	@property()
	icon = "";

	/** Optional text after the icon (e.g. the due date). */
	@property()
	text = "";

	@property()
	label = "";

	@property({ reflect: true })
	variant = "neutral";

	override render() {
		return html`<span class="badge" role="img" aria-label=${this.label}>${this.icon}${this.text ? ` ${this.text}` : ""}</span>`;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-badge": KanbanBadge;
	}
}
