# ParseDMARC Web GUI

A modern web-based interface for [parsedmarc](https://github.com/domainaware/parsedmarc) - transforming the CLI DMARC report parser into a user-friendly web application.

## Features

- 🌐 **Web-Based Configuration** - Visual interface for all settings (no manual INI editing)
- 📊 **Real-Time Dashboard** - Live monitoring of DMARC reports with statistics
- 📧 **Multiple Mailbox Support** - IMAP, Microsoft Graph (Office 365), Gmail API, Maildir
- 🔄 **Automated Monitoring** - Continuous mailbox watching with background jobs
- 📤 **Multiple Output Destinations** - Elasticsearch, OpenSearch, Splunk, Kafka, S3, Syslog, GELF, Webhooks
- 🔒 **Secure Credential Storage** - Encrypted credentials using Fernet encryption
- 📁 **File Upload Parsing** - Drag-and-drop individual DMARC report files
- 🧪 **Connection Testing** - Test mailbox and output connections before saving
- 🐳 **Docker Ready** - Simple deployment with docker-compose

## Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async support
- **Database**: SQLite with SQLAlchemy ORM
- **Background Jobs**: APScheduler for mailbox monitoring
- **Real-Time Updates**: Server-Sent Events (SSE)
- **Security**: Fernet encryption for credentials, HTTP Basic Auth

### Frontend (Vue.js 3) - *In Progress*
- **Framework**: Vue.js 3 with Composition API
- **UI Library**: Tailwind CSS
- **State Management**: Pinia
- **Real-Time**: SSE client for live updates

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend development)
- Docker & Docker Compose (for containerized deployment)

### Setup

1. **Clone the repository**
   ```bash
   cd parsedmarc-gui
   ```

2. **Generate encryption key**
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and set PARSEDMARC_ENCRYPTION_KEY with generated key
   ```

4. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

5. **Run the backend server**
   ```bash
   cd backend
   python -m app.main
   ```

6. **Access the application**
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs (Swagger UI)
   - Health Check: http://localhost:8000/api/health

## Project Structure

```
parsedmarc-gui/
├── backend/
│   ├── app/
│   │   ├── api/              # REST API endpoints
│   │   ├── models/           # SQLAlchemy database models
│   │   ├── services/         # Business logic
│   │   ├── db/               # Database configuration
│   │   ├── config.py         # Application settings
│   │   └── main.py           # FastAPI app entry point
│   └── requirements.txt
├── frontend/               # Vue.js application (in progress)
├── docker/                 # Docker configurations
├── .env.example           # Environment variables template
└── README.md
```

## Configuration

### Environment Variables

See `.env.example` for all configuration options:

- **PARSEDMARC_ENCRYPTION_KEY**: Encryption key for credentials (required)
- **PARSEDMARC_GUI_USERNAME**: Admin username (default: admin)
- **PARSEDMARC_GUI_PASSWORD**: Admin password (default: changeme)
- **PARSEDMARC_DB_PATH**: Database file path
- **PARSEDMARC_HOST**: Server host (default: 0.0.0.0)
- **PARSEDMARC_PORT**: Server port (default: 8000)

### Mailbox Types Supported

1. **IMAP** - Standard IMAP servers
   - Configuration: host, port, username, password, SSL/TLS options

2. **Microsoft Graph** ⭐ - Office 365 / Microsoft 365
   - Authentication methods: DeviceCode, ClientSecret, UsernamePassword
   - Azure AD app registration required
   - Supports shared mailboxes

3. **Gmail API** - Google Gmail
   - OAuth2 authentication
   - Credentials file from Google Cloud Console required

4. **Maildir** - Local Maildir folders
   - File system-based mailbox access

### Output Destinations Supported

- Elasticsearch
- OpenSearch
- Splunk HEC
- Apache Kafka
- AWS S3
- Syslog
- GELF (Graylog)
- Webhooks

## Development Status

### ✅ Completed
- Backend application structure
- Database models and encryption
- Configuration management system
- FastAPI app with health endpoints

### 🚧 In Progress
- Mailbox configuration API endpoints
- Output configuration API endpoints
- Parsing service
- Monitoring service with APScheduler
- Frontend Vue.js application

### 📋 Planned
- Dashboard with real-time statistics
- File upload interface
- Connection testing endpoints
- Docker deployment
- User documentation

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Security

- **Credentials**: All passwords, API keys, and secrets are encrypted using Fernet (symmetric encryption)
- **Authentication**: HTTP Basic Auth (JWT tokens planned)
- **HTTPS**: Use nginx reverse proxy with SSL/TLS in production
- **Database**: SQLite with encrypted sensitive fields

## License

Apache License 2.0 (same as parsedmarc)

## Credits

Built on top of [parsedmarc](https://github.com/domainaware/parsedmarc) by Sean Whalen.
