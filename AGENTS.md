# AGENTS.md - Guide for AI Agents

This document serves as a quick reference for the architecture, commands, and conventions adopted in the **django-kanban** repository to guide future AI development agents.

---

## Tech Stack

*   **Backend:** Python 3.14+ · Django 6.0+
*   **Python Package Manager:** [uv](https://github.com/astral-sh/uv)
*   **Frontend (Web Components Approach):** [Lit](https://lit.dev/) + TypeScript
*   **Interactivity (Django Templates Approach):** [HTMX](https://htmx.org/) + [Alpine.js](https://alpinejs.dev/)
*   **Asset Bundler:** Vite (runs in library mode, compiling TypeScript/Lit and copying `htmx.min.js` and `alpine.min.js` to the Django static directory)
*   **Code Quality:** Ruff (linter and formatter) + pyupgrade

---

## Project Structure

*   `core/` - Core Django configuration (`settings.py`, `urls.py`).
*   `kanban/` - Main Django Kanban application:
    *   `fixtures/initial_data.json` - Initial database seed data for SQLite.
    *   `forms.py` - Django forms used to validate request data.
    *   `models.py` - Database models (`Board`, `Column`, `Card`).
    *   `tests/` - Unit tests (`test_models.py`, `test_views.py`) and browser integration tests (`test_integration.py`).
    *   `views.py` - Route handlers implemented as Class-Based Views (CBVs).
    *   `static/kanban/` - Compiled assets copied by Vite.
    *   `templates/kanban/` - Django HTML template files.
*   `frontend/` - TypeScript source code for Web Components (Lit):
    *   `index.ts` - Entry point (registers all custom elements).
    *   `components/` - Individual component implementations (`kanban-board.ts`, `kanban-column.ts`, `kanban-card.ts`, `kanban-board-title.ts`).

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
3.  **`Card`**:
    *   ForeignKey to `Column` (`related_name="cards"`, Cascade Delete).
    *   `title` (CharField, max 200)
    *   `description` (TextField, optional)
    *   `order` (PositiveIntegerField)
    *   `created_at` / `updated_at` (DateTimeField, auto populated)

---

## Rules and Conventions

### 1. Models and Forms
*   **Strict Validation:** Ensure all POST/PATCH request inputs are validated through Django Forms defined in [forms.py](file:///Users/gabrieldamota/Code/django-kanban/kanban/forms.py) before updating or creating models.

### 2. Django Admin
*   All database models must be registered in [admin.py](file:///Users/gabrieldamota/Code/django-kanban/kanban/admin.py).

### 3. Tests
*   Always ensure unit test coverage in [kanban/tests/](file:///Users/gabrieldamota/Code/django-kanban/kanban/tests/) for any new model properties, form validations, views, or endpoints.
*   Template tests must verify error handling paths (e.g. invalid form submits, missing parameters) in addition to success paths.
