# ParseDMARC Web GUI

A modern web-based interface for [parsedmarc](https://github.com/domainaware/parsedmarc) — transforming the CLI DMARC report parser into a user-friendly web application with a guided setup wizard, visual configuration, and report browsing.

## Features

- **Setup Wizard** — Guided first-run configuration (encryption key, admin credentials, SSL, server, database)
- **Multiple Mailbox Support** — IMAP, Microsoft Graph (Office 365), Gmail API, Maildir
- **Multiple Output Destinations** — Elasticsearch, OpenSearch, Splunk, Kafka, S3, Syslog, GELF, Webhooks
- **Automated Monitoring** — Background mailbox watching with APScheduler
- **File Upload Parsing** — Drag-and-drop individual DMARC report files (XML, GZ, ZIP, EML, MSG)
- **Report Browsing** — Filtered and paginated report viewer with full JSON detail
- **Connection Testing** — Test mailbox connections before saving
- **Secure Credential Storage** — All passwords and secrets encrypted with Fernet (unique key per installation)
- **SSL Certificate Management** — Self-signed, Let's Encrypt, or custom certificates with renewal support
- **Dashboard** — Stats overview, system health, recent jobs, quick actions

## Architecture

```
┌─────────────────────────────────────────┐
│              Browser (SPA)              │
│    Vue 3 + TypeScript + Tailwind CSS    │
│    Pinia state · Vue Router · Vite      │
└──────────────────┬──────────────────────┘
                   │ HTTP /api/*
┌──────────────────▼──────────────────────┐
│            FastAPI Backend               │
│  REST API · SQLAlchemy · APScheduler     │
│  Fernet Encryption · Certificate Mgmt   │
│  Serves frontend/dist/ as SPA           │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│       SQLite (encrypted credentials)     │
└─────────────────────────────────────────┘
```

### Backend (Python / FastAPI)

- **Framework**: FastAPI with async lifespan
- **Database**: SQLite with SQLAlchemy ORM (7 models)
- **Background Jobs**: APScheduler for mailbox monitoring
- **Security**: Fernet symmetric encryption for credentials, self-signed/LE/custom SSL
- **Parsing**: Wraps parsedmarc library for mailbox fetching and file parsing

### Frontend (Vue.js 3)

- **Framework**: Vue 3 with Composition API (`<script setup>`)
- **Language**: TypeScript
- **Styling**: Tailwind CSS (no component library)
- **State**: Pinia stores
- **Routing**: Vue Router with setup-guard (redirects to wizard if not configured)
- **Build**: Vite (output to `frontend/dist/`, served by backend)

## Quick Start

### Option A: Docker (Recommended)

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env and set PARSEDMARC_ENCRYPTION_KEY (or use the setup wizard to generate one)

# 2. Run
docker compose up -d

# 3. (Optional) Include Elasticsearch for report storage
docker compose --profile elasticsearch up -d
```

Open http://localhost:8000 — the setup wizard will guide you through initial configuration.

### Option B: Manual Setup

**Prerequisites:** Python 3.9+, Node.js 18+

```bash
# 1. Install backend dependencies
cd backend
pip install -r requirements.txt
pip install parsedmarc

# 2. Build the frontend
cd ../frontend
npm install
npm run build

# 3. Configure and run
cp .env.example .env
# Edit .env and set PARSEDMARC_ENCRYPTION_KEY
cd ../backend
python -m app.main
```

Open http://localhost:8000 — the setup wizard will guide you through initial configuration.

### Development Mode

For frontend hot-reload during development:

```bash
# Terminal 1: Backend
cd backend
python -m app.main

# Terminal 2: Frontend dev server (proxies /api to :8000)
cd frontend
npm run dev
```

Frontend dev server runs on http://localhost:3000 with API proxy to the backend.

## Project Structure

```
parsedmarc-gui/
├── backend/
│   ├── app/
│   │   ├── api/                # REST API endpoints
│   │   │   ├── setup.py        # Setup wizard (10 endpoints)
│   │   │   ├── mailbox_configs.py  # Mailbox CRUD + test connection
│   │   │   ├── output_configs.py   # Output CRUD
│   │   │   └── parsing.py      # Parse jobs, reports, file upload
│   │   ├── models/             # SQLAlchemy models (7)
│   │   ├── services/           # Business logic
│   │   │   ├── encryption_service.py
│   │   │   ├── certificate_service.py
│   │   │   ├── mailbox_service.py
│   │   │   ├── parsing_service.py
│   │   │   └── monitoring_service.py
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── db/session.py       # Database engine & session
│   │   ├── config.py           # Settings (env vars / Pydantic)
│   │   └── main.py             # FastAPI app, CORS, static files, SPA
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                # API client (fetch-based)
│   │   ├── types/              # TypeScript interfaces
│   │   ├── stores/             # Pinia stores (app, setup, mailboxes, outputs, parsing)
│   │   ├── composables/        # useApi, useToast, usePagination, useConfirmDialog
│   │   ├── router/             # Vue Router with setup guard
│   │   ├── layouts/            # AppLayout, BlankLayout
│   │   ├── components/
│   │   │   ├── ui/             # 12 base components (Button, Input, Modal, etc.)
│   │   │   ├── layout/         # Sidebar, Topbar
│   │   │   ├── data/           # DataTable, Pagination, FilterBar
│   │   │   ├── forms/          # FormSection, FormField, PasswordInput, FileDropZone
│   │   │   ├── mailbox/        # 4 type-specific settings forms
│   │   │   ├── output/         # 8 type-specific settings forms
│   │   │   └── report/         # ReportJsonViewer
│   │   └── views/
│   │       ├── setup/          # SetupWizard + 6 step components
│   │       ├── DashboardView.vue
│   │       ├── mailboxes/      # List + Create/Edit
│   │       ├── outputs/        # List + Create/Edit
│   │       ├── reports/        # List + Detail (JSON viewer)
│   │       ├── jobs/           # Job list with status filter
│   │       ├── upload/         # File upload with drag-and-drop
│   │       └── settings/       # System info + SSL certificate
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
├── .env.example
├── .gitignore
└── README.md
```

## Configuration

### Environment Variables

See `.env.example` for all options:

| Variable | Default | Description |
|----------|---------|-------------|
| `PARSEDMARC_ENCRYPTION_KEY` | *(required)* | Fernet key for credential encryption |
| `PARSEDMARC_GUI_USERNAME` | `admin` | Admin username |
| `PARSEDMARC_GUI_PASSWORD` | `changeme` | Admin password |
| `PARSEDMARC_DB_PATH` | `./data/parsedmarc.db` | SQLite database path |
| `PARSEDMARC_HOST` | `0.0.0.0` | Server bind address |
| `PARSEDMARC_PORT` | `8000` | Server port |
| `PARSEDMARC_CORS_ORIGINS` | `localhost:3000,8000` | Allowed CORS origins |
| `PARSEDMARC_LOG_LEVEL` | `INFO` | Logging level |

> **Note:** The setup wizard configures these on first run. Environment variables override wizard settings.

### Mailbox Types

| Type | Auth | Notes |
|------|------|-------|
| **IMAP** | Username/Password | Standard IMAP with SSL/TLS, configurable folder |
| **Microsoft Graph** | ClientSecret / DeviceCode / UsernamePassword | Azure AD app registration required |
| **Gmail** | OAuth2 | Google Cloud Console credentials file required |
| **Maildir** | Filesystem | Local Maildir directory path |

### Output Destinations

| Output | Protocol | Key Settings |
|--------|----------|-------------|
| **Elasticsearch** | REST | Hosts, auth, SSL, API key, monthly indexes |
| **OpenSearch** | REST | Hosts, auth, SSL, index suffix |
| **Splunk** | HEC | URL, token, index |
| **Kafka** | TCP | Bootstrap servers, per-type topics, SASL |
| **S3** | AWS SDK | Bucket, region, IAM or access keys |
| **Syslog** | UDP/TCP | Server, port |
| **GELF** | UDP/TCP | Server, port (Graylog) |
| **Webhook** | HTTP POST | URL, custom headers, timeout |

## API Endpoints

Once running, full API docs are at http://localhost:8000/docs (Swagger UI).

| Prefix | Description |
|--------|-------------|
| `GET /api/health` | Health check |
| `GET /api/system/info` | System information |
| `/api/setup/*` | Setup wizard (status, encryption, SSL, admin, server, DB, complete) |
| `/api/configs/mailboxes/*` | Mailbox config CRUD + test connection |
| `/api/configs/outputs/*` | Output config CRUD |
| `/api/parse/*` | Parse from mailbox, upload file, list jobs/reports |
| `/api/dashboard/*` | Aggregated stats, activity feed |
| `/api/monitoring/*` | Start/stop monitoring jobs, status |
| `/api/test/*` | Output destination connection testing |

## Security

- **Credential Encryption**: All passwords, API keys, and secrets are encrypted at rest using Fernet symmetric encryption. Each installation generates a unique encryption key during setup.
- **SSL/TLS**: Supports self-signed certificates (auto-generated), Let's Encrypt, or custom certificates.
- **Database**: SQLite with encrypted sensitive fields. Database path is configurable.

## License

Apache License 2.0 (same as parsedmarc)

## Credits

Built on top of [parsedmarc](https://github.com/domainaware/parsedmarc) by Sean Whalen.
