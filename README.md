# Support Ticket Triage: FDE Training Project

## Business Case

Enterprise support and IT operations teams receive high volumes of incidents with inconsistent descriptions, incomplete routing, and uneven urgency assessment. This project demonstrates how a Forward Deployed Engineering workflow can turn messy ITSM records into structured, reviewable operational decisions.

The business objective is to reduce triage latency, improve routing consistency, identify high-priority incidents faster, and create an auditable foundation for human-in-the-loop automation.

## Architecture

The project uses a realistic 300-row ServiceNow-style synthetic incident dataset. Records include incident number, company, caller, short description, description, category, subcategory, impact, urgency, priority, assignment group, service, configuration item, location, and channel.

The system has seven layers:

1. **Data Generation Layer** — `generate_incidents.py` creates synthetic ITSM incident records and expected evaluation labels.
2. **Rules-Based Triage Layer** — `main.py` applies deterministic classification, urgency, confidence, owner routing, and human-review logic.
3. **LLM Triage Layer** — `llm_triage.py` uses structured LLM output with Pydantic to classify incidents, assign urgency, recommend owners, summarize issues, and suggest next actions.
4. **Evaluation Layer** — `evaluate.py` and `evaluate_llm.py` compare classifier outputs against expected labels.
5. **Comparison and Hybrid Layer** — `compare_triage.py` compares rules vs. LLM performance and recommends a hybrid operating model.
6. **Review Workbench Layer** — `app.py` provides a Streamlit Triage Workbench for reviewing human-review candidates, inspecting recommendations, approving or overriding decisions, and exporting reviewed results.
7. **Service and Persistence Layer** — `api.py` exposes typed FastAPI endpoints, while `db.py` stores incidents, system predictions, and human review decisions in SQLite.

## Key Design Decision

The project intentionally compares deterministic rules against LLM-based triage instead of assuming the LLM should replace the baseline. The measured result supports a hybrid architecture: use the LLM for semantic category and owner recommendation, use deterministic rules for urgency guardrails, and send disagreements, low-confidence items, and Critical incidents to human review.

This reflects a realistic enterprise AI pattern: LLMs are valuable for interpretation and summarization, while rules remain better for enforceable business policy.

## Current System Capabilities

The system can generate realistic ITSM data, ingest GitHub-hosted CSV records, run rules-based triage, run structured LLM triage, evaluate outputs against expected labels, compare rules and LLM performance, produce hybrid recommendations, support human review in Streamlit, expose triage through FastAPI, and persist system and human decisions in SQLite.

## Capabilities Demonstrated

- Synthetic enterprise data generation
- ServiceNow-style incident schema design
- GitHub-hosted CSV ingestion
- Rules-based routing and urgency guardrails
- LLM structured output using Pydantic
- Prompt tuning and failure analysis
- Rules vs. LLM evaluation and hybrid recommendation design
- Human-in-the-loop Streamlit review workflow
- FastAPI service layer with typed request/response schemas
- SQLite persistence for incidents, predictions, and review decisions
- Audit trail separating system recommendations from human-approved outcomes
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
- **Lesson 7:** SQLite persistence for source incidents, API triage predictions, and Streamlit review decisions.

## Data and Evaluation

The dataset is synthetic and designed for training. It is not real customer data. Expected labels act as generated ground truth for measuring category, urgency, and owner accuracy. This allows the project to demonstrate evaluation discipline while avoiding sensitive production data.

## Known Limitations

The system is not production deployed, the API has no authentication, the database is local SQLite, and there is no real ServiceNow connector yet. LLM latency, token usage, and cost are not yet tracked. Human review decisions persist locally but are not yet connected to a multi-user workflow or enterprise identity system.

## Future Improvements

Planned improvements include observability and run logging, prompt/version tracking, API authentication, mock ServiceNow integration, Slack or email escalation for critical incidents, LangSmith tracing, cloud deployment, MCP tool wrapping for agent-based triage, and migration from SQLite to Postgres or Supabase for shared persistence.