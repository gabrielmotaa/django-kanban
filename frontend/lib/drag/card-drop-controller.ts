import type { ReactiveController, ReactiveControllerHost } from "lit";
import type { KanbanBoard } from "../../components/kanban-board";
import type { KanbanCard } from "../../components/kanban-card";
import type { KanbanColumn } from "../../components/kanban-column";

/**
 * Makes a `<kanban-column>` a drop zone for cards: highlights it, keeps the
 * dragged card positioned among the column's cards and announces the move
 * (`cardmove`) when the card is dropped. The drag state lives in the board.
 */
export class CardDropController implements ReactiveController {
	private disposer?: AbortController;

	constructor(private host: KanbanColumn & ReactiveControllerHost) {}

	private get board(): KanbanBoard {
		return this.host.closest("kanban-board") as KanbanBoard;
	}

	hostConnected() {
		this.disposer = new AbortController();
		const { signal } = this.disposer;
		this.host.addEventListener("dragenter", this.onDragEnter, { signal });
		this.host.addEventListener("dragleave", this.onDragLeave, { signal });
		this.host.addEventListener("dragover", this.onDragOver, { signal });
		this.host.addEventListener("drop", this.onDrop, { signal });
	}

	hostDisconnected() {
		this.disposer?.abort();
	}

	private onDragEnter = () => {
		if (this.board.dragState?.type !== "card") return;
		this.host.classList.add("drag-over");
	};

	private onDragLeave = (e: DragEvent) => {
		if (this.board.dragState?.type !== "card") return;
		if (!this.host.contains(e.relatedTarget as Node)) {
			this.host.classList.remove("drag-over");
		}
	};

	private onDragOver = (e: DragEvent) => {
		// Always allow dropping; column reordering shares this event.
		e.preventDefault();

		const state = this.board.dragState;
		if (state?.type !== "card") return;

		const after = this.cardAfterPosition(e.clientY);
		if (!after) {
			this.host.appendChild(state.card);
		} else {
			this.host.insertBefore(state.card, after);
		}
	};

	private onDrop = () => {
		this.host.classList.remove("drag-over");

		const state = this.board.dragState;
		if (state?.type !== "card") return;

		const cards = [...this.host.querySelectorAll("kanban-card")];
		const toIndex = cards.indexOf(state.card);

		if (state.fromColumn === this.host && state.fromIndex === toIndex) return;

		if (state.fromColumn !== this.host) state.fromColumn.updateOrders();
		this.host.updateOrders();

		this.host.dispatchEvent(
			new CustomEvent("cardmove", {
				bubbles: true,
				composed: true,
				detail: {
					card_id: state.card.cardId,
					href: state.card.href,
					column_id: this.host.columnId,
					order: toIndex,
				},
			}),
		);
	};

	private cardAfterPosition(mouseY: number): Element | null {
		const cards = [
			...this.host.querySelectorAll<KanbanCard>("kanban-card:not(.dragging)"),
		];

		let closest: Element | null = null;
		let closestOffset = Number.NEGATIVE_INFINITY;

		for (const card of cards) {
			const box = card.getBoundingClientRect();
			const offset = mouseY - box.top - box.height / 2;
			if (offset < 0 && offset > closestOffset) {
				closestOffset = offset;
				closest = card;
			}
		}

		return closest;
	}
}
