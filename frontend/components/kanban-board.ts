import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("kanban-board")
export class KanbanBoard extends LitElement {
  static styles = css`
    :host {
      display: block;
      font-family: sans-serif;
      padding: 1rem;
      border: 1px solid #ccc;
      border-radius: 8px;
    }

    h2 {
      margin: 0 0 0.5rem;
    }
  `;

  @property({ type: String })
  title = "Kanban Board";

  render() {
    return html`
      <h2>${this.title}</h2>
      <slot></slot>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "kanban-board": KanbanBoard;
  }
}
