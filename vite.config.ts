import { defineConfig } from "vite";
import { resolve } from "path";
import { copyFileSync, mkdirSync } from "fs";

function copyExternalLibs() {
  return {
    name: "copy-external-libs",
    closeBundle() {
      const dest = "kanban/static/kanban/js";
      mkdirSync(dest, { recursive: true });
      copyFileSync(
        "node_modules/htmx.org/dist/htmx.min.js",
        `${dest}/htmx.min.js`,
      );
      copyFileSync(
        "node_modules/alpinejs/dist/cdn.min.js",
        `${dest}/alpine.min.js`,
      );
      console.log("external libraries copied to", dest);
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
  plugins: [copyExternalLibs()],
});
