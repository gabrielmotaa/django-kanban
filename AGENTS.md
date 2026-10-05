# AGENTS.md - Guide for AI Agents

This document serves as a quick reference for the architecture, commands, and conventions adopted in the **django-kanban** repository to guide future AI development agents.

---

## Tech Stack

*   **Backend:** Python 3.14+ · Django 6.0+
*   **Python Package Manager:** [uv](https://github.com/astral-sh/uv)
*   **Frontend (Web Components Approach):** [Lit](https://lit.dev/) + TypeScript
*   **Interactivity (Django Templates Approach):** [HTMX](https://htmx.org/) + [Alpine.js](https://alpinejs.dev/)
*   **Asset Bundler:** Vite (runs in library mode, compiling TypeScript/Lit and copying `htmx.min.js` and `alpine.min.js` to the Django static directory)
*   **Code Quality:** Ruff (linter and formatter) + pyupgrade · [Biome](https://biomejs.dev/) (TypeScript linter and formatter)

---

## Project Structure

*   `core/` - Core Django configuration (`settings.py`, `urls.py`).
*   `kanban/` - Main Django Kanban application:
    *   `fixtures/initial_data.json` - Initial database seed data for SQLite.
    *   `forms.py` - Django forms used to validate request data.
    *   `models.py` - Database models (see below).
    *   `activity.py` - `record_activity()` writes a card's history; activity messages are rendered here (pt-BR).
    *   `middleware.py` - Sets `request.web_components` from the `X-Web-Components` header.
    *   `utils.py` - Shared view helpers (`template_for_request`, `ApiError`, `error_response` with toast).
    *   `views.py` - Route handlers implemented as Class-Based Views (CBVs).
    *   `tests/` - Unit tests (`test_*.py`) and Playwright browser tests: `test_integration.py` and `test_parity.py` (aria + pixel-diff parity between both UIs, page object in `parity.py`).
    *   `static/kanban/css/` - `theme.css` (design tokens, neobrutalism), `templates.css` (templates UI), `components.css`, `home.css`. `static/kanban/js/` is Vite output (gitignored).
    *   `templates/kanban/templates/` and `templates/kanban/components/` - Fragments of each UI version (`/templates/` and `/components/`).
*   `frontend/` - TypeScript source code for Web Components (Lit):
    *   `index.ts` - Entry point (registers all custom elements).
    *   `components/` - One `kanban-*.ts` file per custom element (board, column, card, card dialog, labels, due date, checklists, comments…).
    *   `lib/` - Shared helpers (htmx requests, drag controllers, palette, toasts).
    *   `styles/` - Shared Lit styles (`buttons`, `forms`, `menu`, `reset`).

---

## Useful Commands

### Backend and Database
```bash
# Sync python dependencies from the lockfile
uv sync

# Run database migrations
uv run manage.py migrate

# Seed: populate the database with demo data (required for Board id=1)
uv run manage.py loaddata initial_data

# Start the Django development server
uv run manage.py runserver

# Run all unit tests (skips integration tests by default)
uv run pytest

# Run integration/browser tests explicitly (requires playwright)
uv run pytest -m integration

# Run unit tests with coverage report
uv run pytest --cov=kanban

# Run unit tests and show missing lines in coverage report
uv run pytest --cov=kanban --cov-report=term-missing
```

### Frontend (Lit / Vite)
```bash
# Install npm dependencies
npm install

# Build and watch for changes (Watch Mode)
npm run dev

# Production build
npm run build

# Typecheck TypeScript files
npm run typecheck

# Lint TypeScript (Biome)
npm run lint

# Format TypeScript (Biome)
npm run format

# Lint + format with auto-fix (safe fixes only)
npm run lint:fix
```

---

## Data Models (kanban/models.py)

1.  **`Board`**:
    *   `title` (CharField, max 100)
    *   `created_at` (DateTimeField, auto populated)
2.  **`Column`**:
    *   ForeignKey to `Board` (`related_name="columns"`, Cascade Delete).
    *   `title` (CharField, max 100)
    *   `order` (PositiveIntegerField)
    *   `color` (CharField, default `"#64748b"`)
    *   Properties: `fg_color` (returns contrasting text color for accessibility).
    *   Constants: `COLOR_CHOICES` (available colors).
3.  **`Label`**: ForeignKey to `Board` (`related_name="labels"`); `name` (max 30, may be blank), `color` (one of `COLOR_CHOICES`). Properties: `fg_color`, `color_name`.
4.  **`Card`**:
    *   ForeignKey to `Column` (`related_name="cards"`, Cascade Delete).
    *   `title` (CharField, max 200), `description` (TextField, blank)
    *   `labels` (ManyToMany to `Label`), `due_date` (DateField, optional), `completed` (BooleanField)
    *   `order` (PositiveIntegerField), `created_at` / `updated_at`
    *   Properties computed on the server for both UIs: `due_status` / `due_label` / `due_chip`, `checklist_*`, `comment_count` / `comment_label`; `timeline()` merges comments and activity.
5.  **`Checklist`** (FK `Card`, `related_name="checklists"`; `title`, `order`; `done_count`, `total_count`, `percent`) and **`ChecklistItem`** (FK `Checklist`, `related_name="items"`; `text`, `done`, `order`).
6.  **`Comment`** (FK `Card`, `related_name="comments"`; `text`, timestamps) and **`Activity`** (FK `Card`, `related_name="activities"`; `kind`, `data` JSON, `created_at`; `message` rendered by `activity.py`). No authentication, so neither has an author.

---

## Rules and Conventions

### 1. Models and Forms
*   **Strict Validation:** Ensure all POST/PATCH request inputs are validated through Django Forms defined in [forms.py](file:///Users/gabrieldamota/Code/django-kanban/kanban/forms.py) before updating or creating models.

### 2. Django Admin
*   All database models must be registered in [admin.py](file:///Users/gabrieldamota/Code/django-kanban/kanban/admin.py).

### 3. TypeScript Linting (Biome)
*   Use `npm run lint` to check for issues and `npm run lint:fix` to apply safe auto-fixes.
*   To suppress a rule on a specific line, use a `// biome-ignore lint: <reason>` comment (prefer the broad `lint` category over a specific rule unless targeting a single rule).

### 4. UI Parity
*   Every feature exists in both UIs and must look and behave the same. Style changes go to both `templates.css` and the Lit component styles, using the tokens in `theme.css`; `test_visual_parity` compares screenshots of both versions pixel by pixel.

### 5. Tests
*   Always ensure unit test coverage in [kanban/tests/](file:///Users/gabrieldamota/Code/django-kanban/kanban/tests/) for any new model properties, form validations, views, or endpoints.
*   Template tests must verify error handling paths (e.g. invalid form submits, missing parameters) in addition to success paths.
