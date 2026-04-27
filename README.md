# AI Repository Agent

A multi-agent repository analysis and dashboard project built with a Python backend and a React frontend.

This workspace contains an AI-driven repository intelligence system organized into a backend API, analysis agents and a frontend dashboard UI.

## Project Overview

- `ai-repository-agent/backend`: FastAPI backend for repository analysis orchestration.
- `ai-repository-agent/agents`: Python agent implementations for code review, security scanning, documentation, and learning.
- `ai-repository-agent/src`: React + Vite frontend dashboard with routing and visualization.
- `ai-repository-agent/workspace`: data storage areas for intelligence, knowledge, and logs.

## Key Features

- AI-powered repository analysis
- Multi-agent architecture for code quality, security and developer intelligence
- Web dashboard for result visualization
- FastAPI backend with CORS support

## Prerequisites

- Python 3.11
- Node.js 18+ or compatible version for Vite
- npm or yarn for frontend dependencies

## Installation

### Backend

From the repository root:

```powershell
cd "c:\Desktop\hackthon - kl"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Frontend

```powershell
cd ai-repository-agent
npm install
```

## Running the Application

### Start Backend

From `c:\Desktop\hackthon - kl` after activating the virtual environment:

```powershell
uvicorn backend.app:app --reload
```

The backend will be available at `http://127.0.0.1:8000`.

### Start Frontend

From `c:\Desktop\hackthon - kl\ai-repository-agent`:

```powershell
npm run dev
```

Open the local Vite URL shown in the terminal to access the dashboard.

## Repository Structure

- `ai-repository-agent/agents/`: top-level Python agents and AI orchestration logic
- `ai-repository-agent/backend/`: API server, routers, analysis engines, collaboration logic
- `ai-repository-agent/backend/api/`: API endpoints and route definitions
- `ai-repository-agent/backend/analysis/`: analysis engines and intelligence pipelines
- `ai-repository-agent/backend/collaboration/`: consensus, aggregation, and risk fusion modules
- `ai-repository-agent/backend/comparison/`: repository comparison engine
- `ai-repository-agent/backend/dashboard/`: DevOps/dashboard engine components
- `ai-repository-agent/backend/intelligence/`: metrics, reputation, and health scoring
- `ai-repository-agent/backend/security/`: security agents and tests
- `ai-repository-agent/src/`: React app entrypoint, components, and UI logic
- `ai-repository-agent/workspace/`: generated intelligence, knowledge, and logs

## Helpful Notes

- The backend is configured with FastAPI and CORS middleware matching any origin.
- The frontend uses React Router for navigation and Recharts / Three.js for visualizations.
- There is also a backend-specific setup guide at `ai-repository-agent/backend/README.md`.

## Common Commands

From the root:

- `python -m venv .venv`
- `.venv\Scripts\Activate.ps1`
- `pip install -r requirements.txt`
- `uvicorn backend.app:app --reload`

From `ai-repository-agent`:

- `npm install`
- `npm run dev`
- `npm run build`

## Contribution Guidelines

1. Use the existing module layout when adding new analysis or collaboration code.
2. Keep backend API routes in `backend/api/`.
3. Keep frontend pages in `src/components/`.
4. Document new behavior in code comments and update this README if the workflow changes.

## License

Add your license file or license statement here if applicable.
