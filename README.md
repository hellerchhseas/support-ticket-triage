# Support Ticket Triage: FDE Training Project

## Business Case

Enterprise support and IT operations teams receive large volumes of incidents with inconsistent descriptions, incomplete routing, and uneven urgency assessment. This project demonstrates how an applied AI / Forward Deployed Engineering workflow can convert messy incident records into structured operational decisions.

The business objective is to reduce triage latency, improve routing consistency, identify high-priority incidents faster, and create a measurable foundation for human-in-the-loop automation.

## Architecture

The project uses a realistic ServiceNow-style incident dataset with 300 synthetic records. Incident records include fields such as incident number, company, caller, short description, description, category, subcategory, impact, urgency, priority, assignment group, service, configuration item, and channel.

The data pipeline has three layers:

1. **Data Generation Layer** — `generate_incidents.py` creates realistic ITSM incident data and expected evaluation labels.
2. **Rules-Based Triage Layer** — `main.py` applies deterministic classification logic, confidence scoring, owner recommendation, and human-review flags.
3. **LLM Triage Layer** — `llm_triage.py` uses structured LLM output to classify incidents, assign urgency, recommend owners, summarize issues, and suggest next actions.

Evaluation scripts compare classifier outputs against expected labels, making the system measurable rather than anecdotal.

## Capabilities Demonstrated

This project demonstrates practical FDE and applied AI skills:

- Synthetic enterprise data generation
- ServiceNow-style incident schema design
- CSV ingestion from both local and GitHub-hosted data sources
- Rules-based classification and routing
- Confidence scoring and human-review logic
- Ground-truth evaluation harnesses
- LLM-based structured output using Pydantic
- Comparison of deterministic and AI-based triage methods
- Safe local secret handling through environment variables
- Git/GitHub workflow using branches, commits, and pull requests
- Prompt tuning and failure analysis to improve urgency classification against expected labels
- Side-by-side rules vs. LLM evaluation with field-level correctness, disagreement analysis, and hybrid routing recommendations
- Human-in-the-loop review workbench for hybrid rules + LLM triage recommendations
- Operational queue design with review reasons, urgency sorting, decision buttons, and exportable review outcomes

## Current State

The project has progressed through four stages:

- **Lesson 1:** Built a rules-based support ticket triage CLI.
- **Lesson 2:** Added confidence scoring and an evaluation harness.
- **Lesson 2.5:** Replaced toy data with a 300-row ServiceNow-style incident dataset.
- **Lesson 3:** Added LLM-based structured incident triage and LLM evaluation.
- **Lesson 4:** Added a Streamlit human-review UI for filtering incidents, inspecting LLM recommendations, applying manual overrides, and exporting reviewed results.
- **Lesson 4.5:** Tuned LLM urgency policy and improved evaluation diagnostics for failure analysis.
- **Lesson 5:** Added a comparison engine showing that the strongest architecture is hybrid: LLM for category and owner, deterministic rules for urgency, with human review for disagreements and high-risk incidents.
- **Lesson 5.5:** Rebuilt the Streamlit app as a Triage Workbench focused on human review candidates, disagreement-based sorting, recommendation inspection, decision buttons, manual overrides, analytics, and export.

## Future Improvements

Planned improvements include:

- Persist reviewer overrides across the full dataset and reload prior review sessions
- Side-by-side rules vs. LLM comparison dashboard
- Manual override workflow for low-confidence incidents
- Remote ingestion from Google Sheets, Supabase, or a mock ServiceNow API
- LangSmith tracing for prompt/version evaluation
- Slack or email notification for critical incidents
- MCP tool wrapper for agent-based incident triage
- Cloud deployment as a lightweight review application
- Streamlit dashboard for visualizing rules vs. LLM performance, hybrid routing, and review priorities
- Persist reviewer decisions across sessions using SQLite