# ProMan — Kanban Board Application

A Trello-inspired project management tool with public/private boards, customizable status columns, task cards with drag-and-drop, and user authentication. Built as a team project during the [Codecool](https://codecool.com/) bootcamp (2023).

> **PL:** Narzędzie do zarządzania zadaniami inspirowane Trello — tablice publiczne i prywatne, konfigurowalne kolumny statusów, karty zadań z obsługą drag and drop oraz system rejestracji i logowania. Projekt zespołowy wykonany podczas bootcampu Codecool (2023).

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3, Flask |
| **Database** | PostgreSQL (psycopg2) |
| **Auth** | bcrypt (password hashing), Flask sessions |
| **Frontend** | Vanilla JavaScript (ES6 modules), Jinja2 templates |
| **Styling** | CSS, Bootstrap (accordion layout) |

## Architecture

```
main.py                          ← Flask routing (typed, NumPy-style docstrings)
├── data_handler/
│   ├── __init__.py              ← package facade: exposes handlers as dh.boards, dh.cards, ...
│   ├── board_handler.py         ← board CRUD queries
│   ├── card_handler.py          ← card CRUD queries
│   ├── status_handler.py        ← status CRUD queries
│   ├── user_handler.py          ← registration, login, user queries
│   └── connection_manager.py    ← DB connection layer (pooled, parameterized queries)
└── static/js/
    ├── data/
    │   └── dataHandler.js       ← REST API client (fetch wrappers)
    ├── controller/
    │   ├── boardsManager.js     ← board logic
    │   ├── cardsManager.js      ← card logic
    │   ├── statusesManager.js   ← status column logic
    │   ├── usersManager.js      ← auth UI logic
    │   └── dragHandler.js       ← drag-and-drop between columns
    └── view/
        ├── domManager.js        ← DOM manipulation
        └── htmlFactory.js       ← HTML template factory
```

**Backend** follows a layered design: routes in `main.py` delegate to domain-specific handlers in `data_handler/`, which share a single database access layer in `connection_manager.py` (psycopg2 connection pool). The package `__init__.py` acts as a facade, so routes reach the handlers through one import (`import data_handler as dh`, then `dh.boards`, `dh.cards`). All SQL queries use psycopg2 parameterized statements to prevent injection.

**Frontend** is organized in an MVC-like pattern without any framework — `data/` handles API communication, `controller/` manages business logic, and `view/` owns DOM rendering via a template factory.

## Database Schema

```
boards ──┬── board_statuses ──── statuses
         │
         ├── cards (board_id, status_id, card_order)
         │
         └── user_boards (board_id, user_id, user_role[])

users (id, username, email, password[bcrypt], is_admin)
```

- **boards** ↔ **statuses**: many-to-many via `board_statuses` (with `status_order`)
- **cards**: belong to a board and a status, ordered by `card_order`
- **user_boards**: ownership/role mapping for private board access control
- Full schema dump: [`data/proman_database_dump.sql`](data/proman_database_dump.sql)

## Features

- 📋 **Boards** — create, rename, delete; toggle public/private visibility
- 📊 **Status columns** — add custom columns per board, rename, reorder, delete
- 🃏 **Cards** — create, edit, archive; ordered within columns
- 🔀 **Drag and drop** — move cards between status columns
- 🔐 **Authentication** — registration with bcrypt-hashed passwords, session-based login
- 👁️ **Private boards** — visible only to the owner

## Authorship

Team project built with [Zachiel](https://github.com/Zachiel) during the Codecool bootcamp, using a professional Git workflow on the CodecoolGlobal organization: feature branches → pull requests → code review → merge. The initial repository contained a starter scaffold provided by Codecool (basic project structure and a few stub functions).

Zachiel focused on backend infrastructure, the core drag-and-drop engine, and visual styling. What I worked on:

- **Authentication (full stack)** — server-side registration, login flow, bcrypt password hashing, Flask sessions, form validation with regex, login/registration modals
- **Board management** — adding public and private boards, frontend fetch integration, automatic default status columns for new boards, private board visibility for owners
- **Card management** — adding new cards with frontend rendering and backend persistence
- **Status columns** — adding, deleting, and deduplicating statuses
- **Drag-and-drop extensions** — extended `dragHandler` to support dragging newly created cards and statuses (not just pre-loaded ones)
- **Bug fixes** — logout handling for deleted users, error messages for anonymous board creation, message-box cleanup
- **HTML foundation** — base layout, accordion structure, modal system (extending a general template)
- **PR reviews** — reviewed and merged pull requests as the repository maintainer

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/MateuszPiszczatowski/codecool_proman.git
   cd codecool_proman
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**
   ```bash
   # Create the database, then load the schema and seed data:
   psql -U postgres -c "CREATE DATABASE cc_proman;"
   psql -U postgres -d cc_proman -f data/proman_database_dump.sql
   ```

5. **Configure environment variables**
   ```bash
   # Copy the template and fill in your values:
   cp .env.template .env
   ```
   ```ini
   MY_PSQL_DBNAME=cc_proman
   MY_PSQL_USER=postgres
   MY_PSQL_HOST=localhost
   MY_PSQL_PASSWORD=your_password
   FLASK_SECRET_KEY=your_secret_key
   ```

6. **Run the application**
   ```bash
   python main.py
   ```
   The app will be available at `http://localhost:5000`.

---

## Autorstwo (PL)

Projekt zespołowy zrealizowany wspólnie z [Zachiel](https://github.com/Zachiel) podczas bootcampu Codecool, w profesjonalnym workflow Git na organizacji CodecoolGlobal: feature branch → pull request → code review → merge. Repozytorium startowe zawierało szkielet projektu dostarczony przez Codecool (struktura katalogów i kilka stubów funkcji).

Zachiel skupił się na infrastrukturze backendu, silniku drag-and-drop i stylowaniu. Pracowałem głównie nad:

- **Autoryzacja (full stack)** — rejestracja po stronie serwera, logowanie, hashowanie haseł bcrypt, sesje Flask, walidacja formularzy z regex, modale logowania/rejestracji
- **Zarządzanie tablicami** — dodawanie tablic publicznych i prywatnych, integracja fetch z frontendu, automatyczne kolumny domyślne, widoczność tablic prywatnych tylko dla właściciela
- **Zarządzanie kartami** — dodawanie kart z renderowaniem na froncie i zapisem w bazie
- **Kolumny statusów** — dodawanie, usuwanie i deduplikacja statusów
- **Rozszerzenie drag-and-drop** — obsługa przeciągania nowo utworzonych kart i statusów
- **Poprawki błędów** — wylogowanie usuniętych użytkowników, komunikaty przy anonimowym tworzeniu tablic, czyszczenie message-box
- **Fundament HTML** — layout bazowy, struktura akordeonowa, system modali (rozszerzanie szablonu bazowego)
- **Recenzje PR** — recenzowanie i scalanie pull requestów jako maintainer repozytorium
