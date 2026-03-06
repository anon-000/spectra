<p align="center">
  <h1 align="center">🔮 Spectra</h1>
  <p align="center">
    <strong>Unified Security Scanning as a Service for GitHub Repositories</strong>
  </p>
  <p align="center">
    Plug into your GitHub repos, get automated security scanning on every PR with AI-powered noise reduction and a dashboard to manage findings.
  </p>
</p>

---

## 🏗️ Overview

**Spectra** is a SaaS-style security scanning platform that integrates directly with GitHub via a GitHub App. It automatically triggers four core security scans on every pull request, normalizes and deduplicates findings across tools, uses AI (Claude) to triage results, and surfaces everything through inline PR comments, GitHub Checks, Slack alerts, and a web dashboard.

### Key Features

- **🔌 GitHub App Integration** — Install on your org/repos, auto-scan every PR and push to the default branch
- **🛡️ Four Core Scans** — SAST (Semgrep), Secrets (Trufflehog), SCA (osv-scanner), License/SBOM (CycloneDX via cdxgen)
- **🤖 AI Triage** — Every finding is triaged by Claude to classify as true positive, false positive, or needs review — cutting noise by 50%+
- **💬 Inline PR Feedback** — Findings posted as GitHub Check annotations and inline PR review comments with severity badges and fix suggestions
- **📊 Web Dashboard** — Manage repos, view scans, filter/triage findings, configure policies
- **📋 Policy Engine** — Define severity thresholds and license blocklists; automatically block or warn on PRs
- **🔔 Slack Notifications** — Alerts on critical/high findings and policy failures
- **🧬 Cross-Scan Deduplication** — SHA-256 fingerprint-based dedup prevents duplicate findings across scans

---

## 📐 Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                          EXTERNAL                                 │
│                                                                   │
│   GitHub ──webhook──▶  API (FastAPI)  ◀──────── Dashboard (Next)  │
│          ◀──PR comments──┘     │                                  │
│                                │                                  │
│   Slack  ◀──alerts─────────────┘                                  │
└────────────────────────────────┼──────────────────────────────────┘
                                 │
┌────────────────────────────────┼──────────────────────────────────┐
│                          BACKEND                                  │
│                                ▼                                  │
│                     ┌────────────────────┐                        │
│                     │   Core API         │  FastAPI + Python 3.12 │
│                     │   - Auth (GitHub)  │                        │
│                     │   - Webhook Rx     │                        │
│                     │   - Findings CRUD  │                        │
│                     │   - Policy Eval    │                        │
│                     └────────┬───────────┘                        │
│                              │                                    │
│                              ▼                                    │
│                     ┌────────────────────┐                        │
│                     │   Redis + ARQ      │  Task queue             │
│                     └────────┬───────────┘                        │
│                              │                                    │
│                    ┌─────────┴──────────┐                         │
│                    ▼                    ▼                          │
│             ┌────────────┐      ┌────────────┐                    │
│             │ Worker #1  │      │ Worker #N  │  Docker containers  │
│             │ - semgrep  │      │            │  with all tools     │
│             │ - truffleh.│      │            │  pre-installed      │
│             │ - osv-scan │      │            │                    │
│             │ - cdxgen   │      │            │                    │
│             └─────┬──────┘      └─────┬──────┘                    │
│                   │                   │                            │
│                   └────────┬──────────┘                            │
│                            ▼                                      │
│              ┌──────────────────────────┐                         │
│              │  Normalizer + AI Triage  │                         │
│              │  - Unified schema        │                         │
│              │  - Dedup (SHA-256)       │                         │
│              │  - Claude triage         │                         │
│              └────────────┬─────────────┘                         │
│                           ▼                                       │
│              ┌──────────────────────────┐                         │
│              │  PostgreSQL + MinIO      │                         │
│              │  (data)     (artifacts)  │                         │
│              └──────────────────────────┘                         │
└───────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component          | Technology                             | Purpose                                                      |
| ------------------ | -------------------------------------- | ------------------------------------------------------------ |
| **Backend API**    | FastAPI (Python 3.12)                  | Async REST API, webhook receiver, auth                       |
| **Task Queue**     | Redis + ARQ                            | Lightweight async job queue for scan workers                 |
| **Database**       | PostgreSQL 16                          | Primary data store (repos, scans, findings, policies, users) |
| **Object Storage** | MinIO (S3-compatible)                  | Raw scan artifacts and SBOM storage                          |
| **Frontend**       | Next.js 16 + React 19 + Tailwind CSS 4 | Dashboard SPA                                                |
| **AI Triage**      | Anthropic Claude (Sonnet)              | Finding classification and fix suggestions                   |
| **Auth**           | GitHub OAuth + JWT (PyJWT)             | User authentication                                          |
| **ORM**            | SQLAlchemy 2 (async) + Alembic         | Database models and migrations                               |
| **Logging**        | structlog                              | Structured JSON logging                                      |
| **UI Components**  | Radix UI + Lucide Icons                | Accessible, unstyled component primitives                    |
| **DB Admin**       | Adminer                                | Dev-time database browser                                    |

### Security Tools (in Worker)

| Tool                                                        | Scan Type      | Purpose                                                 |
| ----------------------------------------------------------- | -------------- | ------------------------------------------------------- |
| [Semgrep](https://semgrep.dev)                              | SAST           | Static Analysis — finds code-level vulnerabilities      |
| [Trufflehog](https://github.com/trufflesecurity/trufflehog) | Secrets        | Detects leaked secrets, API keys, credentials           |
| [osv-scanner](https://github.com/google/osv-scanner)        | SCA            | Finds known vulnerabilities in open-source dependencies |
| [cdxgen (CycloneDX)](https://github.com/CycloneDX/cdxgen)   | License / SBOM | Generates SBOMs and checks license compliance           |

---

## 📂 Project Structure

```
spectra/
├── src/                          # Python backend source
│   ├── main.py                   # FastAPI app factory + health endpoint
│   ├── config.py                 # Pydantic settings (env-driven config)
│   ├── worker.py                 # ARQ worker settings + entrypoint
│   ├── dependencies.py           # FastAPI dependencies (DB session, auth)
│   ├── api/                      # REST API route handlers
│   │   ├── router.py             #   Route aggregation (/api/v1 prefix)
│   │   ├── auth.py               #   GitHub OAuth callback + /me
│   │   ├── repos.py              #   Repo CRUD + GitHub sync
│   │   ├── scans.py              #   Scan listing + manual trigger
│   │   ├── findings.py           #   Findings CRUD + bulk update + events
│   │   ├── policies.py           #   Policy CRUD
│   │   └── webhooks.py           #   GitHub webhook receiver
│   ├── core/                     # Cross-cutting concerns
│   │   ├── security.py           #   JWT encode/decode, webhook verification
│   │   ├── exceptions.py         #   Custom exception classes
│   │   ├── error_handlers.py     #   FastAPI error handlers
│   │   ├── middleware.py         #   Request ID middleware
│   │   └── logging.py           #   structlog setup
│   ├── db/                       # Database layer
│   │   ├── engine.py             #   SQLAlchemy async engine + session
│   │   ├── base.py               #   Base model with UUID PK + timestamp mixins
│   │   └── models/               #   ORM models
│   │       ├── user.py           #     users table
│   │       ├── organization.py   #     organizations table
│   │       ├── repo.py           #     repos table
│   │       ├── scan.py           #     scans table
│   │       ├── finding.py        #     findings table (unified schema)
│   │       ├── finding_event.py  #     finding audit trail
│   │       └── policy.py         #     policies table
│   ├── schemas/                  # Pydantic request/response schemas
│   │   ├── finding.py            #     Finding DTOs
│   │   ├── scan.py               #     Scan DTOs
│   │   ├── repo.py               #     Repo DTOs
│   │   ├── policy.py             #     Policy DTOs + eval result
│   │   ├── user.py               #     User + Token DTOs
│   │   └── webhook.py            #     Webhook payload schemas
│   ├── services/                 # Business logic layer
│   │   ├── auth.py               #   GitHub OAuth + user resolution
│   │   ├── github.py             #   GitHub API (clone, checks, PR comments)
│   │   ├── scan_orchestrator.py  #   Webhook → scan job orchestration
│   │   ├── policy_engine.py      #   Policy evaluation logic
│   │   └── notification.py       #   GitHub + Slack notification composer
│   ├── tasks/                    # Worker tasks
│   │   ├── scan_task.py          #   Main scan job (clone → tools → normalize → persist)
│   │   ├── ai_triage.py          #   Claude API integration for AI triage
│   │   ├── normalizer.py         #   Finding dedup + fingerprinting
│   │   └── tools/                #   Scanner tool adapters
│   │       ├── base.py           #     RawFinding dataclass + BaseTool ABC
│   │       ├── semgrep.py        #     Semgrep adapter
│   │       ├── trufflehog.py     #     Trufflehog adapter
│   │       ├── osv_scanner.py    #     osv-scanner adapter
│   │       └── cyclonedx.py      #     CycloneDX/cdxgen adapter
│   └── storage/
│       └── s3.py                 #   MinIO client for artifact upload/download
│
├── frontend/                     # Next.js dashboard
│   └── src/
│       ├── app/
│       │   ├── layout.tsx        #   Root layout
│       │   ├── globals.css       #   Global styles (Tailwind)
│       │   ├── login/            #   Login page
│       │   ├── auth/             #   OAuth callback handler
│       │   └── (app)/            #   Authenticated app routes
│       │       ├── page.tsx      #     Dashboard home (overview)
│       │       ├── layout.tsx    #     App layout with sidebar
│       │       ├── repos/        #     Repos list + detail pages
│       │       ├── scans/        #     Scans list + detail pages
│       │       ├── findings/     #     Findings list + detail pages
│       │       └── policies/     #     Policy management page
│       ├── components/           #   Reusable UI components
│       │   ├── Sidebar.tsx       #     Navigation sidebar
│       │   ├── ManualScanModal.tsx#    Manual scan trigger modal
│       │   └── ui/              #     Base UI primitives
│       ├── lib/
│       │   ├── api.ts            #   API client (typed fetch wrappers)
│       │   ├── auth.tsx          #   Auth context provider
│       │   └── utils.ts          #   Utility helpers
│       └── types/                #   TypeScript type definitions
│
├── alembic/                      # Database migrations
│   ├── env.py                    #   Migration environment config
│   └── versions/                 #   Migration scripts
│       ├── 001_initial_schema.py
│       ├── 002_finding_schema_additions.py
│       └── 003_scan_check_run_id.py
│
├── tests/                        # Test suite
│   ├── conftest.py               #   Fixtures (async DB, test client)
│   ├── factories.py              #   Factory Boy factories for models
│   ├── test_health.py            #   Health endpoint test
│   ├── test_auth.py              #   Auth flow tests
│   ├── test_normalizer.py        #   Dedup/fingerprint tests
│   └── test_policy_engine.py     #   Policy evaluation tests
│
├── Dockerfile                    # API server container
├── Dockerfile.worker             # Worker container (includes security tools)
├── docker-compose.yml            # Full local stack (Postgres, Redis, MinIO, API, Worker)
├── pyproject.toml                # Python project config + dependencies
├── alembic.ini                   # Alembic configuration
└── .env.example                  # Environment variable template
```

---

## ⚡ Getting Started

### Prerequisites

- **Docker** & **Docker Compose** (v2+)
- **Python 3.12+** (for local development without Docker)
- **Node.js 20+** (for frontend development)
- A **GitHub App** configured (see [GitHub App Setup](#github-app-setup))
- An **Anthropic API key** (for AI triage — optional but recommended)

### 1. Clone & Configure

```bash
git clone <repo-url> spectra
cd spectra

# Copy and fill in environment variables
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required
DATABASE_URL=postgresql+asyncpg://spectra:spectra@localhost:5432/spectra
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=<generate-a-strong-secret>

# GitHub App (required for full functionality)
GITHUB_APP_ID=<your-app-id>
GITHUB_APP_PRIVATE_KEY=<your-pem-key>
GITHUB_CLIENT_ID=<your-client-id>
GITHUB_CLIENT_SECRET=<your-client-secret>
GITHUB_WEBHOOK_SECRET=<your-webhook-secret>

# AI Triage (optional)
ANTHROPIC_API_KEY=<your-key>

# Slack (optional)
SLACK_WEBHOOK_URL=<your-webhook-url>
```

### 2. Run with Docker Compose (Recommended)

```bash
# Start all services: Postgres, Redis, MinIO, API, Worker, Adminer
docker compose up --build
```

| Service           | URL                        |
| ----------------- | -------------------------- |
| **API**           | http://localhost:8000      |
| **API Docs**      | http://localhost:8000/docs |
| **MinIO Console** | http://localhost:9001      |
| **Adminer (DB)**  | http://localhost:8080      |

### 3. Run Database Migrations

```bash
# Inside the API container or locally with the venv active:
alembic upgrade head
```

### 4. Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Copy frontend env
cp .env.local.example .env.local

# Start dev server
npm run dev
```

The dashboard will be available at **http://localhost:3000**.

---

## 🔧 Local Development (Without Docker)

### Backend

```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies (with dev extras)
pip install -e ".[dev]"

# Start Postgres, Redis, MinIO via Docker
docker compose up postgres redis minio -d

# Run migrations
alembic upgrade head

# Start API server
PYTHONPATH=src uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start worker (in a separate terminal)
PYTHONPATH=src arq worker.WorkerSettings
```

### Running Tests

```bash
# Run the test suite
PYTHONPATH=src pytest tests/ -v
```

### Linting

```bash
# Format and lint with Ruff
ruff check src/ tests/
ruff format src/ tests/
```

---

## <a name="github-app-setup"></a>🔑 GitHub App Setup

To use Spectra, you need to create a GitHub App:

1. Go to **GitHub Settings → Developer Settings → GitHub Apps → New GitHub App**
2. Configure the app:
   - **Homepage URL**: Your Spectra deployment URL
   - **Callback URL**: `<your-url>/api/v1/auth/github/callback`
   - **Webhook URL**: `<your-url>/webhooks/github`
   - **Webhook secret**: Generate a strong secret and add to `.env`
3. Set **Permissions**:
   - **Repository permissions**: Contents (Read), Pull Requests (Read & Write), Checks (Read & Write), Metadata (Read)
   - **Organization permissions**: Members (Read)
4. **Subscribe to events**: `pull_request`, `push`, `installation`
5. Generate a **private key** and save it
6. Note the **App ID**, **Client ID**, and **Client Secret**

---

## 🔄 End-to-End Scan Flow

```
1. Developer opens a PR on GitHub
                    │
2. GitHub sends webhook → POST /webhooks/github
                    │
3. API creates Scan record (status: pending)
   └─ Sets GitHub Check to "in_progress"
   └─ Enqueues job to Redis via ARQ
                    │
4. Worker picks up the job
   └─ git clone the repo at the PR head SHA
   └─ Runs 4 tools in parallel:
      • Semgrep (SAST)
      • Trufflehog (Secrets)
      • osv-scanner (SCA)
      • cdxgen (SBOM/License)
                    │
5. Normalizer processes results
   └─ Converts to unified Finding schema
   └─ Computes SHA-256 fingerprints
   └─ Deduplicates against existing findings
   └─ AI triage via Claude (for new findings)
                    │
6. Policy Engine evaluates
   └─ Loads org/repo policies
   └─ Checks severity thresholds + license blocklists
   └─ Determines: pass ✅ or fail ❌
                    │
7. Notifications sent
   └─ GitHub Check Run updated (success/failure + annotations)
   └─ Inline PR review comments posted
   └─ Slack alert (if critical/high findings)
                    │
8. Dashboard reflects results in real-time
```

---

## 📡 API Endpoints

All REST endpoints are under `/api/v1` and require JWT authentication (except webhooks and health).

| Method   | Endpoint                       | Description                         |
| -------- | ------------------------------ | ----------------------------------- |
| `GET`    | `/health`                      | Health check                        |
| `GET`    | `/api/v1/auth/github/callback` | GitHub OAuth callback (returns JWT) |
| `GET`    | `/api/v1/auth/me`              | Get current user                    |
| `POST`   | `/api/v1/repos/sync`           | Sync repos from GitHub              |
| `GET`    | `/api/v1/repos`                | List repos                          |
| `GET`    | `/api/v1/repos/:id`            | Get repo details                    |
| `PATCH`  | `/api/v1/repos/:id`            | Update repo settings                |
| `GET`    | `/api/v1/scans`                | List scans (filterable)             |
| `GET`    | `/api/v1/scans/:id`            | Get scan details                    |
| `POST`   | `/api/v1/scans`                | Trigger manual scan                 |
| `GET`    | `/api/v1/findings`             | List findings (filterable)          |
| `GET`    | `/api/v1/findings/:id`         | Get finding details                 |
| `PATCH`  | `/api/v1/findings/:id`         | Update finding status               |
| `POST`   | `/api/v1/findings/bulk-update` | Bulk update finding statuses        |
| `GET`    | `/api/v1/findings/:id/events`  | Finding audit trail                 |
| `GET`    | `/api/v1/policies`             | List policies                       |
| `POST`   | `/api/v1/policies`             | Create policy                       |
| `PATCH`  | `/api/v1/policies/:id`         | Update policy                       |
| `DELETE` | `/api/v1/policies/:id`         | Delete policy                       |
| `POST`   | `/webhooks/github`             | GitHub webhook receiver             |

> **Interactive API docs** are available at `/docs` (Swagger UI) when the server is running.

---

## 🗄️ Data Model

```
users ─────────────┐
                    │
organizations ◄────┤ (users belong to orgs)
    │               │
    ├── repos ◄─────┘
    │     │
    │     ├── scans
    │     │     │
    │     │     └── findings
    │     │           │
    │     │           └── finding_events (audit trail)
    │     │
    │     └── policies
    │
    └── (org-wide policies)
```

### Unified Finding Schema

Every finding from any tool is normalized into a single schema with:

- **Source**: tool, rule_id, category (sast/sca/secret/license)
- **Location**: file_path, line_start, line_end, snippet
- **Severity**: original + AI-adjusted severity
- **AI Triage**: verdict, confidence, explanation, suggested fix
- **Dedup**: SHA-256 fingerprint, first_seen, last_seen
- **Status**: open → resolved / suppressed / false_positive

---

## 🧪 Testing

```bash
# Run all tests
PYTHONPATH=src pytest tests/ -v

# Run specific test
PYTHONPATH=src pytest tests/test_normalizer.py -v
```

Tests use an in-memory SQLite database (via `aiosqlite`) and pytest-asyncio for async test support.

---

## 🚀 Deployment

### Docker

```bash
# Build and deploy the full stack
docker compose up --build -d

# Run migrations
docker compose exec api alembic upgrade head
```

### Environment Variables

See [`.env.example`](.env.example) for all available configuration options. Key variables:

| Variable                 | Required | Description                       |
| ------------------------ | -------- | --------------------------------- |
| `DATABASE_URL`           | ✅       | PostgreSQL connection string      |
| `REDIS_URL`              | ✅       | Redis connection string           |
| `JWT_SECRET_KEY`         | ✅       | Secret for JWT signing            |
| `GITHUB_APP_ID`          | ✅       | GitHub App ID                     |
| `GITHUB_APP_PRIVATE_KEY` | ✅       | GitHub App private key (PEM)      |
| `GITHUB_CLIENT_ID`       | ✅       | GitHub OAuth client ID            |
| `GITHUB_CLIENT_SECRET`   | ✅       | GitHub OAuth client secret        |
| `GITHUB_WEBHOOK_SECRET`  | ✅       | Webhook signature verification    |
| `ANTHROPIC_API_KEY`      | ❌       | Claude API key (for AI triage)    |
| `SLACK_WEBHOOK_URL`      | ❌       | Slack webhook (for notifications) |
| `MINIO_ENDPOINT`         | ✅       | MinIO/S3 endpoint                 |
| `CORS_ORIGINS`           | ✅       | Allowed frontend origins          |

---

## 📄 License

Private — All rights reserved.
