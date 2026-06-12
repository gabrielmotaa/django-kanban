import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";

@customElement("kanban-board-title")
export class KanbanBoardTitle extends LitElement {
  @property({ type: Number, attribute: "board-id" })
  boardId = 0;

  @property({ type: String, reflect: true })
  title = "";

  @state()
  private editing = false;

  static styles = css`
    input, button, select, textarea {
      font: inherit;
    }

    :host {
      display: block;
    }

    .board-header {
      display: flex;
      align-items: center;
      margin-bottom: 20px;
      min-height: 48px;
    }

    .view {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .title {
      font-size: var(--font-size-xxl);
      font-weight: var(--font-weight-bold);
      color: var(--color-text-primary);
      margin: 0;
      letter-spacing: -0.025em;
    }

    .edit-btn {
      background: var(--color-bg-column);
      border: none;
      cursor: pointer;
      padding: 8px;
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background var(--transition-normal), transform var(--transition-fast);
    }

    .edit-btn:hover {
      background: var(--color-border-hover);
      transform: scale(1.05);
    }

    .edit-btn svg {
      fill: var(--color-text-primary);
    }

    .form {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .input {
      font-size: var(--font-size-xl);
      font-weight: var(--font-weight-semibold);
      padding: 6px 12px;
      border: 2px solid var(--color-input-border);
      border-radius: var(--radius-md);
      outline: none;
      color: var(--color-text-primary);
      background: var(--color-bg-column);
      transition: border-color var(--transition-normal);
    }

    .input:focus {
      border-color: var(--color-primary);
    }

    .btn-save,
    .btn-cancel {
      padding: 8px 16px;
      font-size: var(--font-size-base);
      font-weight: var(--font-weight-medium);
      border-radius: var(--radius-md);
      border: none;
      cursor: pointer;
      transition: background var(--transition-normal);
    }

    .btn-save {
      background: var(--color-primary);
      color: white;
    }

    .btn-save:hover {
      background: var(--color-primary-hover);
    }

    .btn-cancel {
      background: var(--color-border);
      color: var(--color-text-light);
    }

    .btn-cancel:hover {
      background: var(--color-border-hover);
    }
  `;

  get patchUrl(): string {
    return window.urls.boardDetail;
  }

  override updated() {
    if (this.shadowRoot) {
      window.htmx.process(this.shadowRoot as any);
    }
  }

  private onEditClick = () => {
    this.editing = true;
    this.updateComplete.then(() => {
      const input = this.shadowRoot?.querySelector(".input") as HTMLInputElement;
      input?.focus();
    });
  };

  private onCancelClick = () => {
    this.editing = false;
  };

  private onKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Escape") {
      this.editing = false;
    }
  };

  render() {
    return html`
      <div class="board-header">
        ${this.editing
          ? html`
              <form
                class="form"
                hx-patch=${this.patchUrl}
                hx-target="host"
                hx-swap="outerHTML"
                @submit=${() => { this.editing = false; }}
              >
                <input
                  type="text"
                  name="title"
                  .value=${this.title}
                  required
                  class="input"
                  maxlength="100"
                  @keydown=${this.onKeyDown}
                />
                <button type="submit" class="btn-save">Salvar</button>
                <button type="button" @click=${this.onCancelClick} class="btn-cancel">
                  Cancelar
                </button>
              </form>
            `
          : html`
              <div class="view">
                <h1 class="title">${this.title}</h1>
                <button
                  type="button"
                  @click=${this.onEditClick}
                  class="edit-btn"
                  title="Editar título do quadro"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px">
                    <path d="M200-200h57l391-391-57-57-391 391v57Zm-80 80v-170l528-527q12-11 26.5-17t30.5-6q16 0 31 6t26 18l55 56q12 11 17.5 26t5.5 30q0 16-5.5 30.5T817-647L290-120H120Zm640-584-56-56 56 56Zm-141 85-28-29 57 57-29-28Z"/>
                  </svg>
                </button>
              </div>
            `}
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "kanban-board-title": KanbanBoardTitle;
  }
}
