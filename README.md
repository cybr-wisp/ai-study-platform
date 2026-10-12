# AI Study Platform

An AI-powered adaptive learning platform designed for university students.

> Project status: Initial architecture and repository scaffolding.

## Vision

Transform university course materials into personalized,
interactive learning experiences.

## Core Features

- AI-generated study kits
- Smart Study and active recall
- Flashcards and spaced repetition
- Practice exams
- Personalized study guides
- Course material ingestion
- Learning progress analytics
- Adaptive question selection

## Technology Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js, React, TypeScript |
| Backend | Python, Django, Django REST Framework |
| Database | PostgreSQL, pgvector |
| Cache and Jobs | Redis, Celery |
| AI | LLMs, RAG, Embeddings |
| Infrastructure | Docker, Cloud Hosting |
| Analytics | PostHog |
| CI/CD | GitHub Actions |

## Repository Structure

    apps/       Student application and marketing website
    services/   Django REST API and background workers
    packages/   Shared frontend libraries and contracts
    ml/         Adaptive learning and model evaluation
    infra/      Deployment and infrastructure
    tests/      End-to-end and performance tests
    docs/       Architecture, product, and growth
    scripts/    Development utilities

## Product Roadmap

### Phase 1: MVP
- [ ] User authentication
- [ ] Document uploads
- [ ] AI study-kit generation
- [ ] Flashcards
- [ ] Smart Study
- [ ] Practice exams

### Phase 2: Personalization
- [ ] Spaced repetition
- [ ] Mastery estimation
- [ ] Personalized study schedules
- [ ] Progress dashboard

### Phase 3: Launch and Growth
- [ ] University beta testing
- [ ] Campus marketing
- [ ] Student referrals
- [ ] Subscription plans

## Development

This repository currently contains the planned directory structure.
The application and services are not implemented yet.

See CONTRIBUTING.md for team guidelines.

## Security

Never commit API credentials, private study materials,
or student personal information.

## Team

Built collaboratively by student engineers.


## Backend Development Setup (Django)

### Prerequisites

Install the following tools:

- Python 3.11 or newer (recommended: Python 3.12)
- Git
- PostgreSQL (for database-backed development)
- Redis (for background Celery tasks)

### 1. Navigate to the Backend

From the repository root:

```powershell
cd services/api
```

### 2. Create a Python Virtual Environment

```powershell
py -3.12 -m venv .venv
```

If Python 3.12 is not installed, use an installed supported version:

```powershell
python -m venv .venv
```

### 3. Activate the Virtual Environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If execution is blocked, allow locally created scripts
for the current PowerShell session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Once activated, your terminal displays `(.venv)`.

### 4. Install Python Dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5. Configure Environment Variables

Copy the repository environment template:

```powershell
Copy-Item ../../.env.example .env
```

Fill in your local database credentials and API keys.
Never commit the `.env` file.

### 6. Run Database Migrations

Once Django settings and PostgreSQL are configured:

```powershell
python manage.py migrate
```

### 7. Start the Django Development Server

Once the Django project is initialized:

```powershell
python manage.py runserver
```

The backend will be available at:

http://127.0.0.1:8000/

### 8. Deactivate the Virtual Environment

```powershell
deactivate
```

### Notes

- Each contributor creates their own local `.venv`.
- Virtual environments must not be committed to GitHub.
- Install dependencies from `requirements.txt`.
- When adding a dependency, update `requirements.txt` and
  include the change in your pull request.
- The Django project settings and database configuration
  must be implemented before migrations or the server can run.

