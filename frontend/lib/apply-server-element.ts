/**
 * Applies a server-sent custom element to a host that must keep its children.
 *
 * The server stays the source of truth for the element's state (its
 * attributes), but an `outerHTML` swap would replace the host and lose the
 * light-DOM children the response deliberately leaves out (e.g. the cards of
 * a column). So the response is parsed and only its attributes are copied.
 * Attributes are only added or updated, never removed (client-managed ones
 * such as `order` or `role` must survive).
 */
export function applyServerElement(host: Element, html: string) {
	const template = document.createElement("template");
	template.innerHTML = html.trim();
	const incoming = template.content.querySelector(host.localName);
	if (!incoming) return;
	for (const { name, value } of Array.from(incoming.attributes)) {
		if (host.getAttribute(name) !== value) host.setAttribute(name, value);
	}
}
