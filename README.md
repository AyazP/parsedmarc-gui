# ParseDMARC Web GUI

A modern web-based interface for [parsedmarc](https://github.com/domainaware/parsedmarc) — transforming the CLI DMARC report parser into a user-friendly web application with a guided setup wizard, visual configuration, and report browsing.

## Features

- **Setup Wizard** — Guided 6-step first-run configuration (encryption key, admin credentials, SSL, server, database, review)
- **JWT Authentication** — Secure login with HttpOnly cookie-based JWT tokens and CSRF double-submit cookie protection
- **Multiple Mailbox Support** — IMAP, Microsoft Graph (Office 365), Gmail API, Maildir
- **Multiple Output Destinations** — Elasticsearch, OpenSearch, Splunk, Kafka, S3, Syslog, GELF, Webhooks
- **Automated Monitoring** — Background mailbox watching with APScheduler
- **File Upload Parsing** — Drag-and-drop individual DMARC report files (XML, GZ, ZIP, EML, MSG)
- **Report Browsing** — Filtered and paginated report viewer with full JSON detail
- **Connection Testing** — Test mailbox and output connections before saving
- **Secure Credential Storage** — All passwords and secrets encrypted with Fernet (unique key per installation)
- **SSL Certificate Management** — Self-signed, Let's Encrypt (HTTP-01 and DNS-01 challenges), or custom certificate upload with validation
- **Dashboard** — Stats overview, system health, recent jobs, quick actions
- **Database Flexibility** — SQLite (default), PostgreSQL, or MySQL with built-in migration and purge tools
- **Update Checker** — Automatic GitHub release checks with configurable intervals
- **Dark Mode** — System preference auto-detection with manual toggle

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
│   SQLite / PostgreSQL / MySQL            │
│   (encrypted credentials at rest)        │
└─────────────────────────────────────────┘
```

### Backend (Python / FastAPI)

- **Framework**: FastAPI with async lifespan
- **Database**: SQLAlchemy ORM (7 models) — SQLite, PostgreSQL, or MySQL
- **Background Jobs**: APScheduler for mailbox monitoring and update checks
- **Security**: Fernet symmetric encryption for credentials, bcrypt password hashing, JWT authentication with HttpOnly cookies, CSRF double-submit cookie protection, security headers middleware, rate limiting, SSRF protection
- **Parsing**: Wraps parsedmarc library for mailbox fetching and file parsing

### Frontend (Vue.js 3)

- **Framework**: Vue 3 with Composition API (`<script setup>`)
- **Language**: TypeScript
- **Styling**: Tailwind CSS with dark mode support (class-based toggle)
- **State**: Pinia stores (app, auth, setup, mailboxes, outputs, parsing, updates)
- **Routing**: Vue Router with auth guard (redirects to login) and setup guard (redirects to wizard if not configured)
- **Build**: Vite (output to `frontend/dist/`, served by backend)

## Quick Start

### Option A: Docker (Recommended)

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env and set PARSEDMARC_ENCRYPTION_KEY (or use the setup wizard to generate one)

# 2. Run
docker compose up -d

# 3. (Optional) Include Elasticsearch or OpenSearch for report storage
docker compose --profile elasticsearch up -d
# or
docker compose --profile opensearch up -d
```

Open http://localhost:8000 — the setup wizard will guide you through initial configuration.

The Docker image is also available from GitHub Container Registry:

```bash
docker pull ghcr.io/ayazp/parsedmarc-gui:latest
```

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
│   │   │   ├── auth.py         # Login, logout, session management
│   │   │   ├── setup.py        # Setup wizard + SSL upload/validate
│   │   │   ├── mailbox_configs.py  # Mailbox CRUD + test connection
│   │   │   ├── output_configs.py   # Output CRUD
│   │   │   ├── parsing.py      # Parse jobs, reports, file upload
│   │   │   ├── dashboard.py    # Aggregated stats, activity feed
│   │   │   ├── monitoring.py   # Background monitoring control
│   │   │   ├── test_connections.py  # Output destination testing
│   │   │   ├── updates.py      # Update checker status/settings
│   │   │   └── settings.py     # Database info, migration, purge
│   │   ├── models/             # SQLAlchemy models (7)
│   │   ├── dependencies/       # FastAPI dependencies (auth, database)
│   │   ├── services/           # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── encryption_service.py
│   │   │   ├── certificate_service.py
│   │   │   ├── mailbox_service.py
│   │   │   ├── parsing_service.py
│   │   │   ├── monitoring_service.py
│   │   │   ├── update_service.py
│   │   │   └── database_migration_service.py
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── db/session.py       # Database engine & session
│   │   ├── config.py           # Settings (env vars / Pydantic)
│   │   └── main.py             # FastAPI app, CORS, static files, SPA
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                # API client (fetch-based)
│   │   ├── types/              # TypeScript interfaces
│   │   ├── stores/             # Pinia stores (app, setup, mailboxes, outputs, parsing, updates)
│   │   ├── composables/        # useApi, useToast, usePagination, useConfirmDialog
│   │   ├── router/             # Vue Router with setup guard
│   │   ├── layouts/            # AppLayout, BlankLayout
│   │   ├── components/
│   │   │   ├── ui/             # Base components (Button, Input, Modal, Badge, etc.)
│   │   │   ├── layout/         # Sidebar, Topbar
│   │   │   ├── data/           # DataTable, Pagination, FilterBar
│   │   │   ├── forms/          # FormSection, FormField, PasswordInput, FileDropZone
│   │   │   ├── mailbox/        # 4 type-specific settings forms
│   │   │   ├── output/         # 7 type-specific settings forms
│   │   │   ├── report/         # ReportJsonViewer
│   │   │   ├── settings/       # DatabaseSettings
│   │   │   └── updates/        # UpdateModal, UpdateBadge, UpdateSettings
│   │   └── views/
│   │       ├── setup/          # SetupWizard + 6 step components
│   │       ├── DashboardView.vue
│   │       ├── mailboxes/      # List + Create/Edit
│   │       ├── outputs/        # List + Create/Edit
│   │       ├── reports/        # List + Detail (JSON viewer)
│   │       ├── jobs/           # Job list with status filter
│   │       ├── upload/         # File upload with drag-and-drop
│   │       └── settings/       # System info, SSL, database, update checker
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
├── docker-compose.yml          # GUI + optional Elasticsearch/OpenSearch
├── Dockerfile.gui              # Multi-stage build (Node + Python)
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
| `PARSEDMARC_GUI_PASSWORD_HASH` | *(set during setup)* | Bcrypt password hash (generated by setup wizard) |
| `PARSEDMARC_SECRET_KEY` | *(auto-generated)* | JWT signing key |
| `PARSEDMARC_TOKEN_EXPIRE` | `1440` | JWT token expiration (minutes, default 24h) |
| `PARSEDMARC_DB_PATH` | `./data/parsedmarc.db` | SQLite database path |
| `PARSEDMARC_DATABASE_URL` | *(none)* | Full SQLAlchemy URL for PostgreSQL/MySQL (overrides DB_PATH) |
| `PARSEDMARC_HOST` | `0.0.0.0` | Server bind address |
| `PARSEDMARC_PORT` | `8000` | Server port |
| `PARSEDMARC_CORS_ORIGINS` | `localhost:3000,8000` | Allowed CORS origins |
| `PARSEDMARC_LOG_LEVEL` | `INFO` | Logging level |
| `PARSEDMARC_DATA_DIR` | `./data` | Data directory for uploads, certs, tokens |
| `PARSEDMARC_SSL_ENABLED` | `false` | Enable HTTPS |
| `PARSEDMARC_SSL_CERTFILE` | *(none)* | Path to SSL certificate file |
| `PARSEDMARC_SSL_KEYFILE` | *(none)* | Path to SSL private key file |
| `PARSEDMARC_UPDATE_CHECK_ENABLED` | `true` | Enable GitHub release update checks |
| `PARSEDMARC_UPDATE_CHECK_INTERVAL` | `24` | Update check interval (hours, 1–168) |
| `PARSEDMARC_DOCKER` | `false` | Set to true when running in Docker |

> **Note:** The setup wizard configures these on first run. Environment variables override wizard settings.

### Database Support

| Engine | Default | Connection |
|--------|---------|------------|
| **SQLite** | `./data/parsedmarc.db` | Automatic, zero-config |
| **PostgreSQL** | *(none)* | Set `PARSEDMARC_DATABASE_URL=postgresql+psycopg2://user:pass@host/db` |
| **MySQL** | *(none)* | Set `PARSEDMARC_DATABASE_URL=mysql+pymysql://user:pass@host/db` |

Database can be selected during the setup wizard (Step 5) or by setting the environment variable. The built-in migration tool in Settings allows migrating data between database engines with connection testing.

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

### SSL Certificate Options

| Method | Description |
|--------|-------------|
| **Self-Signed** | Auto-generated with configurable CN, organization, and validity |
| **Let's Encrypt (HTTP-01)** | Standard ACME challenge via certbot (requires port 80) |
| **Let's Encrypt (DNS-01)** | DNS-based challenge via Cloudflare, Route53, DigitalOcean, or Google Cloud DNS |
| **Custom Upload** | Upload PEM certificate and key files with built-in validation |

## API Endpoints

Once running, full API docs are at http://localhost:8000/docs (Swagger UI).

| Prefix | Description |
|--------|-------------|
| `GET /api/health` | Health check (version, monitoring status) |
| `GET /api/system/info` | System information (version, DB type, data dir) |
| `/api/auth/*` | Login, logout, current user |
| `/api/setup/*` | Setup wizard (status, encryption, SSL, admin, server, DB, complete) |
| `/api/configs/mailboxes/*` | Mailbox config CRUD + test connection |
| `/api/configs/outputs/*` | Output config CRUD |
| `/api/parse/*` | Parse from mailbox, upload file, list jobs/reports |
| `/api/dashboard/*` | Aggregated stats, activity feed |
| `/api/monitoring/*` | Start/stop monitoring jobs, status |
| `/api/test/*` | Output destination connection testing |
| `/api/updates/*` | Update checker status, force check, settings |
| `/api/settings/*` | Database info, test connection, migrate, purge |

## Security

- **Authentication** — JWT-based authentication using HttpOnly cookies (not localStorage). Passwords hashed with bcrypt. Rate-limited login endpoint (5 attempts/minute).
- **CSRF Protection** — Double-submit cookie pattern on all POST/PUT/DELETE requests. CSRF token set as a JS-readable cookie, validated against `X-CSRF-Token` header.
- **Credential Encryption** — All passwords, API keys, and secrets are encrypted at rest using Fernet symmetric encryption. Each installation generates a unique encryption key during setup.
- **Security Headers** — CSP, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy. HSTS enabled when SSL is active.
- **Rate Limiting** — 120 requests/minute default. Stricter limits on auth (5/min), setup, connection testing, and migration endpoints.
- **SSRF Protection** — Output connection testing blocks requests to private/internal IP ranges (10.x, 172.16-31.x, 192.168.x, localhost, link-local).
- **SSL/TLS** — Self-signed certificates (auto-generated), Let's Encrypt (HTTP-01 and DNS-01), or custom certificate upload with validation.
- **Path Traversal Protection** — File uploads use UUID-prefixed sanitized filenames. SPA catch-all validates paths against directory traversal.

## License

Apache License 2.0 (same as parsedmarc)

## Credits

Built on top of [parsedmarc](https://github.com/domainaware/parsedmarc) by Sean Whalen.
