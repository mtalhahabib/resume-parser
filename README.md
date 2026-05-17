# ResumeIQ — AI Resume Parsing & Enrichment Platform

> Portfolio demo built for Upwork.  
> Powered by Claude claude-sonnet-4-20250514 · FastAPI · Python

---

## What this system does

- **Extracts** structured data from raw resume text (messy, abbreviated, multi-column)
- **Normalizes** company names (`Goog` → `Google`, `MSFT` → `Microsoft`, `IBM Corp` → `IBM`)
- **Detects** acquired companies (`Nimbus Analytics` → acquired by Salesforce)
- **Maps skills** to taxonomy clusters: Frontend / Backend / AI/ML / DevOps / Data
- **Normalizes skill abbreviations** (`K8s` → `Kubernetes`, `TF` → `TensorFlow`, `PG` → `PostgreSQL`)
- **Scores education** (Elite / Target / Standard — Ivy League, MIT, Stanford, etc.)
- **Infers proficiency** from context (Expert / Proficient / Familiar)
- **Accepts PDF / DOCX / TXT uploads** as well as pasted text
- Returns a **structured JSON output** ready for ATS or database insertion

---

## Project structure

```
resume-parser/
├── backend/
│   ├── main.py            ← FastAPI app (routes + file serving)
│   ├── parser_llm.py      ← Claude API calls + prompt engineering
│   ├── pdf_extractor.py   ← PDF/DOCX text extraction
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── public/
│       └── index.html     ← Full UI (open directly in browser)
├── tests/
│   └── test_parser.py     ← 3 end-to-end tests (no pytest needed)
└── README.md
```

---

## Setup — 5 steps, ~3 minutes

### Step 1 — Get your Anthropic API key

1. Go to https://console.anthropic.com/
2. Sign in → API Keys → Create Key
3. Copy the key (starts with `sk-ant-...`)

### Step 2 — Set up the backend

```bash
# Clone or unzip this project, then:
cd resume-parser/backend

# Create and activate a virtual environment (recommended)
python -m venv venv

# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3 — Add your API key

```bash
# Copy the template
cp .env.example .env

# Open .env in any text editor and replace the placeholder:
# ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE
```

On Windows (no cp command): manually copy `.env.example`, rename it to `.env`, open in Notepad, paste your key.

### Step 4 — Start the backend

```bash
# From the backend/ folder, with venv active:
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Verify it's working: open http://localhost:8000/health in your browser.  
You should see: `{"status":"ok","api_key_set":true}`

If `api_key_set` is false — check your `.env` file is in the `backend/` folder and the key starts with `sk-ant-`.

### Step 5 — Open the frontend

```bash
# Just open this file directly in Chrome/Firefox — no server needed:
open frontend/public/index.html       # macOS
start frontend/public/index.html      # Windows
xdg-open frontend/public/index.html  # Linux
```

OR — the backend serves it too. Once uvicorn is running, go to:
http://localhost:8000/

---

## Running tests

```bash
cd resume-parser/backend
source venv/bin/activate   # if not already active

# Run the test suite (makes real API calls — costs ~$0.05 total):
python ../tests/test_parser.py
```

Tests cover:
- **Test 1** — Clean resume: Google + AWS + MIT → basic extraction
- **Test 2** — Messy resume: abbreviations, bad dates, acquired company detection
- **Test 3** — Senior/VP resume: multi-role, Twitter/X normalization, Harvard scoring

Expected output:
```
ResumeIQ Parser — Test Suite
Using Claude claude-sonnet-4-20250514

============================================================
TEST 1: Clean Resume (Google + AWS + MIT)
============================================================
  ✓  Candidate name extracted
  ✓  Email extracted
  ✓  Found 3 experience entries (expected ≥2)
  ✓  Google and Amazon normalized correctly
  ✓  Found 12 skills
  ✓  Clusters: {'Frontend', 'Backend', 'DevOps', 'AI/ML'}
  ✓  MIT correctly tiered as Elite
  ✓  Years experience: 7.5
  ✓  Overall confidence: 0.93

  PASS ✓
...

  All 3 tests passed.
```

---

## API reference

### `GET /health`
Check backend + API key status.

### `POST /parse/text`
Parse resume from pasted text.
```json
Request body:  { "text": "John Smith\njohn@email.com\n..." }
Response:      { "candidate": {...}, "experience": [...], "skills": [...], ... }
```

### `POST /parse/file`
Parse resume from uploaded PDF, DOCX, or TXT.
```
Form field: file (multipart/form-data)
```

---

## Demo script (for your Upwork video)

1. Open http://localhost:8000 in browser
2. Click **"Messy + abbreviations"** demo chip
3. Hit **Parse & Enrich Resume** — show the pipeline steps animating
4. Point out: `Goog → Google`, `MSFT → Microsoft`, `Nimbus Analytics → acquired by Salesforce`
5. Click **Skills tab** — show K8s → Kubernetes, cluster grouping, proficiency inference
6. Click **Education tab** — show Stanford + MIT both scored as Elite
7. Click **JSON Output tab** — show the structured data, click Copy JSON
8. Upload a real PDF resume to show file upload works

That's your full demo — covers every bullet point in the job description.

---

## Troubleshooting

**`ANTHROPIC_API_KEY not set`**  
→ Make sure `.env` is in the `backend/` folder (not the root). File must be named exactly `.env`.

**`ModuleNotFoundError: pdfplumber`**  
→ Run `pip install -r requirements.txt` with your venv active.

**Frontend shows "Backend offline"**  
→ Make sure uvicorn is running on port 8000. Check terminal for errors.

**JSON parse error from Claude**  
→ Rare. Usually means the resume text is extremely short. Add more content to the resume.

**PDF text extraction is empty**  
→ The PDF is likely a scanned image (not text-based). For portfolio purposes, use text-based PDFs or paste text directly.
