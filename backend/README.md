# Backend Phase 1 Setup

## Recommended Python Version

Use Python 3.11 for the Phase 1 backend setup. It is stable, well-supported by FastAPI and common AI tooling, and works well for future multi-agent expansion.

## Virtual Environment Setup

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### macOS / Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the Backend Server

```bash
uvicorn backend.app:app --reload
```

## Example API Request

```bash
curl -X POST "http://127.0.0.1:8000/analyze-repository" \
  -H "Content-Type: application/json" \
  -d "{\"repo_url\": \"https://github.com/user/repo\"}"
```
