export type Palette = [hex: string, name: string][];

/**
 * Reads the color palette the server rendered on the enclosing
 * `<kanban-board colors='[["#64748b","Cinza"], ...]'>`.
 *
 * The palette lives in markup (single source of truth: `Column.COLOR_CHOICES`)
 * and descendants find it through `closest()`, so no page global is needed.
 */
export function readPalette(el: Element): Palette {
	const raw = el.closest("kanban-board")?.getAttribute("colors");
	if (!raw) return [];
	try {
		return JSON.parse(raw) as Palette;
	} catch {
		return [];
	}
}
