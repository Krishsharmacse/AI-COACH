# AI-COACH

AI-COACH is an AI-driven interviewing and candidate-evaluation platform that combines semantic (cosine-similarity) vector search, structured resume analysis, and real-time mock HR interviews to help recruiters and candidates find the best matches, make objective decisions, and practice interviews with data-driven feedback.

## Problem it solves

Hiring is slow, subjective, and error-prone. Keyword-based resume screening misses contextual fit and transferable skills; interview outcomes vary widely across interviewers; and candidates lack realistic, actionable practice. AI-COACH addresses these problems by:

- Surfacing candidates via semantic (embedding) search instead of brittle keyword matching.
- Extracting structured resume data, highlighting skills and experience gaps, and producing recruiter-friendly summaries.
- Running real-time mock interviews (streaming) that give immediate, actionable feedback.
- Combining automated scoring with human-in-the-loop review to reduce bias and improve calibration.

## Key features

- Cosine-similarity vector search
  - Convert resumes, job descriptions and candidate answers into embeddings and perform fast nearest-neighbor search.
- Resume Analyzer
  - Parse PDF/DOCX resumes into structured fields (contact, roles, dates, skills), compute skill-match scores, and generate summaries/recommendations.
- Real-time HR Interview (Mock Interviews)
  - Bi-directional streaming using WebSockets for live AI interviewer <> candidate interactions with follow-ups and feedback in real time.
- Candidate scoring & ranking
  - Blend cosine-similarity with rule-based heuristics (years of experience, required skills) and optional ML models to produce calibrated ranks.
- Indexing & Vector store integration
  - Support for FAISS (local), Milvus (self-hosted), or managed providers like Pinecone/Weaviate.
- Explainability & Summaries
  - Provide human-readable rationale for scores: matched skills, top-similar resume snippets, and red flags.
- Dashboard & analytics
  - Track metrics (average scores, skill gaps, frequent questions), pipeline progress and reviewer feedback.
- Integrations
  - Hooks for ATS systems, calendars, video platforms, and HRIS tools.
- Security & PII protections
  - Configurable retention policies, encryption in transit & at rest, and optional PII redaction pipelines.

## Advantages / Benefits

- Faster shortlisting: find contextual matches even when keywords differ.
- Consistency & calibration: standardized scoring reduces reviewer variability and bias.
- Better candidate experience: realistic mock interviews and detailed feedback improve preparedness.
- Scalable interviewing: run many mock/screening interviews in parallel with AI assistance.
- Actionable analytics: identify common skill deficits and hiring bottlenecks.

## Tech stack (recommended)

- Languages: Python (backend/ML) + JavaScript/TypeScript (frontend)
- Backend: FastAPI (ASGI) or Flask (WSGI) recommended for REST + WebSocket endpoints
- Frontend: React + Vite
- Embeddings / LLMs: OpenAI (or open-source alternatives / sentence-transformers)
- Vector store: FAISS (local), Milvus (self-hosted), or Pinecone/Weaviate (managed)
- Resume parsing: pdfminer / python-docx / Apache Tika
- Persistence: Postgres / SQLite for metadata
- Docker & docker-compose for local dev

## Repository layout (suggested)

project/
  README.md          # project-level notes (present)
  backend/           # API, embedding pipeline, resume parsing, scoring services
  frontend/          # React app for interview UI, dashboards, WebSocket client
  infra/             # Docker, docker-compose, k8s manifests (optional)
  scripts/           # import/index-building/maintenance utilities
  docs/              # architecture, prompt library, API docs (optional)

## How it fits together (high level)

1. Resume ingestion: resumes (PDF/DOCX) are parsed into structured text and normalized fields.
2. Chunking & embeddings: text chunks are embedded with an embedding model and stored/indexed in a vector DB.
3. Matching & ranking: given a job description or query, compute embeddings and perform nearest-neighbor search (cosine similarity) to find relevant candidates and resume snippets. Combine with rule-based scores.
4. Real-time interview: frontend opens a WebSocket to the backend; the backend orchestrates LLM prompts, generates interview questions, accepts candidate answers, performs scoring on the fly, and streams feedback.
5. Human-in-the-loop: reviewers can see summarized rationale and adjust scores; feedback can be used to retrain or tune heuristics.

## Quickstart — local development

Prerequisites:
- Python 3.10+
- Node 18+
- Docker & docker-compose (optional, recommended for vector DB or full stack)
- An embeddings/LLM provider API key (OPENAI_API_KEY or alternative)

Backend
```bash
cd project/backend
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
# copy .env.example -> .env and set env vars
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend
```bash
cd project/frontend
npm install
npm run dev
```

Full stack with Docker Compose (if infra/docker-compose.yml is present)
```bash
cd project
docker-compose up --build
```

## Environment variables (.env.example)

- OPENAI_API_KEY=your_openai_api_key_or_other_provider_key
- VECTOR_DB_URL=postgres://user:pass@host:port/vectordb    # or provider-specific URL
- VECTOR_DB_TYPE=faiss|milvus|pinecone|weaviate
- DATABASE_URL=postgres://user:pass@localhost:5432/appdb
- SECRET_KEY=your-app-secret
- FRONTEND_URL=http://localhost:5173
- DATA_RETENTION_DAYS=90
- LOG_LEVEL=info

## Example docker-compose snippet (local dev)

```yaml
version: '3.8'
services:
  backend:
    build: ./project/backend
    ports:
      - "8000:8000"
    env_file:
      - ./project/.env
    depends_on:
      - vectordb
      - postgres

  frontend:
    build: ./project/frontend
    ports:
      - "5173:5173"
    env_file:
      - ./project/.env

  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: example
      POSTGRES_DB: appdb
    volumes:
      - pgdata:/var/lib/postgresql/data

  vectordb:
    # Example: Milvus quickstart container or a placeholder for FAISS helper.
    image: milvusdb/milvus:v2.2.9
    environment:
      # milvus envs...
    ports:
      - "19530:19530"

volumes:
  pgdata:
```

Adjust vectordb service to your chosen vector store (FAISS might run as a local process inside backend; Milvus/Pinecone require separate setup).

## Core API endpoints (examples)

- POST /api/upload-resume
  - Upload a resume (multipart/form-data file). Returns parsed fields & candidate ID.
- POST /api/resume-analyze
  - Body: { "candidate_id": "...", "file_url": "..." } — returns parsed JSON, extracted skills, summary and scores.
- POST /api/embedding
  - Body: { "text": "..." } — returns embedding vector (for debugging).
- POST /api/search-candidates
  - Body: { "job_description": "...", "filters": { ... }, "top_k": 10 } — returns ranked candidate list with match explanations.
- POST /api/interview/start
  - Body: { "role": "Backend Engineer", "difficulty": "medium", "candidate_id": "...", "prompt_overrides": { ... } } — returns session_id and initial prompt.
- WebSocket /ws/interview/{session_id}
  - Bi-directional stream for interview messages (see contract below).

Example cURL: analyze resume
```bash
curl -X POST "http://localhost:8000/api/resume-analyze" \
  -H "Authorization: Bearer $API_KEY" \
  -F "file=@/path/to/resume.pdf"
```

## WebSocket contract (message examples)

Client -> Server (JSON)
```json
{ "type": "answer", "turn": 1, "text": "My experience includes..." }
```

Server -> Client (JSON)
```json
{ "type": "question", "turn": 2, "text": "Tell me about a time you..."}
```

Server -> Client (JSON streaming feedback)
```json
{ "type": "feedback", "turn": 1,
  "score": 3.7,
  "highlights": ["structured answer", "good technical depth"],
  "notes": "Add more metrics to quantify impact."
}
```

Client -> Server (end interview)
```json
{ "type": "end", "reason": "candidate_finished" }
```

Adjust fields to include timestamps, audio references, or chunk IDs for alignment with transcripts/recordings.

## Scoring & explainability

Scoring is a hybrid of:
- Cosine-similarity on embedding vectors between job description and resume chunks.
- Heuristic rules (required skills presence, years of experience, education).
- Optional ML ranking model trained on labeled data.

Explainability outputs include:
- Top matched resume snippets (with cosine scores).
- Matched skill list and gap highlights.
- Human-readable rationale and reviewer notes.

## Data privacy & security

- Treat resumes as PII — use encryption at rest & TLS in transit.
- Provide configurable retention & purge policies; consider redaction before sending to third-party LLMs if policy requires.
- Log and audit access to candidate data.
- Carefully review LLM provider data policies before sending PII.

## Typical workflows

- Bulk ingest: run `scripts/import_resumes.py` to parse & index resumes.
- Shortlist: POST a job description to `/api/search-candidates` and review ranked candidates.
- Interview: POST `/api/interview/start`; open WebSocket `/ws/interview/{session_id}` to conduct the mock interview in real time.
- Calibrate: Export results for human review, adjust scoring heuristics, and repeat.

## Monitoring & analytics

- Track interview duration, average score, common weak skills, and question difficulty.
- Dashboard should show candidate pipeline stages and reviewer agreement metrics to spot bias.

## Roadmap / Extensions

- Interview recording & playback with transcript + timestamp alignment.
- Human-in-the-loop labeling UI to collect labeled outcomes and retrain ranking models.
- Multilingual parsing & interviewing.
- Better bias detection & calibration tooling.
- ATS sync & bulk resume importers.

## Developer notes & best practices

- Chunking strategy is important: use semantic-friendly chunk sizes (e.g., 150–500 tokens) and include context metadata (role, dates).
- Keep consistent schema for parsed resume fields.
- Tune embedding model and vector store parameters (metric, index type) for your dataset.
- Test privacy flows end-to-end: verify redaction and retention settings.
- Provide an admin interface for scoring weights, domain-specific prompts, and question libraries.

## Contributing

Contributions are welcome:
1. Fork the repo.
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Add tests and update docs.
4. Open a PR describing the change.

For large changes, open an issue first to discuss design.

## License

Specify your license here (for example, MIT). Add `LICENSE` file at repo root.

## Acknowledgements

- Embedding & LLM providers used as examples: OpenAI, sentence-transformers.
- Vector stores: FAISS, Milvus, Pinecone.

## FAQ / Try asking

- "Where is the resume parsing entrypoint (which file)? Look for `project/backend` — is there a parser module like `backend/services/parser.py` or `app/services/parser.py`?"
- "How do I run the WebSocket interview client from the frontend? Which files under `project/frontend/src` implement the socket and UI (e.g., `src/components/Interview.jsx` and `src/ws-client.js`)?"
- "What vector-store configuration is used in infra/docker-compose.yml — is it Milvus, FAISS helper, or a managed provider like Pinecone?"

If you'd like, I can:
- Generate this file in your repo root (README.md).
- Create `.env.example` and `infra/docker-compose.yml` with concrete parameters for a small local dev setup (Postgres + Milvus + backend + frontend).
- Create API docs / OpenAPI schema for the backend endpoints.
- Produce sample prompt templates and interview question libraries for different roles (technical, behavioral, managerial).
