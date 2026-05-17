"""
ResumeIQ - AI Resume Parsing & Enrichment Platform

"""

import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import tempfile
import traceback

load_dotenv()

from parser_llm import parse_resume_text
from pdf_extractor import extract_text_from_pdf, extract_text_from_docx

app = FastAPI(
    title="ResumeIQ API",
    description="AI-powered resume parsing and enrichment",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ────────────────────────────────────────────────────────────────────

class TextRequest(BaseModel):
    text: str


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    key = os.getenv("GROQ_API_KEY", "")
    return {
        "status": "ok",
        "api_key_set": bool(key and key.startswith("gsk_")),
    }


@app.post("/parse/text")
async def parse_text(req: TextRequest):
    """Parse resume from raw pasted text."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    try:
        result = parse_resume_text(req.text)
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/parse/file")
async def parse_file(file: UploadFile = File(...)):
    """Parse resume from uploaded PDF or DOCX."""
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower()

    if ext not in ("pdf", "docx", "txt"):
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, or TXT supported")

    contents = await file.read()

    try:
        if ext == "pdf":
            text = extract_text_from_pdf(contents)
        elif ext == "docx":
            text = extract_text_from_docx(contents)
        else:
            text = contents.decode("utf-8", errors="ignore")

        if not text.strip():
            raise HTTPException(status_code=422, detail="Could not extract text from file")

        result = parse_resume_text(text)
        result["source_filename"] = filename
        return result

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── Serve frontend ────────────────────────────────────────────────────────────

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "public")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
