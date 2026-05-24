# Support Ticket Triage CLI

This project reads a CSV of customer support tickets and produces a triaged output file.

## What it does

For each ticket, the tool assigns:

- Category
- Urgency
- Suggested owner
- Short summary
- Recommended next action

## Why this project exists

This is an FDE training project. It demonstrates how to turn messy business text into structured operational decisions.

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate

Install dependencies:
'''bash
pip install -r requirements.txt

Run the app:
'''bash
python main.py

## Input

tickets.csv

## Output

triaged_tickets.csv

## Future Improvements

* Add LLM-based summarization (Complete)
* Add confidence scoring (Complete)
* Add Streamlit UI
* Add ticket history
* Add Slack notifications
* Add LangSmith tracing
* Convert the classifier into an MCP tool

## Lesson 3: LLM-Based Structured Triage

This project includes an optional LLM-based triage workflow. We created two files:

* llm_triage.py
* evaluate_llm.py

This moves the scenario away from hard-coded word determination for evaluating and recommendating next best action for the tickets, to a more flexible LLM determinate that returns structured outputs using pydantic.

