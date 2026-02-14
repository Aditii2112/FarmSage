from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import GenerateRequest, GenerateResponse
from app.graph import build_graph

app = FastAPI(title="Climate-Smart Crop Plan Generator")

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

# Serve static files at /web (farm.jpg, index.html, etc.)
app.mount("/web", StaticFiles(directory=WEB_DIR), name="web")

# CORS (fine for hackathon/demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(WEB_DIR / "index.html")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/api", include_in_schema=False)
def api_root():
    return {"message": "API running. POST /api/generate-plans or visit /docs"}

@app.post("/api/generate-plans", response_model=GenerateResponse)
def generate_plans(req: GenerateRequest):
    try:
        out = graph.invoke({"req": req})
        return {
            "farm_profile": out["farm_profile"],
            "constraints": out["constraints"],
            "plans": out["plans"],
            "comparison": out["comparison"],
            "recommendation": out["recommendation"],
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
