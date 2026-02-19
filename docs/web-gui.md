# Web GUI Guide

The ParseDMARC Web GUI provides a browser-based interface for configuring
mailbox sources, parsing DMARC reports, viewing results on a dashboard, and
forwarding parsed data to various output destinations.

## Getting Started

After installation (see {doc}`installation`), open the application in your
browser. On first run, you will be guided through the **Setup Wizard**.

## Setup Wizard

The setup wizard walks you through six steps to configure the application.

### Step 1: Encryption Key

A Fernet symmetric encryption key is used to encrypt sensitive data such as
mailbox passwords and API keys at rest in the database. You can:

- **Auto-generate** a new key (recommended)
- **Enter** an existing key if restoring from a backup

:::{warning}
Store this key securely. If lost, encrypted credentials in the database
cannot be recovered.
:::

### Step 2: Admin Credentials

Set the admin username and password for logging into the web interface.

- Username must be at least 3 characters
- Password must be at least 8 characters
- Passwords are hashed with **bcrypt** before storage — plaintext passwords
  are never saved

### Step 3: SSL / TLS

Choose how to secure the application with HTTPS:

| Option | Description |
|--------|-------------|
| **Self-Signed** | Auto-generates a certificate (good for internal/testing use) |
| **Let's Encrypt (HTTP-01)** | Standard ACME challenge (requires port 80 and a public domain) |
| **Let's Encrypt (DNS-01)** | DNS-based challenge via Cloudflare, Route53, DigitalOcean, or Google Cloud DNS |
| **Custom Upload** | Upload your own PEM certificate and key files |
| **None** | Run without SSL (HTTP only) |

After setup, if SSL is enabled the server will restart and redirect to HTTPS.

:::{note}
When using self-signed certificates, your browser will show a security
warning on first visit. You must accept the certificate before the
application will load.
:::

### Step 4: Server Configuration

Configure the server bind address, port, CORS origins, and log level.

| Setting | Default | Description |
|---------|---------|-------------|
| Host | `0.0.0.0` | Server bind address |
| Port | `8000` | Server port |
| CORS Origins | `http://localhost:3000,http://localhost:8000` | Allowed CORS origins (comma-separated) |
| Log Level | `INFO` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` |

### Step 5: Database

Choose the database engine for storing configurations and parsed reports.

| Engine | Best For |
|--------|----------|
| **SQLite** (default) | Single-server deployments, getting started quickly |
| **PostgreSQL** | Production deployments, multi-user, larger datasets |
| **MySQL** | Production deployments where MySQL is preferred |

For PostgreSQL or MySQL, enter the connection details and test the connection
before proceeding.

### Step 6: Review

Review all settings and complete the setup. The application will:

1. Write configuration to the `.env` file
2. Initialize the database tables
3. Automatically log you in
4. Restart the server (if SSL was configured)

## Authentication

### Logging In

Navigate to the application URL. If not authenticated, you will be redirected
to the login page. Enter the admin username and password configured during
setup.

Authentication uses **JWT tokens** stored in **HttpOnly cookies**:

- The access token cookie is not accessible to JavaScript (prevents XSS theft)
- A separate CSRF token cookie is set for state-changing requests
- Tokens expire after 24 hours by default (configurable via `PARSEDMARC_TOKEN_EXPIRE`)

### Logging Out

Click the **Logout** button in the top navigation bar. This clears both the
access token and CSRF cookies.

### Session Expiry

When your session expires, API requests will return 401 and the frontend will
redirect you to the login page. Your intended destination is preserved so you
return to the same page after logging in again.

## Dashboard

The dashboard provides an at-a-glance overview of your DMARC data:

- **Report Statistics** — Total count of aggregate, forensic, and SMTP TLS reports
- **Job Statistics** — Total, completed, and failed parse jobs
- **Configuration Counts** — Number of mailbox and output configurations
- **Recent Activity** — Activity feed showing recent parse jobs, configuration changes, and monitoring events

## Mailbox Configuration

Navigate to **Mailboxes** in the sidebar to manage mailbox sources.

### Supported Mailbox Types

#### IMAP

Standard IMAP mailbox connection.

| Setting | Description |
|---------|-------------|
| Host | IMAP server hostname |
| Port | IMAP port (default: 993 for SSL, 143 for plain) |
| Username | IMAP username |
| Password | IMAP password (encrypted at rest) |
| SSL | Enable SSL/TLS connection |
| Folder | Mailbox folder to read from (default: `INBOX`) |
| Batch Size | Number of emails to process per batch |

#### Microsoft Graph

Connect to Microsoft 365 / Exchange Online mailboxes.

| Setting | Description |
|---------|-------------|
| Auth Method | `DeviceCode`, `ClientSecret`, or `UsernamePassword` |
| Tenant ID | Azure AD tenant ID |
| Client ID | Azure AD application (client) ID |
| Client Secret | Application secret (for ClientSecret auth) |
| Username / Password | User credentials (for UsernamePassword auth) |

Requires an Azure AD app registration with `Mail.Read` permissions.

#### Gmail API

Connect to Gmail using OAuth2.

| Setting | Description |
|---------|-------------|
| Credentials File | Google Cloud Console OAuth2 credentials JSON |
| Token File | Cached OAuth2 token (auto-generated) |
| Scopes | Gmail API scopes |
| Include Spam/Trash | Also search spam and trash folders |

#### Maildir

Read reports from a local Maildir directory.

| Setting | Description |
|---------|-------------|
| Path | Filesystem path to the Maildir directory |

### Testing Connections

Click **Test Connection** on any mailbox configuration to verify connectivity
before saving. The test attempts to connect and list available folders.

### Common Settings

All mailbox types share these options:

| Setting | Description |
|---------|-------------|
| Enabled | Enable/disable this mailbox |
| Delete After Processing | Remove emails after successful parsing |
| Watch Interval | Minutes between monitoring checks (for background monitoring) |

## Output Configuration

Navigate to **Outputs** in the sidebar to manage output destinations where
parsed reports are forwarded.

### Supported Output Types

| Type | Protocol | Key Settings |
|------|----------|-------------|
| **Elasticsearch** | REST | Hosts, auth (user/pass or API key), SSL, monthly indexes |
| **OpenSearch** | REST | Hosts, auth, SSL, index suffix |
| **Splunk** | HEC | URL, token, index |
| **Kafka** | TCP | Bootstrap servers, per-type topics, SASL auth |
| **S3** | AWS SDK | Bucket, region, IAM or access keys, key prefix |
| **Syslog** | UDP/TCP | Server, port |
| **GELF** | UDP/TCP | Server, port (Graylog) |
| **Webhook** | HTTP | URL, custom headers, timeout |

Each output can be configured to receive specific report types:
aggregate, forensic, and/or SMTP TLS.

### Testing Outputs

Click **Test Connection** on any output configuration to verify connectivity.
Connection testing includes **SSRF protection** — requests to private/internal
IP ranges (10.x, 172.16-31.x, 192.168.x, localhost) are blocked.

## Parsing Reports

### From a Mailbox

1. Navigate to **Mailboxes**
2. Click the **Parse** button on any configured mailbox
3. Optionally set batch size, date range, or test mode
4. The parse job runs in the background — check status on the **Jobs** page

### From a File Upload

1. Navigate to **Upload**
2. Drag and drop (or click to browse) report files
3. Supported formats: `.xml`, `.gz`, `.zip`, `.eml`, `.msg`
4. Maximum file size: 50 MB
5. Results appear immediately after parsing

### Parse Jobs

Navigate to **Jobs** to view all parse jobs with their status:

| Status | Description |
|--------|-------------|
| `pending` | Job queued, not yet started |
| `running` | Job currently processing |
| `completed` | Job finished successfully |
| `failed` | Job encountered an error |

Click on a job to see details including report counts and error messages.

## Report Viewer

Navigate to **Reports** to browse all parsed reports.

- **Filter** by report type (aggregate, forensic, SMTP TLS), domain, or organization
- **Paginated** list with configurable page size
- Click any report to view the **full JSON detail** with syntax highlighting

## Background Monitoring

Navigate to **Settings** or use the monitoring controls on individual mailbox
configurations to enable continuous background monitoring.

- **Start/Stop** monitoring per mailbox
- Runs on the configured watch interval using APScheduler
- Automatically parses new reports as they arrive
- View monitoring status (running/stopped, active jobs) on the dashboard

## Settings

Navigate to **Settings** in the sidebar for system-wide configuration.

### Database Management

View current database information:

- Database engine (SQLite, PostgreSQL, MySQL)
- Connection string
- Total records and per-table row counts

**Migrate Database** — Move data from one database engine to another:

1. Click **Migrate Database**
2. Select target database type and enter connection details
3. Click **Test Connection** to verify
4. Click **Migrate & Switch** to copy all data and switch to the new database
5. Restart the application to use the new database

**Purge Database** (SQLite only) — Delete all data and reset to initial state.
After purging, you will be redirected to the setup wizard.

### SSL Certificate Management

- View current certificate details (type, domain, expiry)
- **Renew** Let's Encrypt certificates
- **Upload** new custom certificates
- **Restart** the server to apply SSL changes

### Update Checker

- View the current version and latest available release
- Enable/disable automatic update checking
- Configure check interval (1–168 hours)
- Force an immediate update check

## Configuration Reference

All configuration is managed through environment variables, which can be set in
a `.env` file in the backend directory. The setup wizard configures these
automatically on first run.

| Variable | Default | Description |
|----------|---------|-------------|
| `PARSEDMARC_ENCRYPTION_KEY` | *(required)* | Fernet encryption key for stored secrets |
| `PARSEDMARC_GUI_USERNAME` | `admin` | Admin login username |
| `PARSEDMARC_GUI_PASSWORD_HASH` | *(set during setup)* | Bcrypt password hash |
| `PARSEDMARC_SECRET_KEY` | *(auto-generated)* | JWT signing secret |
| `PARSEDMARC_TOKEN_EXPIRE` | `1440` | JWT expiration in minutes (default 24h) |
| `PARSEDMARC_DB_PATH` | `./data/parsedmarc.db` | SQLite database file path |
| `PARSEDMARC_DATABASE_URL` | *(none)* | Full database URL (overrides DB_PATH) |
| `PARSEDMARC_HOST` | `0.0.0.0` | Server bind address |
| `PARSEDMARC_PORT` | `8000` | Server port |
| `PARSEDMARC_CORS_ORIGINS` | `http://localhost:3000,http://localhost:8000` | CORS allowed origins |
| `PARSEDMARC_LOG_LEVEL` | `INFO` | Log level: DEBUG, INFO, WARNING, ERROR |
| `PARSEDMARC_DATA_DIR` | `./data` | Data directory for uploads, certs, tokens |
| `PARSEDMARC_SSL_ENABLED` | `false` | Enable HTTPS |
| `PARSEDMARC_SSL_CERTFILE` | *(none)* | SSL certificate file path |
| `PARSEDMARC_SSL_KEYFILE` | *(none)* | SSL private key file path |
| `PARSEDMARC_UPDATE_CHECK_ENABLED` | `true` | Enable automatic update checking |
| `PARSEDMARC_UPDATE_CHECK_INTERVAL` | `24` | Hours between update checks (1–168) |
| `PARSEDMARC_DOCKER` | `false` | Set to `true` when running in Docker |

## Security

### Authentication

All API endpoints (except `/api/health`, `/api/system/info`, `/api/auth/login`,
and initial `/api/setup/*`) require authentication. The authentication system
uses:

- **JWT tokens** stored in HttpOnly cookies (not accessible to JavaScript)
- **CSRF double-submit cookies** — a JS-readable CSRF token cookie is sent
  alongside an `X-CSRF-Token` header on all state-changing requests
- **bcrypt** password hashing — plaintext passwords are never stored
- **Rate limiting** — login endpoint limited to 5 attempts per minute

### Encryption

Sensitive configuration values (mailbox passwords, API keys, OAuth tokens) are
encrypted at rest using **Fernet symmetric encryption**. The encryption key is
generated during setup and stored in the `.env` file.

### Security Headers

The application sets the following security headers on all responses:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Content-Security-Policy: default-src 'self'; ...`
- `Strict-Transport-Security` (when SSL is enabled)

### Rate Limiting

| Endpoint Group | Limit |
|---------------|-------|
| General API | 120/minute |
| Login | 5/minute |
| Setup completion | 3/minute |
| Connection testing | 10/minute |
| Database migration | 2/minute |

### SSRF Protection

Connection testing endpoints (for output destinations and database migration)
include SSRF protection that blocks requests to:

- Private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Localhost (127.0.0.0/8)
- Link-local addresses (169.254.0.0/16)
