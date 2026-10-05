import { css } from "lit";

/** Items placed inside a `<kanban-menu>` dropdown. */
export const menuItems = css`
  .menu-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    text-align: left;
    padding: 8px 12px;
    background: none;
    border: none;
    cursor: pointer;
    font-size: var(--font-size-base);
    color: var(--color-text-secondary);
    font-family: inherit;
    transition: background var(--transition-normal);
  }

  .menu-btn:hover {
    background: var(--color-bg-body);
  }

  .menu-btn--danger {
    color: var(--color-danger);
  }

  .menu-btn--danger:hover {
    background: var(--color-danger-soft);
  }

  .menu-divider {
    border-top: var(--nb-border-sm);
    margin: 6px 0;
  }

  .menu-section-title {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    font-weight: var(--font-weight-semibold);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 8px;
    padding: 0 12px;
  }
`;
