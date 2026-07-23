# med-rag

med-rag is a minimal Retrieval-Augmented Generation (RAG) service for ingesting files, processing them into chunks, indexing semantic embeddings, and answering questions using a knowledge base.

![med-rag Dashboard](src/static/ui-screenshot.svg)

## Overview

This repository provides a complete prototype for a document-centric RAG pipeline with:

- Project-level file upload and document management
- Background processing and chunking via Celery
- Semantic indexing via vector stores (Qdrant and PGVector)
- Search and answer APIs for RAG-style query handling
- Prometheus and Grafana monitoring integration
- A simple browser UI for managing projects, documents, and dashboards

## UI

The web interface includes:

- A project creation panel
- Document upload and list management
- Buttons to process files and build vector indexes
- A chat-based query interface for project-specific knowledge
- A dashboard section to open monitoring tools such as Flower, Grafana, Prometheus, RabbitMQ, and Qdrant

## Acknowledgment

This project is inspired by the `minirag` course by Abubakr Channed. It adapts the original architecture and UX for the `med-rag` workflow while extending the prototype with evaluation techniques, enhanced chunking, and other planned improvements documented in the TODO list.

## Architecture map

The application is composed of the following connected services:

```text
Browser UI
    │
    ▼
FastAPI app (src/main.py)
    │
    ├─> /api/v1/data/upload/{project_id}      (file upload)
    ├─> /api/v1/data/process/{project_id}     (enqueue chunking)
    ├─> /api/v1/nlp/index/push/{project_id}   (enqueue indexing)
    ├─> /api/v1/nlp/index/search/{project_id} (semantic search)
    └─> /api/v1/nlp/index/answer/{project_id} (RAG answer)
    │
    ├─> Celery broker (RabbitMQ)
    │       │
    │       └─> Celery worker / beat / Flower dashboard
    │
    ├─> Results backend (Redis)
    │
    ├─> SQL database (Postgres / pgvector)
    │
    └─> Vector store
          ├─ Qdrant
          └─ PGVector (Postgres)

Monitoring and dashboards:
    ├─ Grafana
    ├─ Prometheus
    ├─ Flower
    └─ RabbitMQ management UI
```

## Run locally

The repository includes a Docker Compose setup for the application and monitoring stack.

### Start the stack

```bash
docker compose up -d
```

### Stop the stack

```bash
docker compose down -v --remove-orphans
```

### Service URLs

- Application (FastAPI): `http://localhost:8000`
- Web UI (via Nginx): `http://localhost`
- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`
- Flower (Celery dashboard): `http://localhost:5555`
- RabbitMQ management UI: `http://localhost:15672`
- Qdrant UI: `http://localhost:6333/dashboard`

## How to connect

1. Start Docker Compose.
2. Open the web UI using `http://localhost`.
3. Create a project, upload files, and process them.
4. Use the `Service Dashboards` buttons in the UI to open monitoring tools.
5. To inspect Celery tasks, use Flower at `http://localhost:5555`.
6. To monitor application metrics, use Grafana and Prometheus at their respective URLs.

## Configuration

Environment variables are loaded from `.env` files under `docker/env/`.

Key components:

- `docker/docker-compose.yml` configures services for FastAPI, Celery, Redis, RabbitMQ, Prometheus, Grafana, Qdrant, and PostgreSQL.
- `src/helpers/config.py` reads application and Celery settings.
- `src/main.py` starts the FastAPI application.
- `src/celery_app.py` configures Celery for asynchronous job execution.

## Key source locations

- `src/static/index.html` — browser UI
- `src/routes/` — API endpoint definitions
- `src/controllers/` — business logic for uploads, processing, and NLP
- `src/tasks/` — Celery background jobs
- `src/stores/llm/` — LLM and embedding provider abstractions
- `src/stores/vectordb/` — vector database backends
- `src/utils/metrics.py` — Prometheus metrics support

## Future todos

**Stage 0: Advanced Data Ingestion & Chunking**

- [X] **Implement Smart Chunking:** Move away from fixed-size chunking.

  - [X] Add Recursive Character Chunking (to keep paragraphs and sentences naturally grouped).
  - [ ] Add Semantic Chunking (splitting chunks based on embedding similarity drops between sentences).
- [ ] **Metadata Enrichment:** Attach rich metadata to chunks (e.g., source file name, section headers, timestamps) to enable precise filtering.
- [ ] **Stage 1: Dense & Sparse Retrieval (Hybrid Search)**

  - [ ] Implement vector embeddings (Dense Search) for semantic matching.
  - [ ] Implement a keyword-matching algorithm like BM25 (Sparse Search) for exact IDs or terms.
  - [ ] Combine and re-score results using Reciprocal Rank Fusion (RRF).
- [ ] **Stage 2: Cross-Encoder Reranking**

  - [ ] Integrate a reranker model (e.g., `sentence-transformers` with a Cross-Encoder like `bge-reranker-base`).
  - [ ] Update the retrieval pipeline to fetch a wider pool (e.g., top 20 chunks) and filter them down to the top 3-5 via the reranker before sending to the generator.
- [ ] **Query Rewriting / Expansion:** Handle vague or conversational user inputs by routing them through a quick prompt step or HyDE (Hypothetical Document Embeddings) before hitting the vector database.
- [ ] **Retrieval Fallback / Guardrails:** Implement a checker to grade retrieved chunks; if relevance scores fall below a certain threshold, trigger a fallback mechanism (e.g., asking the user to clarify or expanding search scope).S
- [ ] **Automated Evaluation Framework:** Integrate an evaluation toolkit (like RAGAS) to test pipeline changes against a benchmark test set.
- [X] Track Core Production Metrics:

  - [X] **Faithfulness:** Does the generator hallucinate, or is the answer strictly backed by context?
  - [X] **Context Precision/Recall:** Did the retriever pull the right chunks?
  - [X] **Answer Relevance:** Does the response address the user's intent?
- [ ] **Latency & Cost Monitoring:** Track round-trip time across embedding generation, vector search, reranking, and final LLM generation.

## AWS Production Deployment Architecture

- [ ] **Data Lake Layer:** Configure an Amazon S3 bucket for raw document staging with lifecycle rules and versioning enabled.
- [ ] **Ingestion & Processing:** Set up S3 Event Notifications to trigger a processing script (via AWS Lambda or ECS) for document parsing and chunking.
- [ ] **Vector Storage:** Provision Amazon OpenSearch Serverless (or Bedrock Knowledge Bases) to store vector embeddings securely.
- [ ] **Application Backend:** Containerize the RAG API (FastAPI) using Docker and deploy via Amazon ECS with an Application Load Balancer (ALB).
- [ ] **Secrets & Security:** Store database connection strings, API keys, and model tokens securely using AWS Secrets Manager and manage access via IAM roles.

## Notes

This project is designed as an extensible RAG prototype. The UI is intentionally lightweight, and the dashboard links are included so operators can inspect Celery, Prometheus, Grafana, RabbitMQ, and Qdrant while the system runs.
