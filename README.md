# Resume Tailor

An AI-powered resume tailoring web application that rewrites your resume bullet points to match a target job description — without fabricating any experience.

> Originally: "Spending too much time tailoring your resume for jobs? Use this website for automatic tailoring which includes moving experience around, adding keywords, preserving your formatting or more."

## Features

- 📄 **Upload** PDF or DOCX resumes (up to 10 MB)
- 🤖 **AI Tailoring** with OpenAI GPT-4o-mini
- 🎛️ **Three modes**: Conservative, Balanced, Aggressive
- ✅ **Anti-fabrication guardrails** — never invents employers, degrees, or titles
- 🔍 **Diff view** — see every change with original vs. revised text
- 📥 **Download** tailored resume as DOCX or PDF
- 🔒 **Privacy-first** — files are session-only, never permanently stored

## Architecture

```
backend/   FastAPI (Python 3.11)
frontend/  Next.js 14 + TailwindCSS (TypeScript)
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- OpenAI API key

### 1. Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-your-key-here

# Run the API server
uvicorn app.main:app --reload --port 8000
```

API docs available at http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

Open http://localhost:3000

### 3. Docker Compose (Full Stack)

```bash
# Copy and configure environment
cp backend/.env.example .env

# Set your API key
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# Start both services
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Running Tests

```bash
cd backend

# Install dependencies (if not already done)
pip install -r requirements.txt

# Run all tests (no OpenAI key required — LLM calls are mocked)
pytest tests/ -v

# Run specific test file
pytest tests/test_parser.py -v
```

## Environment Variables

### Backend (`.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ Yes | — | OpenAI API key for GPT-4o-mini |
| `SESSION_DIR` | No | `/tmp/sessions` | Directory for session files |

### Frontend

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API URL |

## API Reference

### `POST /api/upload`
Upload a resume file and job description.

**Request**: `multipart/form-data`
- `file`: PDF or DOCX file (max 10 MB)
- `job_description`: Job description text

**Response**: `{ session_id, filename, message }`

### `POST /api/tailor`
Run the tailoring pipeline.

**Request body**:
```json
{
  "session_id": "uuid",
  "job_description": "...",
  "aggressiveness": "balanced",
  "keyword_emphasis": true,
  "no_reordering": false
}
```

**Response**: `{ session_id, diff_report, preview_html }`

### `GET /api/download/{session_id}/{format}`
Download tailored resume. `format` is `docx` or `pdf`.

## Project Structure

```
backend/
  app/
    main.py              # FastAPI app with CORS
    models/
      ir.py              # Resume Intermediate Representation (Pydantic v2)
      schemas.py         # API request/response schemas
    services/
      parser.py          # PDF + DOCX → IR parser
      llm.py             # OpenAI integration (mockable via Protocol)
      editor.py          # Editing algorithm with aggressiveness modes
      generator.py       # IR → DOCX + PDF output
      diff.py            # Diff report generator
    routers/
      upload.py          # POST /api/upload
      tailor.py          # POST /api/tailor
      download.py        # GET /api/download/{session_id}/{format}
    prompts/
      templates.py       # All LLM prompt templates
  tests/
    conftest.py          # Fixtures (sample_ir, sample_jd_analysis)
    test_parser.py       # DOCX parsing tests
    test_editor.py       # Editing algorithm tests
    test_diff.py         # Diff report tests
    test_guardrails.py   # Anti-fabrication guardrail tests
    test_generator.py    # DOCX/PDF generation tests

frontend/
  src/
    app/
      page.tsx           # Upload + settings page
      review/page.tsx    # Diff review + download page
      layout.tsx
      globals.css
    components/
      FileUpload.tsx      # Drag-and-drop file upload
      JobDescriptionInput.tsx
      TailoringSettings.tsx
      DiffViewer.tsx      # Color-coded diff with expandable cards
      DownloadButtons.tsx
    lib/
      api.ts             # API client functions
      types.ts           # TypeScript types
```

## Design Decisions

### Anti-Fabrication Guardrails
1. **Prompt-level**: System prompt explicitly forbids inventing employers/degrees/dates
2. **Post-processing**: `editor.py` restores immutable fields (employer, title, dates) after LLM edit
3. **Verifier**: A second LLM call checks for fabrications and returns a structured report
4. **Diff check**: `diff.py` detects new employer names and flags them as warnings

### Privacy
- Files are stored in `/tmp/sessions/{session_id}/` — ephemeral storage
- No database, no user accounts
- Sessions are cleaned up automatically by the OS

### Mock-Friendly Architecture
The `LLMService` accepts an `LLMClient` Protocol, enabling full mocking without any OpenAI key in tests.

### ATS Safety
- If the original resume has no tables, the generator never adds tables
- `diff.py` flags any table introduction as an ATS warning

## License

MIT
