# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
# Quick start (from repo root)
./run.sh

# Manual start (from repo root)
cd backend && uv run uvicorn app:app --reload --port 8000
```

The server runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

Requires a `.env` file in the repo root:
```
ANTHROPIC_API_KEY=your-key-here
```

## Package Management

Always use `uv` for all dependency management and Python execution. Never use `pip` directly.

```bash
uv sync          # Install dependencies
uv add <pkg>     # Add a new package
uv remove <pkg>  # Remove a package
uv run <cmd>     # Run any command in the project environment
```

Dependencies are declared in `pyproject.toml`. Python 3.13+ required.

## Architecture

The backend is a FastAPI app (`backend/app.py`) that orchestrates a RAG pipeline:

1. **On startup** — `app.py` calls `RAGSystem.add_course_folder("../docs")` to ingest `.txt`/`.pdf`/`.docx` files from `docs/`. Already-indexed courses are skipped.

2. **On query** (`POST /api/query`) — `RAGSystem.query()` sends the user question to Claude via `AIGenerator`. Claude is given a `search_course_content` tool. If Claude calls the tool, `ToolManager` dispatches it to `CourseSearchTool`, which queries `VectorStore` (ChromaDB). Claude then synthesizes the search results into a final answer.

3. **Session context** — `SessionManager` keeps the last 2 exchanges (configurable via `MAX_HISTORY`) in memory per session. Sessions are identified by a string ID passed in the request.

### Key component relationships

```
RAGSystem
├── DocumentProcessor  — parses course files into Course/Lesson/CourseChunk models
├── VectorStore        — ChromaDB wrapper; two collections: course_catalog, course_content
├── AIGenerator        — Anthropic API client; handles the tool-use loop
├── SessionManager     — in-memory conversation history
└── ToolManager        — registry for tools Claude can call
    └── CourseSearchTool — the only registered tool; delegates to VectorStore.search()
```

### Course document format

Files in `docs/` must follow this structure for `DocumentProcessor` to parse them correctly:
```
Course Title: <title>
Course Link: <url>
Course Instructor: <name>
Lesson 1: <lesson title>
Lesson Link: <url>
<lesson content...>
Lesson 2: <lesson title>
...
```

### Configuration

All tuneable values live in `backend/config.py`:
- `ANTHROPIC_MODEL` — Claude model to use
- `EMBEDDING_MODEL` — sentence-transformers model (default: `all-MiniLM-L6-v2`)
- `CHUNK_SIZE` / `CHUNK_OVERLAP` — text chunking parameters
- `MAX_RESULTS` — number of ChromaDB results returned per search
- `CHROMA_PATH` — where ChromaDB persists data (default: `./chroma_db` relative to `backend/`)

### Frontend

The frontend (`frontend/`) is a plain HTML/CSS/JS single-page app served as static files by FastAPI. It maintains a `session_id` in memory and sends it with each `POST /api/query` request.
