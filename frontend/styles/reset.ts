import { css } from "lit";

/**
 * The slice of the page reset (`reset.css`) that shadow roots need: border-box
 * sizing, and form controls inheriting the page font.
 */
export const reset = css`
  *, *::before, *::after {
    box-sizing: border-box;
  }

  input, button, select, textarea {
    font: inherit;
  }
`;
