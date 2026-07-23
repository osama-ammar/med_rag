# med-rag Project Documentation

## Purpose

`med-rag` is a minimal Retrieval-Augmented Generation (RAG) service built in Python. It is designed to:

- Ingest files into a project-specific file storage.
- Split documents into chunks.
- Store chunk metadata in a relational database.
- Create and maintain semantic vector indexes.
- Search and answer queries using a combination of embeddings and LLM generation.

The project is educational in nature and demonstrates how to connect file ingestion, vector search, and LLM-based answers in an extensible architecture.

## High-Level Architecture

The application is organized into clear layers:

1. **API layer**

   - `src/main.py`: FastAPI application startup and dependency setup.
   - `src/routes/`: HTTP endpoints grouped by purpose.
     - `routes/base.py`: health/welcome endpoint.
     - `routes/data.py`: file upload and processing APIs.
     - `routes/nlp.py`: indexing, search, and RAG answer APIs.
2. **Controller layer**

   - `src/controllers/`: business logic for file validation, project management, document processing, and NLP operations.
     - `DataController.py`: validate uploads and create safe file paths.
     - `ProjectController.py`: manage project folders.
     - `ProcessController.py`: load and chunk files.
     - `NLPController.py`: handle vector search, indexing, and RAG prompt generation.
3. **Background task layer**

   - `src/tasks/`: asynchronous heavy work via Celery.
     - `file_processing.py`: parse files, split text into chunks, persist chunks into DB.
     - `data_indexing.py`: create or reset vector collections and insert embeddings.
     - `process_workflow.py`: additional workflow orchestration.
     - `maintenance.py`: recurring cleanup jobs.
4. **Storage and model layer**

   - `src/models/`: database access and ORM models.
     - `ProjectModel.py`: create or fetch projects.
     - `AssetModel.py`: store uploaded asset records.
     - `ChunkModel.py`: manage text chunk persistence.
     - `db_schemes/`: SQLAlchemy table definitions.
5. **Provider abstraction layer**

   - `src/stores/llm/`: LLM providers and factory.
     - `LLMProviderFactory.py`: selects OpenAI or Cohere provider.
     - `OpenAIProvider.py`, `CoHereProvider.py`: wrap generation and embedding APIs.
   - `src/stores/vectordb/`: vector database providers.
     - `VectorDBProviderFactory.py`: selects Qdrant or PGVector backend.
     - `QdrantDBProvider.py`, `PGVectorProvider.py`: implement vector index storage and search.
6. **Configuration and utilities**

   - `src/helpers/config.py`: reads `.env` via `pydantic-settings`.
   - `src/utils/metrics.py`: registers Prometheus metrics.
   - `src/utils/idempotency_manager.py`: guards Celery tasks against repeated execution.
   - `src/stores/llm/templates/`: prompt templates for RAG generation.

## Data Flow

1. Client uploads a file to `/api/v1/data/upload/{project_id}`.
2. The file is saved under `src/assets/files/{project_id}` and recorded as an asset.
3. The client requests processing via `/api/v1/data/process/{project_id}` or `process-and-push/{project_id}`.
4. A Celery task loads the file content, chunks it, and saves chunk records in PostgreSQL.
5. A separate indexing task reads chunk records, computes embeddings, and stores them in the selected vector DB backend.
6. Search or answer requests hit `/api/v1/nlp/index/search/{project_id}` and `/api/v1/nlp/index/answer/{project_id}`.
7. The NLP controller retrieves top documents, builds a prompt, and asks the configured LLM for a final answer.

## Key Technologies

- Python 3.10
- FastAPI for REST API
- Celery for background task processing
- PostgreSQL via SQLAlchemy Async + `asyncpg`
- `pgvector` support for vector storage in Postgres
- Qdrant support as an alternate vector data store
- OpenAI and Cohere as abstracted LLM/embedding providers
- `pydantic-settings` for `.env` configuration
- Prometheus metrics integration
- Docker Compose orchestration under `docker/`

## Why These Choices?

- **FastAPI**: easy to define async routes and dependency injection.
- **Celery**: offloads expensive file processing and indexing tasks.
- **SQLAlchemy Async + Postgres**: stable relational store for project, asset, and chunk data.
- **Provider factories**: allow switching LLM and vector DB backends without rewriting business logic.
- **Template parser**: separates prompt text from code so RAG behavior is easier to tune.

## Tradeoffs and Technology Comparison

### Vector database backends

- **Qdrant**
  - Pros: purpose-built vector database, optimized insert/search, easier setup for local/embedded usage via file path.
  - Pros: supports semantic search and payload metadata naturally.
  - Cons: additional dependency and runtime compared to using PostgreSQL only.
  - Good when: you want dedicated vector search performance and flexible vector store features.
- **PGVector (Postgres)**
  - Pros: keeps data in one SQL database, easier transactional consistency with chunk metadata.
  - Pros: no separate vector database deployment if Postgres is already available.
  - Cons: indexing performance and operational overhead can be higher than specialized vector stores for large scale.
  - Good when: you need a compact deployment and want to manage vectors alongside relational data.

### LLM / embedding provider selection

- **OpenAI**
  - Pros: wide model support, mature API, strong default generation quality.
  - Cons: network dependency, cost, and API latency.
  - Good when: production-ready generation and embeddings are required.
- **Cohere**
  - Pros: alternative provider with simpler embedding APIs and chat-style generation support.
  - Cons: may require different prompt formatting and can have different quality characteristics.
  - Good when: you want a second vendor or need a provider with different pricing or model behavior.

### Chunking and document processing

- **Current simple splitter**
  - Pros: easy, predictable flow, minimal dependencies.
  - Cons: may cut documents at arbitrary boundaries and lose sentence/paragraph coherence.
  - Good when: simple text files and fast implementation are the priority.
- **Potential alternatives**
  - `CharacterTextSplitter` / `RecursiveCharacterTextSplitter`: preserve overlap and semantic boundaries better.
  - `SentenceSplitter` or NLP-based chunking: improve answer relevance at the cost of extra complexity.
  - File loader-specific chunking: use PDF or document parsers to preserve structure.

### Prompt generation and RAG strategy

- **Current design**
  - Uses retrieved chunks and a template-based prompt builder.
  - Pros: separation of prompt text from code, easy to tune.
  - Cons: prompt length can grow quickly and may require careful context window management.
- **Alternative strategies**
  - Reranking + retrieval: improve quality by rescoring top documents before generation.
  - Hybrid search: combine keyword and vector search to reduce irrelevant results.
  - Streaming or multi-turn retrieval: useful for longer conversations but adds complexity.

## Core Concepts for New Contributors

- **Routes** are thin and should delegate logic to controllers.
- **Controllers** implement domain behavior and keep route handlers simple.
- **Models** access the database and should be used by controllers or tasks.
- **Tasks** are Celery units for work that may take time or be retried.
- **Providers** abstract external services behind a common interface.
- **Prompt templates** are located under `src/stores/llm/templates/locales/en/rag.py`.

## How to Add a Feature

1. Identify the layer:

   - API endpoint → add route + router entry.
   - New business behavior → add/extend controller.
   - New background job → add a Celery task in `src/tasks/`.
   - New persistence type → add model methods in `src/models/`.
   - New provider backend → implement provider class and register it in the factory.
2. Keep layers separate:

   - Routes call controllers.
   - Controllers call models, providers, and tasks.
   - Tasks reuse controllers and provider factories when possible.
3. Use config objects from `helpers.config` for environment-driven settings.
4. Add new environment variables to `.env` and `helpers/config.py` if needed.
5. Keep prompt content in templates instead of hardcoding text in logic.

## Important Entry Points

- `src/main.py`: application startup, database and provider creation, FastAPI router registration.
- `src/celery_app.py`: Celery app configuration and background worker settings.
- `src/routes/`: endpoint definitions.
- `src/controllers/`: main application behavior.
- `src/stores/llm/` and `src/stores/vectordb/`: backend integration layers.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r src/requirements.txt
   ```
2. Copy environment file:
   ```bash
   cp .env.example .env
   ```
3. Run migrations if configured:
   ```bash
   alembic upgrade head
   ```
4. Start FastAPI:
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 5000
   ```
5. Start Celery worker:
   ```bash
   python -m celery -A src.celery_app worker --queues=default,file_processing,data_indexing --loglevel=info
   ```

## Extension Notes

- To support a new LLM backend, add a provider in `src/stores/llm/providers/` and update `LLMProviderFactory.create()`.
- To support a new vector backend, add a provider in `src/stores/vectordb/providers/` and update `VectorDBProviderFactory.create()`.
- To support new file types, extend `ProcessController.get_file_loader()` and the file chunking logic.
- To expose new application data via API, add route methods in `routes/`, then call controller and model methods as needed.

## Evaluation Techniques

Use these methods to verify that the RAG pipeline is working and to measure model quality:

- **Manual query verification**

  - Upload known documents, index them, and ask questions you already know the answer to.
  - Compare generated answers against a ground truth and note when search results are missing or hallucinated.
- **Semantic search checks**

  - Validate that search results include relevant chunks for given queries.
  - For vector backends, compare nearest-neighbor hits from both Qdrant and PGVector if both are available.
- **Prompt/answer quality checks**

  - Inspect `full_prompt` returned by `/api/v1/nlp/index/answer/{project_id}`.
  - Ensure the retrieved documents are coherent and that the prompt template includes enough context.
- **Regression testing**

  - Create small datasets and use automated tests to verify that answers remain stable after changes.
  - Track metrics such as relevance, precision, and answer completeness through test scripts.
- **Performance monitoring**

  - Measure task duration for file processing and indexing.
  - Observe vector insertion and search latency for each backend.
  - Use Prometheus metrics if available to identify bottlenecks.

## Future Todos

These are practical extensions that would improve robustness, flexibility, and production readiness:

- Add more advanced chunking:

  - support recursive character splitting
  - preserve sentence and paragraph boundaries
  - use language-aware or semantic chunkers
- Support more file formats:

  - Word documents, rich text, HTML, CSV, and audio transcripts.
- Add better RAG prompt management:

  - dynamic temperature and token limits per model
  - retrieval reranking or answer verification
  - multi-turn conversation context
- Improve error handling and observability:

  - richer API error responses
  - logging for failed vector inserts and model calls
  - more comprehensive metrics for task success/failure
- Add automated evaluation tooling:

  - a dedicated test harness for RAG answer quality
  - golden query/answer sets and scoring functions
  - comparison dashboard for Qdrant vs PGVector results
- Expand backend support:

  - add Redis or Milvus as additional vector stores
  - add more LLM providers and local model inference options
  - support hybrid search combining keyword and vector retrieval

## Recommended First Read

- `src/main.py` and `src/celery_app.py`
- `src/routes/data.py` and `src/routes/nlp.py`
- `src/controllers/NLPController.py`
- `src/tasks/file_processing.py`
- `src/stores/llm/LLMProviderFactory.py`
- `src/stores/vectordb/VectorDBProviderFactory.py`

This file should help any new contributor understand the system, locate the core modules, and extend the project safely.


# Med-RAG Radiology Ingestion Roadmap

This roadmap breaks down your first milestone: setting up local report ingestion with structured metadata and section-aware chunking using your existing architecture.

---

## Phase 1: Local Setup & Ollama Integration

- [X] **Configure Local Providers:** Update `src/stores/llm/` to point embeddings and text generation to your local Ollama instance (`http://localhost:11434`).
- [X] **Pull Models:** Run `ollama pull nomic-embed-text` (for embeddings) and `ollama pull llama3` (for local answer generation).

## Phase 2: Sample Data & Metadata Preparation

- [X] **Create Sample Dataset:** Add a `data/sample_reports/` directory to your project root.
- [X] **Draft Test Files:** Create 3-5 text files representing radiology reports containing explicit headers (`INDICATION:`, `FINDINGS:`, `IMPRESSION:`) and basic patient attributes (e.g., `Patient Age: 74`).

## Phase 3: Section-Aware Ingestion & Metadata Parsing

- [X] **Update Parser Logic (`src/controllers/`):** Write a simple regex or rule-based parser to extract patient age and clinical findings separately from raw text files.
- [X] **Bind Metadata to Chunks:** Ensure chunks generated by your background worker carry structured metadata payload (e.g., `age`, `modality`, `diagnosis`) alongside the text.

## Phase 4: Database Storage & Verification

- [X] **Spin Up Stack:** Run `docker compose up -d` to launch PostgreSQL/PGVector, Qdrant, Celery, and FastAPI.
- [X] **Test Ingestion API:** Upload a sample report via the `/api/v1/data/upload/{project_id}` endpoint and trigger processing.
- [X] **Monitor Workers:** Check the Flower dashboard (`http://localhost:5555`) to confirm background task completion without errors.
