# Production Migration Guide

This document outlines the path from POC to production for the AI Performance Analysis Platform.

## Storage Layer

### Current (POC)
- Filesystem JSON storage
- ChromaDB (embedded, persisted locally)

### Production Options
- **Filesystem → Azure Blob / S3** — Swap `FilesystemStorage` with cloud object storage adapter
- **ChromaDB → Managed Vector DB** — Migrate to Azure AI Search, Pinecone, or Weaviate
- **Add relational DB** — PostgreSQL for metadata, user management, audit logs (via the same `StorageInterface`)

## Authentication & Authorization

### Current (POC)
- Hardcoded admin/admin credentials
- Simple JWT with no refresh tokens

### Production
- Integrate Azure AD / OAuth2 / OIDC
- Role-based access control (RBAC)
- API key management for programmatic access
- Refresh token rotation

## AI Layer

### Current (POC)
- Direct Gemini API calls
- No rate limiting
- No cost monitoring

### Production
- Add rate limiting and circuit breaker
- Multi-model support (Azure OpenAI, Anthropic, local models)
- Cost tracking per request
- Response caching for repeated questions
- Prompt versioning and A/B testing

## Observability

### Current (POC)
- Console logging

### Production
- Structured logging (JSON) with correlation IDs
- OpenTelemetry integration
- Metrics (Prometheus/Grafana)
- Distributed tracing
- Alerting on errors and latency

## Security

### Current (POC)
- CORS open to localhost
- No input sanitization beyond basic validation
- Secrets in .env file

### Production
- Azure Key Vault / AWS Secrets Manager
- WAF (Web Application Firewall)
- Rate limiting per user
- Input sanitization and content security
- HTTPS everywhere
- Regular dependency vulnerability scanning

## Scalability

### Current (POC)
- Single-process Uvicorn
- In-memory state

### Production
- Gunicorn with multiple workers
- Container orchestration (Kubernetes / Azure Container Apps)
- Horizontal scaling behind load balancer
- Async task queue (Celery/RQ) for long-running analysis
- Redis for session/cache state

## CI/CD

- GitHub Actions pipeline
- Automated tests (unit, integration, E2E)
- Docker image build and push
- Staged deployments (dev → staging → prod)
- Infrastructure as Code (Terraform/Bicep)
