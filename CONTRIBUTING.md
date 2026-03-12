# Contributing Guide

Thanks for your interest in contributing to Alter.

## Getting Started

1. Fork the repository.
2. Create a feature branch from `main`.
3. Set up a Python environment.
4. Install dependencies.
5. Run the app and validate your changes.

Example setup:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python desktop/main.py
```

## Development Workflow

1. Keep changes focused and small.
2. Use clear commit messages.
3. Update documentation when behavior changes.
4. Ensure the app starts without errors before opening a PR.

## Pull Requests

Please include:
- A concise summary of the problem and fix
- Screenshots or short videos for UI changes
- Manual test notes (what you validated)
- Any migration or breaking-change notes

## Coding Expectations

- Follow existing project structure under `desktop/alter_app/`
- Avoid large unrelated refactors in the same PR
- Prefer readable code over clever code

## Reporting Bugs

Use the bug report template and include:
- OS and Python version
- Reproduction steps
- Expected vs actual behavior
- Logs or traceback, if any

## Feature Requests

Open a feature request with:
- Problem statement
- Proposed solution
- Alternatives considered
