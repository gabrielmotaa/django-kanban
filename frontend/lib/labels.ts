import { closestAcrossShadow } from "./palette";

export type LabelDef = {
	id: number;
	name: string;
	color: string;
	fg: string;
	colorName: string;
	href: string;
};

type LabelHost = Element & { labels?: LabelDef[] };

function boardOf(el: Element): LabelHost | null {
	return closestAcrossShadow(el, "kanban-board");
}

/** The board's label registry (definitions, in label order). */
export function readLabels(el: Element): LabelDef[] {
	return boardOf(el)?.labels ?? [];
}

/** Ids from a `labels="3,5"` attribute, resolved against the registry (label order). */
export function resolveLabels(el: Element, ids: string): LabelDef[] {
	const wanted = new Set(
		ids
			.split(",")
			.filter(Boolean)
			.map((id) => Number(id)),
	);
	return readLabels(el).filter((label) => wanted.has(label.id));
}

/** Re-renders `host` whenever the board's registry changes. */
export function watchLabels(
	host: Element & { requestUpdate(): void },
	signal: AbortSignal,
) {
	boardOf(host)?.addEventListener(
		"kanban-labels-changed",
		() => host.requestUpdate(),
		{ signal },
	);
}
