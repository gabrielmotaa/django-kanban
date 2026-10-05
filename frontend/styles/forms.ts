import { css } from "lit";

/** Shared text field. `--field-padding` tunes the inner spacing. */
export const forms = css`
  .field {
    width: 100%;
    padding: var(--field-padding, 8px);
    border: var(--nb-border-sm);
    border-radius: var(--radius-md);
    font-size: var(--font-size-lg);
    outline: none;
    box-sizing: border-box;
  }

  .field:focus {
    box-shadow: var(--shadow-sm);
  }
`;
