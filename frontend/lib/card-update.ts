/**
 * htmx resolves out-of-band targets inside the root of the element that sent
 * the request, so an OOB `<kanban-card id="card-N">` cannot reach the card
 * front from inside a shadow root. The response still carries the card
 * element; whoever receives it announces it and `<kanban-board>` applies it.
 */
export function announceCardUpdate(host: Element, html: string) {
	host.dispatchEvent(
		new CustomEvent("kanban-card-updated", {
			bubbles: true,
			composed: true,
			detail: { html },
		}),
	);
}

/** Replaces the card front matching the `<kanban-card id>` found in `html`. */
export function applyCardUpdate(board: Element, html: string) {
	const template = document.createElement("template");
	template.innerHTML = html.trim();
	const incoming = template.content.querySelector("kanban-card[id]");
	if (!incoming) return;
	board.querySelector(`#${incoming.id}`)?.replaceWith(incoming);
}
