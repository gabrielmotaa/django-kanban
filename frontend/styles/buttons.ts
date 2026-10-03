import { css } from "lit";

/**
 * Shared button look. Components tune it through custom properties set on
 * themselves or an ancestor: `--btn-padding`, `--btn-font-size`,
 * `--btn-radius`, `--btn-secondary-bg`, `--btn-secondary-fg`,
 * `--btn-secondary-hover-bg`.
 */
export const buttons = css`
  .btn {
    padding: var(--btn-padding, 6px 10px);
    font-size: var(--btn-font-size, var(--font-size-md));
    font-weight: var(--font-weight-medium);
    border-radius: var(--btn-radius, var(--radius-sm));
    border: none;
    cursor: pointer;
    transition: background var(--transition-normal);
  }

  .btn-primary {
    background: var(--color-primary);
    color: white;
  }

  .btn-primary:hover {
    background: var(--color-primary-hover);
  }

  .btn-secondary {
    background: var(--btn-secondary-bg, var(--color-border));
    color: var(--btn-secondary-fg, var(--color-text-light));
  }

  .btn-secondary:hover {
    background: var(--btn-secondary-hover-bg, var(--color-border-hover));
  }
`;
