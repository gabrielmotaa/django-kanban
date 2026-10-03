export type Palette = [hex: string, name: string][];

/** `closest()` that also climbs out of shadow roots through their hosts. */
export function closestAcrossShadow(el: Element, selector: string) {
	let current: Element | null = el;
	while (current) {
		const found = current.closest(selector);
		if (found) return found;
		const root = current.getRootNode();
		current = root instanceof ShadowRoot ? root.host : null;
	}
	return null;
}

/**
 * Reads the color palette the server rendered on the enclosing
 * `<kanban-board colors='[["#64748b","Cinza"], ...]'>`.
 *
 * The palette lives in markup (single source of truth: `Column.COLOR_CHOICES`)
 * and descendants find it through `closestAcrossShadow()`, so no page global
 * is needed.
 */
export function readPalette(el: Element): Palette {
	const raw = closestAcrossShadow(el, "kanban-board")?.getAttribute("colors");
	if (!raw) return [];
	try {
		return JSON.parse(raw) as Palette;
	} catch {
		return [];
	}
}
