/**
 * Shows a server-rendered `<kanban-toast>` fragment in the page's toast area
 * (`<div id="toast-area" popover="manual">`). Used for requests that bypass
 * htmx's swapping. Re-showing the popover puts the area back on top of an
 * open modal dialog.
 */
export function appendToast(html: string) {
	const area = document.getElementById("toast-area");
	if (!area) return;
	area.insertAdjacentHTML("beforeend", html);
	if (area.matches(":popover-open")) area.hidePopover();
	area.showPopover();
}
