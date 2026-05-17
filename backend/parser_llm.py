"""
parser_llm.py
Core LLM parsing using Groq API (free tier — llama-3.3-70b-versatile).
"""

import json
import re
import os
from groq import Groq

_client = None


def get_client() -> Groq:
    global _client
    if _client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY not set in environment")
        _client = Groq(api_key=key)
    return _client


SYSTEM_PROMPT = """You are an expert resume parsing engine used in enterprise staffing software.

Extract structured data from raw resume text with maximum accuracy, even when:
- Formatting is inconsistent or messy
- Company names are abbreviated (IBM, MSFT, Goog, FAANG)
- Dates are ambiguous (2018–20, Jan '19, ~2017)
- Skills are listed as acronyms (JS, TS, K8s, TF, PG)

Return ONLY a valid JSON object. No markdown, no preamble, no explanation."""


def build_prompt(text: str) -> str:
    return f"""Parse this resume and return a JSON object with exactly this structure.

SCHEMA:
{{
  "candidate": {{
    "name": "Full name or null",
    "email": "email or null",
    "phone": "phone or null",
    "location": "city/country or null",
    "linkedin": "url or null"
  }},
  "experience": [
    {{
      "title": "Normalized job title",
      "company_raw": "Exactly as written in resume",
      "company_normalized": "Canonical company name",
      "is_acquired": true or false,
      "acquired_by": "parent company if acquired, else null",
      "industry": "Industry sector",
      "naics_category": "Broad NAICS category",
      "start_date": "YYYY-MM or YYYY or Unknown",
      "end_date": "YYYY-MM or YYYY or Present or Unknown",
      "duration_months": estimated integer or null,
      "highlights": ["up to 3 key achievements"],
      "confidence": float 0.0 to 1.0
    }}
  ],
  "skills": [
    {{
      "name": "Normalized skill name",
      "raw": "Exactly as written",
      "cluster": "Frontend or Backend or AI/ML or DevOps or Data or Mobile or Other",
      "proficiency_inference": "Expert or Proficient or Familiar"
    }}
  ],
  "education": [
    {{
      "school_raw": "Exactly as written",
      "school_normalized": "Full canonical name",
      "degree": "Degree type",
      "field": "Field of study",
      "year_end": integer or null,
      "tier": "Elite or Target or Standard",
      "tier_reason": "One sentence explaining the tier"
    }}
  ],
  "extraction_meta": {{
    "total_years_experience": float,
    "career_level": "Junior or Mid or Senior or Staff or Principal or Executive",
    "skills_count": integer,
    "confidence_overall": float 0.0 to 1.0,
    "parsing_issues": ["list any ambiguities"],
    "company_normalization_notes": ["list company name resolutions made"]
  }}
}}

NORMALIZATION RULES:
- Goog or Google Inc → Google
- MSFT or Microsoft Corp → Microsoft
- IBM Corp or Big Blue → IBM
- Meta Platforms or FB → Meta
- JS → JavaScript, TS → TypeScript, K8s → Kubernetes, PG → PostgreSQL
- TF → TensorFlow, K8s → Kubernetes, dbt → dbt (keep lowercase)
- Stanford Univ → Stanford University, MIT stays MIT

ELITE schools: Harvard, MIT, Stanford, Yale, Princeton, Columbia, UPenn, Brown, Dartmouth, Cornell, Caltech, CMU, UC Berkeley (top programs), Oxford, Cambridge.

RESUME TEXT:
{text}"""


def parse_resume_text(text: str) -> dict:
    client = get_client()

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(text)}
        ],
        temperature=0.1,
        max_tokens=2500,
    )

    raw = completion.choices[0].message.content.strip()

    # Strip markdown fences if model wraps in them
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model returned invalid JSON: {e}\n\nRaw output:\n{raw[:500]}")

    result["_usage"] = {
        "input_tokens": completion.usage.prompt_tokens,
        "output_tokens": completion.usage.completion_tokens,
        "model": completion.model,
    }

    return result