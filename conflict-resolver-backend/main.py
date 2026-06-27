import re
import os
import json
from pathlib import Path
from difflib import SequenceMatcher
from hashlib import sha256
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI
from parser import extract_conflict
from ast_analyzer import extract_functions

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

# Load local secrets from the two places this project commonly uses:
# the repo root for Docker Compose and the backend folder for direct FastAPI runs.
load_dotenv(PROJECT_DIR / ".env")
load_dotenv(BASE_DIR / ".env", override=True)

app = FastAPI(title="Git Conflict Resolver API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

# Keep the AI client optional so the app still runs for demos, tests, and Docker
# smoke checks when no private API key is available.
client = (
    AsyncOpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    if GROQ_API_KEY
    else None
)


class ConflictRequest(BaseModel):
    raw_text: str


def is_functionally_identical(code1: str, code2: str) -> bool:
    """
    Compare code after whitespace is removed.

    This catches the easy merge case where both sides changed formatting only,
    which saves an unnecessary AI request and gives the user an instant answer.
    """
    clean1 = re.sub(r'\s+', '', code1)
    clean2 = re.sub(r'\s+', '', code2)
    return clean1 == clean2


def normalize_code(code: str) -> str:
    """Collapse repeated blank space so the model sees a cleaner prompt."""
    return "\n".join(line.rstrip() for line in code.strip().splitlines())


def extract_block_summary(code: str) -> str:
    """Extract a short summary line for the prompt without overloading it."""
    lines = [line.strip() for line in code.splitlines() if line.strip()]
    if not lines:
        return "No meaningful code detected."
    first_line = lines[0]
    if len(first_line) > 120:
        return first_line[:117] + "..."
    return first_line


def build_graph_data(function_names: list[str]) -> dict:
    """Create React Flow friendly graph data from detected function names."""
    nodes = [{"id": "conflict_1", "label": "Merge Conflict Zone", "type": "conflict"}]
    edges = []

    for index, function_name in enumerate(function_names):
        node_id = f"dep_{index}"
        nodes.append({
            "id": node_id,
            "label": f"Function: {function_name}",
            "type": "dependency",
        })
        edges.append({"source": "conflict_1", "target": node_id})

    return {"nodes": nodes, "edges": edges}


def merge_without_ai(parsed_data: dict, reason: str) -> dict:
    """
    Produce a readable fallback resolution when no model response is available.

    The merged block is intentionally conservative: it keeps both versions and
    adds comments that tell the developer exactly why manual review is needed.
    """
    current = parsed_data.get("current_change", "")
    incoming = parsed_data.get("incoming_change", "")
    pre_context = parsed_data.get("pre_conflict_code", "")
    post_context = parsed_data.get("post_conflict_code", "")

    if is_functionally_identical(current, incoming):
        return {
            "resolved_code": f"// AUTO-RESOLVED: only formatting changed.\n{incoming}",
            "explanation": "Both sides are functionally identical after whitespace is ignored.",
            "confidence": "high",
            "needs_manual_review": False,
        }

    matcher = SequenceMatcher(None, current.strip(), incoming.strip())
    similarity = matcher.ratio()
    if similarity >= 0.9:
        return {
            "resolved_code": (
                f"// REVIEW NEEDED: {reason}\n"
                "// The two sides are very similar, so manual review should be quick.\n"
                f"{pre_context}\n"
                f"{current}\n\n"
                f"{incoming}\n"
                f"{post_context}"
            ).strip(),
            "explanation": "The two versions are highly similar, so this is likely a small edit conflict.",
            "confidence": "medium",
            "needs_manual_review": True,
        }

    return {
        "resolved_code": (
            f"// REVIEW NEEDED: {reason}\n"
            "// Current branch version:\n"
            f"{current}\n\n"
            "// Incoming branch version:\n"
            f"{incoming}"
        ),
        "explanation": reason,
        "confidence": "low",
        "needs_manual_review": True,
    }


def build_prompt(parsed_data: dict, found_functions: list[str]) -> str:
    """Package the conflict into a smaller, clearer prompt for the model."""
    pre_context = normalize_code(parsed_data.get("pre_conflict_code", ""))
    current = normalize_code(parsed_data.get("current_change", ""))
    incoming = normalize_code(parsed_data.get("incoming_change", ""))
    post_context = normalize_code(parsed_data.get("post_conflict_code", ""))

    return f"""
You are an expert software engineer resolving a Git merge conflict.

Task:
Return JSON with exactly these keys:
- resolved_code
- explanation
- confidence
- needs_manual_review

Rules:
- Preserve the intent of both sides when possible.
- Prefer the smallest safe change.
- If the result is risky, say so in explanation and set needs_manual_review to true.
- Do not add markdown fences.
- Keep the code valid and concise.

Context before the conflict:
{pre_context or "[none]"}

Current branch code:
{current or "[empty]"}

Incoming branch code:
{incoming or "[empty]"}

Context after the conflict:
{post_context or "[none]"}

Nearby function names:
{found_functions or []}

Current summary:
{extract_block_summary(current)}

Incoming summary:
{extract_block_summary(incoming)}
"""


def build_ai_defaults(reason: str) -> dict:
    """Standardize fallback metadata so the frontend can render it cleanly."""
    return {
        "confidence": "unknown",
        "needs_manual_review": True,
        "reason": reason,
    }


def response_cache_key(parsed_data: dict, found_functions: list[str]) -> str:
    """Create a stable cache key for repeated conflicts."""
    payload = {
        "current": parsed_data.get("current_change", ""),
        "incoming": parsed_data.get("incoming_change", ""),
        "pre": parsed_data.get("pre_conflict_code", ""),
        "post": parsed_data.get("post_conflict_code", ""),
        "functions": found_functions,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return sha256(raw.encode("utf-8")).hexdigest()


@app.post("/api/resolve")
async def resolve_conflict(request: ConflictRequest):
    # First split the conflict marker text into the two competing versions.
    parsed_data = extract_conflict(request.raw_text)

    # Then scan the whole file so the UI can show what functions may be affected.
    found_functions = extract_functions(request.raw_text)
    graph_data = build_graph_data(found_functions)

    current = parsed_data.get('current_change', '')
    incoming = parsed_data.get('incoming_change', '')
    cache_key = response_cache_key(parsed_data, found_functions)

    if is_functionally_identical(current, incoming):
        fallback = merge_without_ai(parsed_data, "Formatting difference only.")
        return {
            "status": "success",
            "parsed_blocks": parsed_data,
            "graph_data": graph_data,
            "ai_resolution": fallback["resolved_code"],
            "explanation": fallback["explanation"],
            "confidence": fallback["confidence"],
            "needs_manual_review": fallback["needs_manual_review"],
            # Backward-compatible fields for older frontend builds.
            "dummy_graph_data": graph_data,
            "dummy_ai_resolution": fallback["resolved_code"],
        }

    if client is None:
        fallback = merge_without_ai(
            parsed_data,
            "AI provider is not configured. Set GROQ_API_KEY to enable model-based resolution.",
        )
        return {
            "status": "needs_review",
            "parsed_blocks": parsed_data,
            "graph_data": graph_data,
            "ai_resolution": fallback["resolved_code"],
            "explanation": fallback["explanation"],
            "confidence": fallback["confidence"],
            "needs_manual_review": fallback["needs_manual_review"],
            "dummy_graph_data": graph_data,
            "dummy_ai_resolution": fallback["resolved_code"],
        }

    prompt = build_prompt(parsed_data, found_functions)

    try:
        completion = await client.chat.completions.create(
            model=GROQ_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": prompt}
            ],
        )

        ai_response = json.loads(completion.choices[0].message.content)
        final_code = ai_response.get("resolved_code", "// Error generating code")
        explanation = ai_response.get("explanation", "AI generated a merged version.")
        confidence = ai_response.get("confidence", "medium")
        needs_manual_review = bool(ai_response.get("needs_manual_review", True))

    except Exception as e:
        fallback = merge_without_ai(parsed_data, f"AI request failed: {e}")
        final_code = fallback["resolved_code"]
        explanation = fallback["explanation"]
        confidence = fallback["confidence"]
        needs_manual_review = fallback["needs_manual_review"]

    return {
        "status": "success",
        "parsed_blocks": parsed_data,
        "graph_data": graph_data,
        "ai_resolution": final_code,
        "explanation": explanation,
        "confidence": confidence,
        "needs_manual_review": needs_manual_review,
        "response_cache_key": cache_key,
        "dummy_graph_data": graph_data,
        "dummy_ai_resolution": final_code,
    }
