# ParseDMARC Web GUI — Open Source DMARC Report Analyzer and Visualizer

A full-stack web application that provides a graphical interface for
[parsedmarc](https://github.com/domainaware/parsedmarc), the open-source
DMARC report parser and analyzer. Upload, parse, and visualize DMARC
aggregate, forensic, and SMTP TLS reports — all from your browser.

> **Note:** This project wraps the [parsedmarc](https://github.com/domainaware/parsedmarc)
> Python library (by Sean Whalen and contributors) with a modern web interface.
> The CLI documentation in this guide covers the upstream parsedmarc tool, while
> the Web GUI sections document the new graphical interface.

## Web GUI Features

- **Setup Wizard** — Guided 6-step first-run configuration
- **JWT Authentication** — Secure login with HttpOnly cookies and CSRF protection
- **Dashboard** — Aggregated statistics, report counts, job status, activity feed
- **Mailbox Configuration** — IMAP, Microsoft Graph, Gmail API, or Maildir sources
- **Output Destinations** — Elasticsearch, OpenSearch, Splunk, Kafka, S3, Syslog, GELF, Webhooks
- **File Upload** — Drag-and-drop `.xml`, `.gz`, `.zip`, `.eml`, `.msg` report files
- **Report Viewer** — Browse and inspect parsed reports with full JSON detail
- **Background Monitoring** — Scheduled mailbox watching with per-source controls
- **SSL/TLS** — Self-signed, Let's Encrypt, or custom certificate upload
- **Database Management** — SQLite (default), PostgreSQL, or MySQL with migration tools
- **Dark Mode** — Full dark theme with system preference detection
- **Update Checker** — Automatic GitHub release checking

## parsedmarc CLI Features

- Parses draft and 1.0 standard aggregate/rua DMARC reports
- Parses forensic/failure/ruf DMARC reports
- Parses reports from SMTP TLS Reporting
- Can parse reports from an inbox over IMAP, Microsoft Graph, or Gmail API
- Transparently handles gzip or zip compressed reports
- Consistent data structures
- Simple JSON and/or CSV output
- Optionally email the results
- Optionally send the results to Elasticsearch, OpenSearch, and/or Splunk
- Optionally send reports to Apache Kafka

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
│  JWT Auth · CSRF · Fernet Encryption     │
│  Serves built frontend as SPA           │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│   SQLite / PostgreSQL / MySQL            │
│   (encrypted credentials at rest)        │
└─────────────────────────────────────────┘
```

## Python Compatibility

| Version | Supported | Reason                                                     |
|---------|-----------|------------------------------------------------------------|
| < 3.9   | No        | End of Life (EOL)                                          |
| 3.9     | Yes       | Supported until August 2026 (Debian 11); May 2032 (RHEL 9) |
| 3.10    | Yes       | Actively maintained                                        |
| 3.11    | Yes       | Actively maintained; supported until June 2028 (Debian 12) |
| 3.12    | Yes       | Actively maintained; supported until May 2035 (RHEL 10)    |
| 3.13    | Yes       | Actively maintained; supported until June 2030 (Debian 13) |
| 3.14    | Yes       | Actively maintained                                        |

## Contents

- [Installation](installation.md) — Docker, manual setup, CLI install
- [Web GUI Guide](web-gui.md) — Setup wizard, dashboard, mailbox/output config, parsing, monitoring
- [CLI Usage](usage.md) — parsedmarc command-line interface
- [Sample Outputs](output.md) — JSON and CSV report examples
- [Elasticsearch & Kibana](elasticsearch.md) — Setup and dashboards
- [OpenSearch & Grafana](opensearch.md) — Setup and dashboards
- [Kibana Dashboards](kibana.md) — Using the Kibana dashboards
- [Splunk](splunk.md) — Splunk HEC setup
- [DavMail](davmail.md) — Accessing Exchange via OWA/EWS
- [Understanding DMARC](dmarc.md) — DMARC alignment, SPF, DKIM
- [Contributing](contributing.md) — Development setup and guidelines
- [API Reference](api.md) — REST API endpoints and Python library

```{toctree}
:hidden:
:maxdepth: 2

installation
web-gui
usage
output
elasticsearch
opensearch
kibana
splunk
davmail
dmarc
contributing
api
```
