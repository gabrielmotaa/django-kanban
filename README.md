# Django Kanban

Um projeto de kanban board construído com **Django**, explorando duas abordagens de frontend em paralelo:

1. **Django Templates** — renderização server-side tradicional
2. **Web Components (Lit)** — custom elements carregados via bundle ESM, servidos como estáticos pelo Django

O objetivo central é comparar e integrar essas duas estratégias num mesmo projeto Django.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.14 · Django 6 |
| Gerenciador de pacotes Python | [uv](https://github.com/astral-sh/uv) |
| Frontend (Web Components) | [Lit](https://lit.dev/) · TypeScript |
| Hipermídia / Interatividade | [HTMX](https://htmx.org/) · [Alpine.js](https://alpinejs.dev/) |
| Bundler | Vite (library mode) |
| Linter / Formatter | Ruff · pyupgrade |
| Pre-commit hooks | uv-lock · ruff-check · ruff-format · pyupgrade |

---

## Estrutura do Projeto

```
django-kanban/
│
├── core/                        # Configurações do projeto Django
│   ├── settings.py
│   ├── urls.py                  # Rota raiz → inclui kanban.urls
│   ├── asgi.py
│   └── wsgi.py
│
├── kanban/                      # App principal
│   ├── views/
│   │   ├── templates.py         # View da página server-side (Django Templates)
│   │   └── components.py        # View da página de Web Components
│   ├── templates/
│   │   ├── base.html            # Layout base (blocos: title, content, extra_js…)
│   │   └── kanban/
│   │       ├── templates/index.html   # Página: abordagem Django Templates
│   │       └── components/index.html  # Página: abordagem Web Components (Lit)
│   ├── static/
│   │   └── kanban/
│   │       └── js/              # ← bundle gerado pelo Vite
│   ├── urls.py
│   ├── models.py
│   ├── apps.py
│   └── migrations/
│
├── frontend/                    # Código-fonte dos Web Components
│   ├── index.ts                 # Entry point — registra todos os custom elements
│   └── components/
│       ├── kanban-board.ts      # Componente <kanban-board> (Lit + TypeScript)
│       ├── kanban-column.ts     # Componente <kanban-column> (Lit + TypeScript)
│       └── kanban-card.ts       # Componente <kanban-card> (Lit + TypeScript)
│
├── package.json                 # Dependências Node (Lit, Vite, TypeScript)
├── tsconfig.json                # Config TypeScript (ES2021, decorators)
├── vite.config.ts               # Vite em library mode → output em kanban/static/
├── pyproject.toml               # Metadados Python + dependências uv
├── .pre-commit-config.yaml
└── manage.py
```

### Rotas disponíveis

| URL | View | Descrição |
|---|---|---|
| `/templates/` | `views/templates.py` | Página renderizada com Django Templates |
| `/components/` | `views/components.py` | Página com Web Components (Lit) |
| `/admin/` | Django Admin | Painel de administração |

---

## Setup

### Pré-requisitos

- Python 3.14+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 20+ e npm

### Instalação

```bash
# 1. Clonar o repositório
git clone <repo-url>
cd django-kanban

# 2. Criar o ambiente virtual e instalar dependências Python
uv sync

# 3. Instalar dependências Node
npm install

# 4. Aplicar migrações
uv run manage.py migrate

# 5. Carregar os dados iniciais (fixture)
uv run manage.py loaddata initial_data
```

---

## Desenvolvimento

### Backend (Django)

```bash
uv run manage.py runserver
```

### Frontend (Web Components)

```bash
# Watch mode: rebuilda automaticamente ao salvar arquivos em frontend/
npm run dev

# Build único (produção)
npm run build

# Checar tipos TypeScript sem buildar
npm run typecheck
```

O Vite compila `frontend/` e gera o bundle em `kanban/static/kanban/js/kanban-elements.js`, além de copiar as bibliotecas externas (`htmx.min.js` e `alpine.min.js`) para a mesma pasta.
### Testes

Para executar os testes unitários do Django:
```bash
uv run manage.py test
```

### Usando um Web Component nos templates Django

```html
{% load static %}

{% block extra_head %}
  <script src="{% static 'kanban/js/htmx.min.js' %}" defer></script>
  <script type="module" src="{% static 'kanban/js/kanban-elements.js' %}"></script>
{% endblock %}

{% block content %}
  <kanban-board title="Meu Board"></kanban-board>

  <!-- Exemplo de uso do HTMX -->
  <button hx-get="/components/" hx-target="#resultado" hx-swap="innerHTML">
    Carregar via HTMX
  </button>
  <div id="resultado"></div>
{% endblock %}
```

---

## Criando novos Web Components

1. Crie o componente em `frontend/components/meu-componente.ts`:

```typescript
import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("meu-componente")
export class MeuComponente extends LitElement {
  @property({ type: String }) label = "";

  render() {
    return html`<div>${this.label}</div>`;
  }
}
```

2. Exporte-o em `frontend/index.ts`:

```typescript
export * from "./components/meu-componente";
```

3. Rode `npm run build` (ou deixe `npm run dev` rodando em watch mode).

---

## Pre-commit Hooks

```bash
# Instalar os hooks (primeira vez)
uv run pre-commit install

# Rodar manualmente
uv run pre-commit run --all-files
```

Hooks configurados: `uv-lock` (lockfile atualizado), `ruff-check --fix`, `ruff-format`, `pyupgrade --py314-plus`.
