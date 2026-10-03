import { css } from "lit";

/** Shared text field. `--field-padding` tunes the inner spacing. */
export const forms = css`
  .field {
    width: 100%;
    padding: var(--field-padding, 8px);
    border: 1px solid var(--color-input-border);
    border-radius: var(--radius-md);
    font-size: var(--font-size-lg);
    outline: none;
    box-sizing: border-box;
  }

  .field:focus {
    border-color: var(--color-primary);
  }
`;
