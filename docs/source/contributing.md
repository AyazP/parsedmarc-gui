# Contributing

## ParseDMARC Web GUI

### Bug Reports

Please report Web GUI bugs on the GitHub issue tracker:

<https://github.com/AyazP/parsedmarc-gui/issues>

### Development Setup

**Prerequisites:** Python 3.9+, Node.js 20+

```bash
# Clone the repository
git clone https://github.com/AyazP/parsedmarc-gui.git
cd parsedmarc-gui

# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm ci
```

### Running in Development Mode

```bash
# Terminal 1: Backend (with auto-reload)
cd backend
PARSEDMARC_LOG_LEVEL=DEBUG python -m app.main

# Terminal 2: Frontend (with hot-reload)
cd frontend
npm run dev
```

The frontend dev server runs on `http://localhost:3000` and proxies API
requests to the backend on port 8000.

### Building for Production

```bash
cd frontend
npm run build
```

This runs TypeScript type-checking (`vue-tsc --noEmit`) followed by the
Vite production build. Output is written to `backend/static/`.

### Project Structure

| Directory | Description |
|-----------|-------------|
| `backend/app/api/` | FastAPI route handlers |
| `backend/app/services/` | Business logic (parsing, auth, encryption, etc.) |
| `backend/app/models/` | SQLAlchemy database models |
| `backend/app/dependencies/` | FastAPI dependencies (auth, database session) |
| `frontend/src/views/` | Vue page components |
| `frontend/src/components/` | Reusable Vue components |
| `frontend/src/stores/` | Pinia state management stores |
| `frontend/src/api/` | API client modules |
| `frontend/src/types/` | TypeScript type definitions |

---

## parsedmarc (Upstream Library)

For issues with the core DMARC parsing logic (not the web interface), please
report on the upstream repository:

<https://github.com/domainaware/parsedmarc/issues>
