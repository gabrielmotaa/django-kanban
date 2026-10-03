/**
 * Makes every htmx request issued from `host` (including from its shadow
 * root, slotted children and descendants) ask the server for web-component
 * fragments. htmx events are composed, so a listener on the host sees them.
 */
export function sendWebComponentsHeader(
	host: HTMLElement,
	signal: AbortSignal,
) {
	host.addEventListener(
		"htmx:configRequest",
		(event) => {
			(event as CustomEvent).detail.headers["X-Web-Components"] = "true";
		},
		{ signal },
	);
}
