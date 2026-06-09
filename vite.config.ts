import { defineConfig } from "vite";
import { resolve } from "path";
import { copyFileSync, mkdirSync } from "fs";

function copyHtmx() {
  return {
    name: "copy-htmx",
    closeBundle() {
      const dest = "kanban/static/kanban/js";
      mkdirSync(dest, { recursive: true });
      copyFileSync(
        "node_modules/htmx.org/dist/htmx.min.js",
        `${dest}/htmx.min.js`,
      );
    },
  };
}

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, "frontend/index.ts"),
      name: "KanbanElements",
      fileName: "kanban-elements",
      formats: ["es"],
    },
    outDir: "kanban/static/kanban/js",
    emptyOutDir: true,
    rollupOptions: {
      external: [],
    },
  },
  plugins: [copyHtmx()],
});
