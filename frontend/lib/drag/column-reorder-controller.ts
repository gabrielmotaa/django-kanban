import type { ReactiveController, ReactiveControllerHost } from "lit";
import type { KanbanBoard } from "../../components/kanban-board";
import type { KanbanColumn } from "../../components/kanban-column";

/**
 * Makes a `<kanban-column>` draggable by its title (the header announces the
 * grab with `kanban-column-grab` / `kanban-column-release`) and lets other
 * dragged columns be positioned relative to it. Announces the final order
 * with `columnmove` when a column is dropped on it.
 */
export class ColumnReorderController implements ReactiveController {
	private disposer?: AbortController;

	constructor(private host: KanbanColumn & ReactiveControllerHost) {}

	private get board(): KanbanBoard {
		return this.host.closest("kanban-board") as KanbanBoard;
	}

	hostConnected() {
		this.disposer = new AbortController();
		const { signal } = this.disposer;
		const host = this.host;
		host.addEventListener(
			"kanban-column-grab",
			() => {
				host.draggable = true;
			},
			{ signal },
		);
		host.addEventListener(
			"kanban-column-release",
			() => {
				host.draggable = false;
			},
			{ signal },
		);
		host.addEventListener("dragstart", this.onDragStart, { signal });
		host.addEventListener("dragend", this.onDragEnd, { signal });
		host.addEventListener("dragover", this.onDragOver, { signal });
		host.addEventListener("drop", this.onDrop, { signal });
	}

	hostDisconnected() {
		this.disposer?.abort();
	}

	private onDragStart = (e: DragEvent) => {
		if (e.target !== this.host) return;

		const columns = [...this.board.querySelectorAll("kanban-column")];
		const index = columns.indexOf(this.host);

		this.host.dispatchEvent(
			new CustomEvent("kanban-column-dragstart", {
				bubbles: true,
				composed: true,
				detail: { type: "column", column: this.host, fromIndex: index },
			}),
		);

		requestAnimationFrame(() => this.host.classList.add("dragging-col"));
	};

	private onDragEnd = () => {
		this.host.classList.remove("dragging-col");
		this.host.removeAttribute("draggable");

		this.host.dispatchEvent(
			new CustomEvent("kanban-column-dragend", {
				bubbles: true,
				composed: true,
			}),
		);
	};

	private onDragOver = (e: DragEvent) => {
		const state = this.board.dragState;
		if (state?.type !== "column") return;

		const dragged = state.column;
		if (dragged === this.host) return;

		const box = this.host.getBoundingClientRect();
		const middleX = box.left + box.width / 2;
		const board = this.board;

		if (e.clientX < middleX) {
			board.insertBefore(dragged, this.host);
		} else {
			board.insertBefore(dragged, this.host.nextElementSibling);
		}
	};

	private onDrop = () => {
		const state = this.board.dragState;
		if (state?.type !== "column") return;

		const columns = [...this.board.querySelectorAll("kanban-column")];
		const toIndex = columns.indexOf(state.column);

		this.host.dispatchEvent(
			new CustomEvent("columnmove", {
				bubbles: true,
				composed: true,
				detail: {
					column_id: state.column.columnId,
					href: state.column.href,
					order: toIndex,
					fromIndex: state.fromIndex,
				},
			}),
		);
	};
}
