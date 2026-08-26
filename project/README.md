# AI-COACH (project)

AI-COACH is an assistive platform for candidate evaluation and interview preparation that combines vector search, resume analysis, and real-time interview simulation to help recruiters and candidates run data-driven hiring conversations.

## Key features

- Cosine-similarity vector search
  - Convert resumes, job descriptions, and candidate answers into dense embeddings and perform fast similarity search to find best-fit candidates or relevant content.
- Resume Analyzer
  - Parse uploaded resumes, extract skills and experience, compute skill-match scores, and produce a concise summary and recommendations for recruiters and candidates.
- Real-time HR Interview (Mock Interviews)
  - Conduct live, interactive mock interviews with the AI interviewer via WebSockets or streaming APIs. Support for role-based prompts (technical, behavioral, managerial) and live feedback.
- Candidate scoring and ranking
  - Score candidates against job descriptions using weighted feature matches, embedding similarity, and custom rules.
- Analytics & Dashboard
  - Track interview metrics, candidate progress, and common skill gaps.
- Integrations
  - Hooks for Applicant Tracking Systems (ATS), calendar scheduling, and video platforms.

## How it works (high level)

1. Text extraction — resumes and job descriptions are parsed into structured text (name, contact, experience, education, skills).
2. Embeddings — text segments are converted to vector embeddings using an embedding model.
3. Indexing — embeddings are stored in a vector index (e.g., FAISS, Milvus, Pinecone) to support nearest-neighbor search.
4. Matching & scoring — cosine similarity between job and candidate vectors produces match scores; rule-based and ML components refine rankings.
5. Real-time interviewing — a streaming LLM-based interviewer uses prompt engineering to ask questions, receive candidate responses, and deliver feedback in real time.

## Stack (suggested / example)

- Languages: Python (backend / ML), JavaScript/TypeScript (frontend)
- Backend framework: FastAPI or Flask
- Frontend: React/Vite (single-page app)
- Vector store: FAISS, Milvus, or a managed provider (Pinecone, Weaviate)
- Embeddings / LLMs: OpenAI embeddings & chat models or an open-source alternative

## Project layout (example)

project/
  README.md        # (this file)
  backend/         # API + embedding + resume parser
  frontend/        # React app for interview UI and dashboards
  infra/           # Docker, docker-compose, k8s manifests
  scripts/         # utility scripts (data import, index build)

## Getting started (local development)

Prerequisites
- Python 3.10+
- Node 18+
- Docker (optional, for vector DB or full stack)

Quick start (example)

```bash
# Backend
cd project/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Set env vars (see .env.example)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd ../frontend
npm install
npm run dev
```

Or run with Docker Compose if provided:

```bash
docker-compose up --build
```

Environment variables (common)
- OPENAI_API_KEY (or other embedding/LLM provider key)
- VECTOR_DB_URL (or host/port for FAISS/Milvus/Pinecone config)
- DATABASE_URL (Postgres/SQLite)
- SECRET_KEY (app secret)
- FRONTEND_URL (for CORS and redirect configuration)

## API endpoints (examples)

- POST /api/upload-resume — upload a resume (PDF/DOCX) and trigger parsing & embedding
- POST /api/resume-analyze — return parsed fields, skill matches, and score
- POST /api/embedding — compute embeddings for arbitrary text
- POST /api/search-candidates — return ranked candidates given a job description or query
- POST /api/interview/start — create a new interview session
- WebSocket /ws/interview/{session_id} — bi-directional stream for real-time mock interview

## Usage examples

Analyze a resume (pseudo-cURL):

```bash
curl -X POST "http://localhost:8000/api/resume-analyze" \
  -H "Authorization: Bearer $API_KEY" \
  -F "file=@/path/to/resume.pdf"
```

Start a real-time interview (pseudo):

1. POST /api/interview/start with job role and prompt
2. Open a WebSocket to /ws/interview/{session_id}
3. Send candidate answers over the socket, receive streaming questions and feedback back

## Developer notes

- Embedding model choice impacts search quality; tune model and chunking strategy for best results.
- Keep a normalized schema for parsed resume fields to support effective scoring and filtering.
- Use a robust file extraction step (e.g., Apache Tika or python-docx + pdfminer) to extract text from uploads.
- Consider privacy and data retention policies — resumes contain PII.

## Features to prioritize / roadmap
- Add interview recording and playback for review
- ATS syncing and bulk resume import
- Interview scoring calibration with human reviewer feedback
- Multilingual resume parsing and interviews

## Contributing

Contributions are welcome. Please open PRs for bug fixes and features. Add tests and update documentation.

## License

Specify your license here (e.g., MIT).