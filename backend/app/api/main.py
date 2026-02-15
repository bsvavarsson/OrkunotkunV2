from __future__ import annotations

from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ingest.run_backfill import run_incremental_sync

repo_root = Path(__file__).resolve().parents[3]
load_dotenv(repo_root / ".env")

app = FastAPI(title="Orkunotkun API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/sync-data")
async def sync_data() -> dict[str, object]:
    results = await run_incremental_sync(backtrack_days=2, to_date=date.today())

    return {
        "success": True,
        "sources": [
            {
                "source": result.source_name,
                "status": result.status,
                "rows_written": result.rows_written,
                "sync_window": (result.details or {}).get("sync_window"),
                "message": result.message,
            }
            for result in results
        ],
    }
