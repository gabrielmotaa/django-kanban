/**
 * Shows a server-rendered `<kanban-toast>` fragment in the page's toast area
 * (`<div id="toast-area">`). Used for requests that bypass htmx's swapping.
 */
export function appendToast(html: string) {
	document.getElementById("toast-area")?.insertAdjacentHTML("beforeend", html);
}
