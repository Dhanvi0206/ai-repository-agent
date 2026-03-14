# Phase 2 Backend Architecture

## Standardized Agent Response

Each AI agent must return the same JSON structure so the orchestrator can merge results safely and consistently.

```json
{
  "agent_name": "security_agent",
  "issues": [
    {
      "file_path": "config.py",
      "line_number": 12,
      "issue_type": "Hardcoded Secret",
      "severity": "high",
      "description": "Hardcoded API key detected",
      "recommendation": "Use environment variables instead",
      "confidence_score": 0.92
    }
  ]
}
```

## Architecture Components

- Frontend Dashboard: collects repository URLs and displays health, findings, and reports.
- Backend API (FastAPI): receives requests, validates input, and exposes analysis endpoints.
- Repository Fetcher: clones repositories or prepares metadata for analysis jobs.
- File Scanner: enumerates files, filters unsupported content, and prepares agent-ready file payloads.
- Orchestrator Agent: coordinates file scanning, invokes agents, and manages execution flow.
- AI Agent Layer: specialized agents analyze the same repository from different perspectives.
- Result Aggregator: merges standardized outputs into one combined analysis object.
- Health Score Engine: converts findings into a simple quality or risk score.
- Reporting Engine: transforms aggregated results into dashboard summaries and downloadable reports.

## Pipeline Flow

1. User enters a GitHub repository URL in the frontend dashboard.
2. FastAPI receives the request and validates the payload.
3. Repository Fetcher prepares the repository for local analysis.
4. File Scanner collects analyzable files and metadata.
5. Orchestrator Agent sends the scanned files to each AI agent.
6. Agents return standardized JSON responses.
7. Result Aggregator combines all agent findings into one response.
8. Health Score Engine computes a repository score from the aggregated findings.
9. Reporting Engine prepares dashboard-friendly summaries.
10. Frontend Dashboard displays repository analysis, risks, and recommendations.

## ASCII Diagram

```text
User
  |
  v
Frontend Dashboard
  |
  v
FastAPI Backend
  |
  v
Repository Fetcher
  |
  v
File Scanner
  |
  v
Orchestrator Agent
  |
  v
+----------------------------------+
| Security Agent                   |
| Code Review Agent                |
| Dependency Vulnerability Agent   |
| Documentation Agent              |
| Code Quality Agent               |
| Learning Agent                   |
| Contribution Intelligence Agent  |
| Reporting Agent                  |
+----------------------------------+
  |
  v
Result Aggregator
  |
  v
Repository Health Scoring
  |
  v
Reporting Engine
  |
  v
Frontend Dashboard
```

## Why Standardized Responses Matter

- They let the orchestrator treat every agent uniformly.
- They reduce custom parsing logic and backend bugs.
- They make aggregation, scoring, and dashboard rendering straightforward.
- They simplify adding new agents later without changing core orchestration logic.
- They improve logging, testing, and schema validation across the system.
