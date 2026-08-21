# AI Performance Analysis Platform (POC)

An AI-powered performance test analysis platform that combines deterministic analysis with Google Gemini AI for root cause analysis, intelligent chatbot interactions, and automated performance insights.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                         │
│    Dashboard │ Runs │ Analysis │ Chat │ Reports          │
└─────────────────────────┬───────────────────────────────┘
                          │ REST API
┌─────────────────────────┴───────────────────────────────┐
│                    FastAPI Backend                        │
│  ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌──────────┐ │
│  │ Parsers  │ │ Analysis  │ │  AI/RAG   │ │ Reports  │ │
│  │ LR/AppD  │ │ Engine    │ │ Gemini    │ │ Service  │ │
│  └──────────┘ └───────────┘ └───────────┘ └──────────┘ │
└──────────┬──────────────────────┬───────────────────────┘
           │                      │
    ┌──────┴──────┐        ┌─────┴──────┐
    │ Filesystem  │        │  ChromaDB  │
    │   Storage   │        │  (Vector)  │
    └─────────────┘        └────────────┘
```

## Key Features

- **LoadRunner & AppDynamics Parsing** — Parse performance reports from both tools
- **Deterministic Analysis** — Rule-based SLA violation detection, bottleneck identification
- **AI Root Cause Analysis** — Google Gemini provides intelligent RCA with confidence scoring
- **RAG Chatbot** — Ask questions about performance data with context-aware AI
- **Historical Comparison** — Compare runs to detect trends and regressions
- **GitHub PR Analysis** — Correlate code changes with performance impacts
- **Report Generation** — Generate executive summaries and technical reports
- **No Relational Database** — Filesystem + ChromaDB only (POC constraint)

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Google Gemini API key

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt

# Copy environment configuration
cp ../.env.example ../.env
# Edit .env and add your GEMINI_API_KEY

uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 3. Docker (recommended)

```bash
cp .env.example .env
# Edit .env with your GEMINI_API_KEY
docker compose up --build
```

Access at http://localhost:3000

## Default Credentials

- **Username:** admin
- **Password:** admin

(POC-only authentication, not production security)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | System health check |
| POST | `/api/auth/login` | Authentication |
| GET | `/api/runs` | List all runs |
| POST | `/api/runs` | Create new run |
| POST | `/api/runs/{id}/upload/{source}` | Upload performance report |
| POST | `/api/runs/{id}/analyze` | Run deterministic analysis |
| POST | `/api/runs/{id}/rca` | AI Root Cause Analysis |
| GET | `/api/runs/{id}/analysis` | Get analysis results |
| GET | `/api/runs/{id}/rca` | Get RCA results |
| POST | `/api/chat` | AI Chatbot |
| POST | `/api/runs/{id}/report` | Generate report |
| POST | `/api/compare` | Compare multiple runs |
| POST | `/api/github/analyze-pr` | Analyze GitHub PR impact |
| POST | `/api/documents` | Upload architecture docs to RAG |

## Sample Workflow

1. Create a run: `POST /api/runs` with `{"run_id": "RUN-001", "name": "Sprint 42 Load Test"}`
2. Upload LoadRunner report: `POST /api/runs/RUN-001/upload/loadrunner` (multipart form)
3. Upload AppDynamics data: `POST /api/runs/RUN-001/upload/appdynamics` (multipart form)
4. Run analysis: `POST /api/runs/RUN-001/analyze`
5. Run AI RCA: `POST /api/runs/RUN-001/rca`
6. Chat: `POST /api/chat` with `{"question": "Why did RUN-001 fail?", "run_id": "RUN-001"}`
7. Generate report: `POST /api/runs/RUN-001/report`

## Sample Data

The `sample-data/` directory includes:
- `loadrunner/run-healthy.json` — A healthy performance run
- `loadrunner/run-degraded.json` — A degraded run with SLA violations
- `appdynamics/run-degraded.json` — Infrastructure metrics showing bottlenecks
- `architecture/dependency-graph.json` — Service dependency graph
- `github/sample-pr.json` — Example PR data for correlation analysis

## Testing

```bash
cd backend
pip install pytest pytest-asyncio
pytest
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| GEMINI_API_KEY | Yes | — | Google Gemini API key |
| GEMINI_MODEL | No | gemini-2.0-flash | Model to use |
| DATA_DIR | No | ./data | Filesystem storage location |
| JWT_SECRET | No | dev-secret-change-me | JWT signing key |
| GITHUB_TOKEN | No | — | GitHub API token for PR analysis |

## Production Notes

This is a POC. For production migration, see [docs/production-migration.md](docs/production-migration.md).
