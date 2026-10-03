import { css, html, LitElement } from "lit";
import { customElement, property } from "lit/decorators.js";
import { reset } from "../styles/reset";

/**
 * Trigger button + dropdown. Owns open state, click-away (via the composed
 * path, so it works across shadow roots), Escape and `aria-expanded`.
 * The dropdown content comes through the default slot.
 */
@customElement("kanban-menu")
export class KanbanMenu extends LitElement {
	static styles = [
		reset,
		css`
      :host {
        display: block;
      }

      .menu-wrapper {
        position: relative;
      }

      .menu-trigger {
        background: none;
        border: none;
        font-size: 18px;
        font-weight: var(--font-weight-bold);
        cursor: pointer;
        color: inherit;
        padding: 4px 8px;
        border-radius: var(--radius-sm);
        display: flex;
        align-items: center;
        justify-content: center;
        line-height: 1;
        transition: background-color var(--transition-normal), opacity var(--transition-normal);
        opacity: 0.85;
      }

      .menu-trigger:hover {
        background-color: rgba(0, 0, 0, 0.08);
        opacity: 1;
      }

      .menu-dropdown {
        position: absolute;
        right: 0;
        top: 100%;
        margin-top: 4px;
        background: white;
        border: 1px solid var(--color-border);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-dropdown);
        z-index: 100;
        min-width: 160px;
        padding: 6px 0;
        color: var(--color-text-primary);
      }

      .menu-dropdown[hidden] {
        display: none;
      }
    `,
	];

	/** Accessible name of the trigger button. */
	@property()
	label = "";

	@property({ type: Boolean, reflect: true })
	open = false;

	close() {
		this.open = false;
	}

	override connectedCallback() {
		super.connectedCallback();
		document.addEventListener("click", this.onDocumentClick);
		document.addEventListener("keydown", this.onKeyDown);
	}

	override disconnectedCallback() {
		super.disconnectedCallback();
		document.removeEventListener("click", this.onDocumentClick);
		document.removeEventListener("keydown", this.onKeyDown);
	}

	private onDocumentClick = (e: MouseEvent) => {
		if (this.open && !e.composedPath().includes(this)) this.close();
	};

	private onKeyDown = (e: KeyboardEvent) => {
		if (this.open && e.key === "Escape") this.close();
	};

	override render() {
		return html`
      <div class="menu-wrapper">
        <button
          type="button"
          class="menu-trigger"
          aria-label=${this.label}
          aria-expanded=${this.open ? "true" : "false"}
          @click=${() => (this.open = !this.open)}
        >
          ⋮
        </button>
        <div class="menu-dropdown" ?hidden=${!this.open}>
          <slot></slot>
        </div>
      </div>
    `;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-menu": KanbanMenu;
	}
}
