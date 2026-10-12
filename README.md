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

