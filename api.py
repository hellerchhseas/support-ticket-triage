import os
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI
from openai import OpenAI
from pydantic import BaseModel, Field
from db import save_triage_prediction

from llm_triage import LLMTriageResult, triage_incident_with_llm
from main import classify_ticket, recommend_next_action, requires_human_review


# ------------------------------------------------------------
# Environment setup
# ------------------------------------------------------------
# Load environment variables from .env so the API can use OPENAI_API_KEY
# and OPENAI_MODEL without hard-coding secrets into source code.
load_dotenv()


# ------------------------------------------------------------
# FastAPI application
# ------------------------------------------------------------
# This object is the API application. Uvicorn will serve this app locally.
app = FastAPI(
    title="Support Ticket Triage API",
    description="API service for rules-based, LLM-based, and hybrid incident triage.",
    version="0.1.0",
)


# ------------------------------------------------------------
# Shared schema values
# ------------------------------------------------------------
# Literal types constrain API inputs/outputs to known business values.
# This makes responses predictable for downstream systems.
TriageCategory = Literal[
    "Billing",
    "Account Access",
    "Security / Compliance",
    "Product Question",
    "Technical Issue",
    "Other",
]

TriageUrgency = Literal[
    "Low",
    "Medium",
    "High",
    "Critical",
]

RecommendedOwner = Literal[
    "Finance Operations",
    "Service Desk",
    "Security Operations",
    "Customer Success",
    "Application Engineering",
]


class IncidentRequest(BaseModel):
    """
    Input schema for one incident.

    This represents the minimum fields an external system would send to the API.
    The schema is intentionally similar to the ServiceNow-style incident dataset.
    """

    number: str = Field(description="Incident number, such as INC0001234.")
    company: str = Field(description="Customer or company associated with the incident.")
    caller: str = Field(description="Person who reported the incident.")
    short_description: str = Field(description="Brief incident summary.")
    description: str = Field(description="Full incident description.")
    category: str = Field(description="Source-system category.")
    subcategory: str = Field(description="Source-system subcategory.")
    impact: str = Field(description="Source-system impact value.")
    urgency: str = Field(description="Source-system urgency value.")
    priority: str = Field(description="Source-system priority value.")
    assignment_group: str = Field(description="Current source-system assignment group.")
    service: str = Field(description="Affected business or technical service.")
    configuration_item: str = Field(description="Affected configuration item.")
    channel: str = Field(description="Intake channel, such as Portal, Email, Phone, or Chat.")
    location: str = Field(description="User or service location.")


class TriageResponse(BaseModel):
    """
    Standard output schema for all triage approaches.

    Rules, LLM, and hybrid endpoints all return this shape so downstream
    systems can consume responses consistently.
    """

    number: str
    triage_mode: Literal["rules", "llm", "hybrid"]
    triage_category: TriageCategory
    triage_urgency: TriageUrgency
    recommended_owner: RecommendedOwner
    confidence: float
    requires_human_review: bool
    summary: str
    next_action: str
    reasoning_summary: str


class HealthResponse(BaseModel):
    """
    Response schema for the health check endpoint.
    """

    status: str
    service: str
    version: str


def build_classification_text(incident: IncidentRequest) -> str:
    """
    Combine key incident fields into one text string.

    The existing rules classifier expects text. This function adapts the API
    request schema into the same text format used by the rules pipeline.
    """

    return f"{incident.short_description} {incident.description}"


def incident_to_series_dict(incident: IncidentRequest) -> dict:
    """
    Convert the API request object into a dictionary compatible with llm_triage.py.

    The existing LLM function expects a pandas-like row with specific keys.
    This adapter lets the API reuse that function without rewriting LLM logic.
    """

    return {
        "number": incident.number,
        "company": incident.company,
        "caller": incident.caller,
        "short_description": incident.short_description,
        "description": incident.description,
        "category": incident.category,
        "subcategory": incident.subcategory,
        "impact": incident.impact,
        "urgency": incident.urgency,
        "priority": incident.priority,
        "assignment_group": incident.assignment_group,
        "service": incident.service,
        "configuration_item": incident.configuration_item,
        "channel": incident.channel,
        "location": incident.location,
    }


def run_rules_triage(incident: IncidentRequest) -> TriageResponse:
    """
    Run the deterministic rules-based triage path.

    This endpoint is fast, cheap, explainable, and useful as a production
    guardrail or fallback when the LLM path is unavailable.
    """

    classification_text = build_classification_text(incident)

    # Reuse the existing rules classifier from main.py.
    result = classify_ticket(classification_text)

    next_action = recommend_next_action(
        result["triage_category"],
        result["triage_urgency"],
        result["recommended_owner"],
        result["confidence"],
    )

    review_flag = requires_human_review(
        result["confidence"],
        result["triage_urgency"],
    )

    response = TriageResponse(
        number=incident.number,
        triage_mode="rules",
        triage_category=result["triage_category"],
        triage_urgency=result["triage_urgency"],
        recommended_owner=result["recommended_owner"],
        confidence=result["confidence"],
        requires_human_review=review_flag,
        summary=incident.short_description,
        next_action=next_action,
        reasoning_summary=f"Matched rules: {result['matched_rules']}",
    )

    # Save the API prediction for auditability.
    save_triage_prediction(
        incident_number=response.number,
        triage_mode=response.triage_mode,
        triage_category=response.triage_category,
        triage_urgency=response.triage_urgency,
        recommended_owner=response.recommended_owner,
        confidence=response.confidence,
        requires_human_review=response.requires_human_review,
        summary=response.summary,
        next_action=response.next_action,
        reasoning_summary=response.reasoning_summary,
    )

    return response


def run_llm_triage(incident: IncidentRequest) -> TriageResponse:
    """
    Run the LLM-based triage path.

    This uses the existing structured-output LLM function from llm_triage.py.
    """

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI()

    # The LLM helper expects a row-like object. A pandas Series works well.
    # We import pandas locally to keep the API module's top-level imports simpler.
    import pandas as pd

    incident_row = pd.Series(incident_to_series_dict(incident))

    result: LLMTriageResult = triage_incident_with_llm(
        client=client,
        model=model,
        row=incident_row,
    )

    review_flag = result.confidence < 0.70 or result.triage_urgency == "Critical"

    response = TriageResponse(
        number=incident.number,
        triage_mode="rules",
        triage_category=result["triage_category"],
        triage_urgency=result["triage_urgency"],
        recommended_owner=result["recommended_owner"],
        confidence=result["confidence"],
        requires_human_review=review_flag,
        summary=incident.short_description,
        next_action=next_action,
        reasoning_summary=f"Matched rules: {result['matched_rules']}",
    )

    # Save the API prediction for auditability.
    save_triage_prediction(
        incident_number=response.number,
        triage_mode=response.triage_mode,
        triage_category=response.triage_category,
        triage_urgency=response.triage_urgency,
        recommended_owner=response.recommended_owner,
        confidence=response.confidence,
        requires_human_review=response.requires_human_review,
        summary=response.summary,
        next_action=response.next_action,
        reasoning_summary=response.reasoning_summary,
    )

    return response


def run_hybrid_triage(incident: IncidentRequest) -> TriageResponse:
    """
    Run the hybrid triage path.

    Lesson 5 showed that the strongest design was:
    - LLM for category
    - rules for urgency
    - LLM for owner

    This function implements that measured operating model.
    """

    rules_result = run_rules_triage(incident)
    llm_result = run_llm_triage(incident)

    # Hybrid strategy based on previous evaluation:
    # semantic fields from LLM, policy-driven urgency from rules.
    hybrid_category = llm_result.triage_category
    hybrid_urgency = rules_result.triage_urgency
    hybrid_owner = llm_result.recommended_owner

    # Human review is recommended for disagreements, low confidence, or critical urgency.
    has_disagreement = (
        rules_result.triage_category != llm_result.triage_category
        or rules_result.triage_urgency != llm_result.triage_urgency
        or rules_result.recommended_owner != llm_result.recommended_owner
    )

    hybrid_confidence = min(rules_result.confidence, llm_result.confidence)

    review_flag = (
        has_disagreement
        or hybrid_confidence < 0.70
        or hybrid_urgency == "Critical"
    )

    next_action = recommend_next_action(
        hybrid_category,
        hybrid_urgency,
        hybrid_owner,
        hybrid_confidence,
    )

    response = TriageResponse(
        number=incident.number,
        triage_mode="rules",
        triage_category=result["triage_category"],
        triage_urgency=result["triage_urgency"],
        recommended_owner=result["recommended_owner"],
        confidence=result["confidence"],
        requires_human_review=review_flag,
        summary=incident.short_description,
        next_action=next_action,
        reasoning_summary=f"Matched rules: {result['matched_rules']}",
    )

    # Save the API prediction for auditability.
    save_triage_prediction(
        incident_number=response.number,
        triage_mode=response.triage_mode,
        triage_category=response.triage_category,
        triage_urgency=response.triage_urgency,
        recommended_owner=response.recommended_owner,
        confidence=response.confidence,
        requires_human_review=response.requires_human_review,
        summary=response.summary,
        next_action=response.next_action,
        reasoning_summary=response.reasoning_summary,
    )

    return response


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Health check endpoint.

    External systems can call this to verify the service is running.
    """

    return HealthResponse(
        status="ok",
        service="support-ticket-triage-api",
        version="0.1.0",
    )


@app.post("/triage/rules", response_model=TriageResponse)
def triage_rules(incident: IncidentRequest) -> TriageResponse:
    """
    Run deterministic rules-based triage for one incident.
    """

    return run_rules_triage(incident)


@app.post("/triage/llm", response_model=TriageResponse)
def triage_llm(incident: IncidentRequest) -> TriageResponse:
    """
    Run LLM-based structured triage for one incident.
    """

    return run_llm_triage(incident)


@app.post("/triage/hybrid", response_model=TriageResponse)
def triage_hybrid(incident: IncidentRequest) -> TriageResponse:
    """
    Run hybrid triage for one incident.

    This is the recommended production-style endpoint from Lesson 5.
    """

    return run_hybrid_triage(incident)