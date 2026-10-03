import { LitElement, type PropertyValues } from "lit";
import { sendWebComponentsHeader } from "./web-components-header";

/**
 * Base class for elements whose shadow root contains htmx markup.
 *
 * - processes the shadow root after every render (htmx does not look inside
 *   shadow roots on its own);
 * - makes requests issued from the element ask for web-component fragments;
 * - owns an `AbortSignal` that is aborted on disconnect, for listeners.
 */
export class HtmxElement extends LitElement {
	private disposer?: AbortController;

	protected get signal(): AbortSignal {
		if (!this.disposer) this.disposer = new AbortController();
		return this.disposer.signal;
	}

	override connectedCallback() {
		super.connectedCallback();
		this.disposer = new AbortController();
		sendWebComponentsHeader(this, this.disposer.signal);
	}

	override disconnectedCallback() {
		super.disconnectedCallback();
		this.disposer?.abort();
	}

	protected override updated(_changed: PropertyValues) {
		if (this.shadowRoot) {
			// biome-ignore lint/suspicious/noExplicitAny: htmx.process() accepts ShadowRoot at runtime but TS types don't reflect it
			window.htmx.process(this.shadowRoot as any);
		}
	}

	/** Focuses the first match of `selector` once the next render is done. */
	protected focusAfterRender(selector: string) {
		this.updateComplete.then(() => {
			this.shadowRoot?.querySelector<HTMLElement>(selector)?.focus();
		});
	}
}
