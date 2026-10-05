# Django Kanban

![Kanban Board](docs/screenshot.png)

Um projeto de kanban board construído com **Django**, explorando duas abordagens de frontend em paralelo:

1. **Django Templates** — renderização server-side tradicional
2. **Web Components (Lit)** — custom elements carregados via bundle ESM, servidos como estáticos pelo Django

O objetivo central é comparar e integrar essas duas estratégias num mesmo projeto Django.

---

## Setup

### Pré-requisitos

- Python 3.14+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 20.19+ ou 22.12+ (exigido pelo Vite 8) e npm

### Instalação

```bash
# 1. Clonar o repositório
git clone https://github.com/gabrielmotaa/django-kanban
cd django-kanban

# 2. Criar o ambiente virtual e instalar dependências Python
uv sync

# 3. Instalar dependências Node
npm install

# 4. Aplicar migrações
uv run manage.py migrate

# 5. Carregar os dados iniciais (fixture)
uv run manage.py loaddata initial_data

# 6. Gerar o bundle do frontend (Web Components, htmx e Alpine)
npm run build
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

# Lint (Biome)
npm run lint

# Lint + auto-fix (safe fixes)
npm run lint:fix
```

O Vite compila `frontend/` e gera o bundle em `kanban/static/kanban/js/kanban-elements.js`, além de copiar as bibliotecas externas (`htmx.min.js` e `alpine.min.js`) para a mesma pasta.

### Testes

O projeto possui testes unitários (models/views) e testes de integração de ponta a ponta (E2E) usando Playwright.

#### 1. Instalar os navegadores do Playwright (necessário apenas uma vez):
```bash
uv run playwright install chromium
```

#### 2. Executar testes unitários (rápidos, deseleciona integração por padrão):
```bash
uv run pytest
```

#### 3. Executar testes de integração (browser real rodando E2E):
```bash
# Execução headless (em segundo plano)
uv run pytest -m integration

# Execução headed (abrindo janela visual do navegador) com 1 segundo de intervalo para assistir
uv run pytest -m integration --headed --slowmo 1000
```

#### 4. Paridade visual entre as duas versões

`test_visual_parity` abre cada estado da UI (board, menus, dialog, popovers…) em `/templates/` e em `/components/`, tira um screenshot de cada e compara pixel a pixel no próprio navegador. Qualquer diferença de estilo entre `templates.css` e os estilos dos componentes Lit faz o teste falhar; os screenshots e uma imagem de diff (pixels divergentes em magenta) são salvos para depuração:

```bash
PARITY_SCREENSHOTS_DIR=/tmp/parity uv run pytest -m integration -k visual_parity
```

---

## Pre-commit Hooks

```bash
# Instalar os hooks (primeira vez)
uvx pre-commit install

# Rodar manualmente
uvx pre-commit run --all-files
```
