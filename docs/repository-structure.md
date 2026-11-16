# Repository Structure

This document explains the organization of the FakeDeal Buster repository.

## Root Directory

| Directory / File | Purpose |
|---|---|
| `assets/` | Architecture diagrams, screenshots and presentation materials |
| `backend/` | Python FastAPI backend and API endpoints |
| `dataset/` | Dataset source, data dictionary and preprocessing documentation |
| `docs/` | Project planning, technical documentation and reports |
| `frontend/` | React-based user interface |
| `ml/` | Data analysis, preprocessing and machine learning models |
| `tests/` | Unit, integration and application testing |
| `.env.example` | Example environment variable configuration |
| `.gitignore` | Files and folders excluded from Git |
| `CONTRIBUTING.md` | Team contribution and pull request guidelines |
| `README.md` | Main project introduction and setup guide |

## Team Ownership

- Gaurav Das: Project coordination, machine learning and GitHub maintenance.
- Rahul Amin: Backend development.
- Lakhyajyoti Phukan: Data preparation and dataset analysis.
- Saniya Begum: Frontend development.
- Myusha Chakma: Testing and integration coordination.

## GitHub Workflow

1. The central repository is maintained by the team leader.
2. Other members work through their own forks.
3. Members create branches for individual tasks.
4. Members submit pull requests to the central repository.
5. The team leader reviews and merges approved changes.
6. Direct pushes to the central `main` branch are not permitted for team members.

## Important Rules

- Do not upload the full raw dataset to GitHub.
- Never commit passwords, API keys or private credentials.
- Do not commit virtual environments or `node_modules`.
- Keep documentation updated when implementation changes.
- Do not claim a feature or test is complete until it has been verified.
