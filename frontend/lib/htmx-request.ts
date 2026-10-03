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
	verb: "patch" | "delete" | "post",
	url: string,
	values: Record<string, string> = {},
): Promise<HtmxResult> {
	return new Promise((resolve) => {
		window.htmx.ajax(verb, url, {
			source: source as HTMLElement,
			values,
			handler: (_elt: Element, info: unknown) => {
				// A custom handler replaces htmx's own response handling, which is
				// what sets `successful`; mirror its rule (status < 400).
				const { xhr } = info as { xhr: XMLHttpRequest };
				resolve({ successful: xhr.status < 400, html: xhr.responseText });
			},
		});
	});
}
