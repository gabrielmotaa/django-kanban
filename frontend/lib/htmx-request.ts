import { appendToast } from "./toast";

export type HtmxResult = { successful: boolean; html: string };

/**
 * Issues a request through htmx without swapping anything and resolves with
 * the raw response, so the caller decides how to apply it.
 *
 * `source` is the element the request is attributed to: htmx events (and the
 * web-components header listeners) fire on it and bubble up from there.
 */
export function htmxRequest(
	source: Element,
	verb: "get" | "patch" | "delete" | "post",
	url: string,
	values: Record<string, string> = {},
): Promise<HtmxResult> {
	return new Promise((resolve) => {
		// A custom handler skips htmx's error events, so network failures and
		// timeouts are reported here instead of leaving the promise pending.
		const controller = new AbortController();
		const fail = () => {
			controller.abort();
			resolve({ successful: false, html: "" });
		};
		source.addEventListener("htmx:sendError", fail, {
			signal: controller.signal,
		});
		source.addEventListener("htmx:timeout", fail, {
			signal: controller.signal,
		});
		window.htmx.ajax(verb, url, {
			source: source as HTMLElement,
			values,
			handler: (_elt: Element, info: unknown) => {
				// A custom handler replaces htmx's own response handling, which is
				// what sets `successful`; mirror its rule (status < 400).
				controller.abort();
				const { xhr } = info as { xhr: XMLHttpRequest };
				const successful = xhr.status < 400;
				if (!successful && xhr.getResponseHeader("X-Toast")) {
					appendToast(xhr.responseText);
				}
				resolve({ successful, html: xhr.responseText });
			},
		});
	});
}
