# Support Ticket Triage: FDE Training Project

## Business Case

Enterprise support and IT operations teams receive high volumes of incidents with inconsistent descriptions, incomplete routing, and uneven urgency assessment. This project demonstrates how an applied AI / Forward Deployed Engineering workflow can convert messy ITSM incident records into structured operational decisions.

The business objective is to reduce triage latency, improve routing consistency, identify high-priority incidents faster, and create a measurable foundation for human-in-the-loop automation.

## Architecture

The project uses a realistic 300-row ServiceNow-style synthetic incident dataset. Records include incident number, company, caller, short description, description, category, subcategory, impact, urgency, priority, assignment group, service, configuration item, and channel.

The system includes five layers:

1. **Data Generation Layer** — `generate_incidents.py` creates synthetic ITSM incidents and expected evaluation labels.
2. **Rules-Based Triage Layer** — `main.py` applies deterministic routing, urgency, confidence, and human-review logic.
3. **LLM Triage Layer** — `llm_triage.py` uses structured LLM output with Pydantic to classify incidents, assign urgency, recommend owners, summarize issues, and suggest next actions.
4. **Comparison and Review Layer** — `compare_triage.py` compares rules, LLM, and hybrid recommendations. `app.py` provides a Streamlit Triage Workbench for human review.
5. **API Service Layer** — `api.py` exposes rules, LLM, and hybrid triage through FastAPI endpoints for external system integration.

## Capabilities Demonstrated

- Synthetic enterprise data generation
- ServiceNow-style incident schema design
- GitHub-hosted CSV ingestion
- Rules-based classification and routing
- LLM structured output using Pydantic
- Prompt tuning and failure analysis
- Rules vs. LLM evaluation
- Hybrid recommendation design
- Human-in-the-loop Streamlit review workflow
- FastAPI service layer with typed request/response schemas
- Git/GitHub workflow using branches, commits, and pull requests

## Current State

Completed stages:

- **Lesson 1:** Rules-based support ticket triage CLI.
- **Lesson 2:** Confidence scoring and evaluation harness.
- **Lesson 2.5:** Realistic 300-row ITSM incident dataset.
- **Lesson 3:** LLM-based structured incident triage.
- **Lesson 4:** Streamlit human-review UI.
- **Lesson 4.5:** LLM urgency tuning and improved diagnostics.
- **Lesson 5:** Rules vs. LLM comparison and hybrid recommendation.
- **Lesson 5.5:** Streamlit Triage Workbench redesign.
- **Lesson 6:** FastAPI service layer for rules, LLM, and hybrid triage.

## Future Improvements

Planned improvements include SQLite persistence for reviewer decisions, observability and run logging, API authentication, mock ServiceNow integration, LangSmith tracing, Slack or email escalation, and cloud deployment.