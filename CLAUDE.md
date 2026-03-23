# CLAUDE.md

## Purpose

This repository implements an end-to-end data pipeline using the CityBikes API.
The system must support both local and cloud execution modes.

## Core Principles

* ALWAYS implement in small, testable steps
* NEVER move forward unless:

  * Code runs
  * Tests pass
  * Output is correct
* Keep everything minimal and clean
* Prefer clarity over cleverness

## Development Workflow

For each task:

1. Read docs in `/docs`
2. Implement minimal version
3. Write tests
4. Validate
5. Then proceed

## Phase Order (STRICT)

1. Project Setup
2. Ingestion
3. Storage
4. dbt
5. Airflow
6. Cloud (Terraform)
7. CI/CD
8. Dashboard

DO NOT SKIP PHASES.

## Environment Rules

* Use Python 3.12
* Use virtual environment (`venv`)
* Use `pyproject.toml` for dependency management
* NEVER install packages globally

## Git Rules

* Initialize git repo immediately
* Commit after each completed step
* Use clear commit messages

## Data Rules

* Append-only ingestion
* Always include:

  * ingestion_timestamp
  * city

## API Rules

* Handle missing fields
* Implement retries (3x, exponential backoff)

## Stop Conditions

STOP if:

* Tests fail
* Data is invalid
* Any step breaks

## Output Expectations

* Clean code
* Passing tests
* Clear logs
* Small commits
