# AI-COACH (project)

AI-COACH is an AI-driven interviewing and candidate-evaluation platform that combines embedding-based (cosine-similarity) vector search, structured resume analysis, and a real-time mock-HR interview experience so recruiters and candidates can match, score, and practice for roles.

## Problem it solves

Hiring is slow, subjective, and noisy. Recruiters and hiring managers must sift through large numbers of resumes, often relying on keyword matching and manual review that miss contextual fit, transferable skills, and soft-skill signals. Candidates lack realistic, data-driven practice and feedback for interviews. AI-COACH addresses these problems by:

- Accelerating candidate discovery with semantic search (vector embeddings + cosine similarity) rather than brittle keyword matching.
- Providing structured resume analysis that extracts skills, experience, and makes match recommendations against job descriptions.
- Enabling realistic, real-time mock interviews that give immediate, actionable feedback and scoring.
- Combining automated scoring with human-in-the-loop review to reduce bias and improve calibration.

## Key features

- Cosine-similarity vector search
  - Convert resumes, job descriptions, interview transcripts, and candidate answers into dense embeddings and perform fast nearest-neighbor search to find best-fit candidates or relevant content.
- Resume Analyzer
  - Parse PDF/DOCX resumes to extract structured fields (contact, roles, dates, skills, education), compute skill-match scores, highlight gaps, and generate recruiter-friendly summaries.
- Real-time HR Interview (Mock Interviews)
  - Bi-directional streaming via WebSockets for live mock interviews: AI interviewer asks role-specific questions, ingests candidate answers, and provides instant feedback and follow-ups.
- Candidate scoring and ranking
  - Combine cosine-similarity scores, rule-based heuristics (years of experience, required skills), and optional ML models to produce calibrated candidate ranks.
- Indexing & Vector Store integration
  - Support for FAISS (local), Milvus (self-hosted), or managed providers (Pinecone, Weaviate) for scalable vector search.
- Explainability & Summaries
  - Provide concise, human-readable summaries and rationale for scores (matched skills, top similar job experiences, red flags).
- Dashboard & Analytics
  - Track interview metrics (average scores, skill gaps, most-asked questions), candidate pipelines, and reviewer feedback.
- Integrations
  - Hooks for ATS systems, calendar scheduling (for interviews), video platforms, and HRIS tools.
- Security & PII protections
  - Configurable retention, encryption in transit/at rest, and optional redaction pipelines for sensitive PII in resumes.

## Advantages / Benefits

- Faster shortlisting: semantic matching surface candidates who are a contextual fit even when keywords differ.
- Consistency & calibration: standardized scoring + human review reduces variability and bias in screening.
- Better candidate experience: realistic mock interviews and detailed feedback help candidates prepare and perform.
- Scalable interviewing: run many mock or screening interviews in parallel with AI assistance.
- Actionable analytics: identify common skill gaps across candidate pools and prioritize training/recruiting needs.

## Stack
- **Language(s):** Python (backend / ML) + JavaScript/TypeScript (frontend) + HTML/CSS
- **Framework / runtime:** FastAPI (recommended) or Flask backend; React + Vite frontend
- **Notable libraries / services:** OpenAI (embeddings / chat), sentence-transformers (local embeddings), FAISS / Milvus / Pinecone (vector store), pdfminer/python-docx/Tika for resume parsing

## How it's organized
project/
  README.md        # project-level overview and developer notes
  backend/         # API, embedding pipeline, resume parsing, scoring services
  frontend/        # React app for interview UI, dashboards, and WebSocket client
  infra/           # Docker, docker-compose, infra manifests for vector DB and services
  scripts/         # import/index-building/maintenance utilities
  docs/            # design docs, architecture diagrams, prompt library (if present)

How it fits together: The backend normalizes input files (resume PDFs/DOCX) into structured text and semantic chunks. Each chunk is embedded and indexed in a vector store. Given a job description or question, the system computes embeddings and uses cosine similarity to find the most relevant resume chunks or candidate answers. The interview module orchestrates streaming conversations: prompts and candidate answers flow through a WebSocket connection; backend LLMs generate questions, follow-ups, and feedback; scoring modules combine embedding similarity and rule-based checks.

## How to run it (example)

Backend
```bash
cd project/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# set env vars (see .env.example)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend
```bash
cd project/frontend
npm install
npm run dev
```

Full stack with Docker Compose (if provided)
```bash
cd project
docker-compose up --build
```

Environment variables (common)
- OPENAI_API_KEY (or other embeddings/LLM key)
- VECTOR_DB_URL (or FAISS/Milvus connection details)
- DATABASE_URL (Postgres/SQLite)
- SECRET_KEY
- FRONTEND_URL

## Typical workflows

1. Bulk ingest resumes: run scripts/import_resumes.py to parse and index resumes into the vector store.
2. Shortlist candidates: POST a job description to /api/search-candidates and receive ranked candidate results with match explanations.
3. Run mock interview: POST /api/interview/start then open WebSocket /ws/interview/{session_id} for real-time Q&A and streaming feedback.
4. Human calibration: export scoring results for human reviewers, collect feedback, and retrain or adjust heuristic weights.

## Privacy & Compliance
- Treat resumes as PII: enable encryption, minimal retention, and deletion workflows.
- Keep embedding/LLM provider policies in mind (e.g., do not send PII to third-party endpoints if not permitted).

## Roadmap / Extensions
- Interview recording and playback with timestamps aligned to transcript and scoring.
- Human-in-the-loop labeling workflow to improve scoring models.
- Multilingual parsing and interview support.
- Calibration dashboards to align AI scores with human reviewers.

## Contributing
Contributions welcome. Please open PRs with tests and update docs. For major changes, open an issue first to discuss the design.

## License
Specify your license here (e.g., MIT).