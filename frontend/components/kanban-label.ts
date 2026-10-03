import { css, html, LitElement } from "lit";
import { customElement, property } from "lit/decorators.js";

/**
 * A colored label pill. A named label shows its name; a color-only label is a
 * bar named after its color. `block` stretches it (label picker rows).
 */
@customElement("kanban-label")
export class KanbanLabel extends LitElement {
	static styles = css`
    :host {
      display: inline-block;
      max-width: 100%;
    }

    :host([block]) {
      display: block;
      flex-grow: 1;
    }

    .pill {
      display: block;
      max-width: 100%;
      padding: 2px 8px;
      border-radius: var(--radius-sm);
      background: var(--label-color);
      color: var(--label-fg);
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
      line-height: 1.4;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      box-sizing: border-box;
    }

    :host([block]) .pill {
      padding: 6px 10px;
    }

    .bar {
      width: 40px;
      height: 8px;
      padding: 0;
    }

    :host([block]) .bar {
      width: auto;
      height: 28px;
    }
  `;

	@property()
	name = "";

	@property()
	color = "#64748b";

	@property()
	fg = "#ffffff";

	@property({ attribute: "color-name" })
	colorName = "";

	@property({ type: Boolean, reflect: true })
	block = false;

	override render() {
		const style = `--label-color: ${this.color}; --label-fg: ${this.fg};`;
		return this.name
			? html`<span class="pill" style=${style}>${this.name}</span>`
			: html`<span class="pill bar" role="img" aria-label=${this.colorName} style=${style}></span>`;
	}
}

declare global {
	interface HTMLElementTagNameMap {
		"kanban-label": KanbanLabel;
	}
}
