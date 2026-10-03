import { css } from "lit";

/** Form controls inherit the page font instead of the browser default. */
export const reset = css`
  input, button, select, textarea {
    font: inherit;
  }
`;
