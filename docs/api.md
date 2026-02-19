# API Reference

## Web GUI REST API

The Web GUI backend exposes a REST API. When the server is running, interactive
API documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Endpoint Summary

#### Health & System (Public)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check (status, version, monitoring state) |
| GET | `/api/system/info` | System info (version, database type) |

#### Authentication (Public)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | Login with username/password (rate limited: 5/min) |
| POST | `/api/auth/logout` | Logout and clear cookies |
| GET | `/api/auth/me` | Get current authenticated user |

#### Setup Wizard (Public during initial setup)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/setup/status` | Check if setup is complete |
| GET | `/api/setup/encryption-key/generate` | Generate a new Fernet key |
| POST | `/api/setup/encryption-key` | Save encryption key |
| POST | `/api/setup/admin-credentials` | Save admin username and password |
| POST | `/api/setup/ssl` | Configure SSL/TLS |
| POST | `/api/setup/server` | Configure server settings |
| POST | `/api/setup/database` | Configure database |
| POST | `/api/setup/complete` | Complete all setup steps at once |
| GET | `/api/setup/certificate` | Get current SSL certificate info |
| POST | `/api/setup/certificate/renew` | Renew Let's Encrypt certificate |
| POST | `/api/setup/ssl/upload` | Upload custom certificate files |
| POST | `/api/setup/ssl/validate` | Validate certificate pair |
| POST | `/api/setup/restart` | Restart server to apply configuration |

#### Mailbox Configurations (Authenticated)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/configs/mailboxes/` | List all mailbox configurations |
| GET | `/api/configs/mailboxes/{id}` | Get a single mailbox configuration |
| POST | `/api/configs/mailboxes/` | Create a new mailbox configuration |
| PUT | `/api/configs/mailboxes/{id}` | Update a mailbox configuration |
| DELETE | `/api/configs/mailboxes/{id}` | Delete a mailbox configuration |
| POST | `/api/configs/mailboxes/{id}/test` | Test mailbox connection |

#### Output Configurations (Authenticated)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/configs/outputs/` | List all output configurations |
| GET | `/api/configs/outputs/{id}` | Get a single output configuration |
| POST | `/api/configs/outputs/` | Create a new output configuration |
| PUT | `/api/configs/outputs/{id}` | Update an output configuration |
| DELETE | `/api/configs/outputs/{id}` | Delete an output configuration |

#### Connection Testing (Authenticated)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/test/output/{id}` | Test output destination connectivity |

#### Parsing (Authenticated)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/parse/mailbox/{config_id}` | Parse reports from a mailbox |
| POST | `/api/parse/upload` | Upload and parse a report file |
| GET | `/api/parse/jobs` | List parse jobs (paginated, filterable) |
| GET | `/api/parse/jobs/{id}` | Get a specific parse job |
| GET | `/api/parse/reports` | List parsed reports (paginated, filterable) |
| GET | `/api/parse/reports/{id}` | Get a specific parsed report |

#### Dashboard (Authenticated)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/dashboard` | Full dashboard (stats + recent activity) |
| GET | `/api/dashboard/stats` | Aggregated statistics only |
| GET | `/api/dashboard/activity` | Recent activity log entries |

#### Monitoring (Authenticated)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/monitoring/status` | Get monitoring service status |
| GET | `/api/monitoring/jobs` | List all monitoring jobs |
| GET | `/api/monitoring/jobs/{mailbox_config_id}` | Get monitoring job for a mailbox |
| POST | `/api/monitoring/jobs/{mailbox_config_id}/start` | Start monitoring a mailbox |
| POST | `/api/monitoring/jobs/{mailbox_config_id}/stop` | Stop monitoring a mailbox |

#### Updates (Authenticated)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/updates/status` | Get cached update status |
| POST | `/api/updates/check` | Force immediate update check |
| GET | `/api/updates/settings` | Get update checker settings |

#### Settings (Authenticated)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/settings/database` | Get current database info and table counts |
| POST | `/api/settings/database/test` | Test target database connection |
| POST | `/api/settings/database/migrate` | Migrate data to a new database |
| POST | `/api/settings/database/purge` | Purge all data (SQLite only) |

### Authentication

All authenticated endpoints require a valid JWT token in the `access_token`
HttpOnly cookie. For state-changing requests (POST, PUT, DELETE), an
`X-CSRF-Token` header must also be included, matching the value in the
`csrf_token` cookie.

Example using `curl`:

```bash
# Login (stores cookies in jar)
curl -c cookies.txt -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# Authenticated GET request
curl -b cookies.txt http://localhost:8000/api/dashboard

# Authenticated POST request (with CSRF token)
CSRF=$(grep csrf_token cookies.txt | awk '{print $NF}')
curl -b cookies.txt -X POST http://localhost:8000/api/auth/logout \
  -H "X-CSRF-Token: $CSRF"
```

---

## parsedmarc Python Library

The following modules are part of the upstream
[parsedmarc](https://github.com/domainaware/parsedmarc) Python library.
Full auto-generated API documentation is available when building these
docs with Sphinx.

### Modules

| Module | Description |
|--------|-------------|
| `parsedmarc` | Main module — report parsing functions |
| `parsedmarc.elastic` | Elasticsearch output integration |
| `parsedmarc.opensearch` | OpenSearch output integration |
| `parsedmarc.splunk` | Splunk HEC output integration |
| `parsedmarc.types` | Type definitions for parsed reports |
| `parsedmarc.utils` | Utility functions (DNS, GeoIP, base domain, etc.) |

For detailed API documentation of each module, install parsedmarc and use:

```bash
python -c "import parsedmarc; help(parsedmarc)"
```
