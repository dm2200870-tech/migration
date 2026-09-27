from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.scanner import ProjectScanner

app = FastAPI(
    title="MigrationGuard",
    version="0.3.0",
    description="Database migration safety checker - v0.3",
)


class ScanRequest(BaseModel):
    project_path: str | None = None


@app.get("/health")
def health():
    return {"status": "ok", "service": "migrationguard", "version": "0.3.0"}


@app.post("/scan")
def scan(request: ScanRequest):
    project_root = Path(request.project_path or "/workspace/project").resolve()

    if not project_root.exists():
        raise HTTPException(status_code=404, detail=f"Project path not found: {project_root}")

    if not project_root.is_dir():
        raise HTTPException(status_code=400, detail=f"Project path is not a directory: {project_root}")

    scanner = ProjectScanner(project_root)
    try:
        return scanner.scan()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scan failed: {exc}") from exc
