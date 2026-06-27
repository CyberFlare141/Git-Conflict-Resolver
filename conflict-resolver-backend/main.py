from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from parser import extract_conflict

app = FastAPI(title="Git Conflict Resolver API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the expected structure of incoming data from React
class ConflictRequest(BaseModel):
    raw_text: str

@app.post("/api/resolve")
async def resolve_conflict(request: ConflictRequest):
    # 1. Run the raw text through our parser
    parsed_data = extract_conflict(request.raw_text)
    
    # 2. Return the parsed data PLUS dummy AI resolution data
    # (We will replace the dummy data with real AST/OpenAI logic later)
    return {
        "status": "success",
        "parsed_blocks": parsed_data,
        "graph_data": {
            "nodes": [
                {"id": "conflict_1", "label": "Merge Conflict Zone", "type": "conflict"},
                {"id": "dep_1", "label": "Function: calculateTotal", "type": "dependency"}
            ],
            "edges": [
                {"source": "conflict_1", "target": "dep_1"}
            ]
        },
        "resolution": """
// AI RESOLVED CODE:
function calculateTotal(price, tax) {
    const total = price + (price * tax) + 5; // Kept shipping fee
    return total;
}
        """
    }
