import type htmx from "htmx.org";

declare global {
	interface Window {
		htmx: typeof htmx;
		urls: {
			cardCreate: string;
			cardDetail: string;
			columnCreate: string;
			columnDetail: string;
			boardDetail: string;
		};
		colorChoices: [string, string][];
	}
}
