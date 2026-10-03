import { css, html, LitElement } from "lit";
import { customElement, property } from "lit/decorators.js";
import { type Palette, readPalette } from "../lib/palette";

/**
 * Color swatches for the board palette. Form-associated: placed inside a
 * `<form>` (same tree) it submits `name=value` like a native input.
 *
 * `variant="menu"` is the compact grid used in dropdowns; `variant="form"`
 * is the large grid used in creation forms. Emits `change` with `{ value }`.
 */
@customElement("kanban-color-picker")
export class KanbanColorPicker extends LitElement {
	static formAssociated = true;

	static styles = css`
    :host {
      display: block;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
    }

    .dot {
      border-radius: 50%;
      cursor: pointer;
      padding: 0;
      background-color: var(--dot-color);
    }

    :host([variant="menu"]) .grid {
      gap: 6px;
      padding: 0 12px;
    }

    :host([variant="menu"]) .dot {
      width: 22px;
      height: 22px;
      border: 2px solid transparent;
      transition: transform var(--transition-fast);
    }

    :host([variant="menu"]) .dot:hover {
      transform: scale(1.15);
    }

    :host([variant="menu"]) .dot--active {
      border-color: var(--color-text-secondary);
    }

    :host([variant="form"]) .grid {
      gap: 8px;
      margin-bottom: 16px;
    }

    :host([variant="form"]) .dot {
      width: 100%;
      aspect-ratio: 1;
      border: 3px solid transparent;
      outline: none;
      transition: transform var(--transition-fast);
    }

    :host([variant="form"]) .dot:hover {
      transform: scale(1.1);
    }

    :host([variant="form"]) .dot--active {
      outline: 3px solid #000;
      outline-offset: -3px;
    }
  `;

	@property({ reflect: true })
	variant: "menu" | "form" = "menu";

	@property()
	name = "";

	@property()
	value = "";

	private colors: Palette = [];
	private internals = this.attachInternals();

	override connectedCallback() {
		super.connectedCallback();
		this.colors = readPalette(this);
		this.requestUpdate();
	}

	override updated() {
		this.internals.setFormValue(this.value);
	}

	private choose(value: string) {
		// The owner applies the choice by updating `value` (e.g. after the server
		// confirmed it), so a rejected change never leaves a stale highlight.
		this.dispatchEvent(
			new CustomEvent("change", {
				bubbles: true,
				composed: true,
				detail: { value },
			}),
		);
	}

	override render() {
		return html`
      <div class="grid">
        ${this.colors.map(
					([hex, name]) => html`
            <button
              type="button"
              class="dot ${this.value === hex ? "dot--active" : ""}"
              style="--dot-color: ${hex};"
              title=${name}
              aria-label=${name}
              @click=${() => this.choose(hex)}
            ></button>
          `,
				)}
      </div>
    `;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-color-picker": KanbanColorPicker;
	}
}
