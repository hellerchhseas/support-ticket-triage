import argparse
import os
from typing import Literal

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field


# Load environment variables from a local .env file.
# This lets us keep secrets, such as OPENAI_API_KEY, out of source code.
load_dotenv()


# Local input file. This is useful for offline development.
LOCAL_INPUT_FILE = "data/incidents.csv"

# Remote GitHub-hosted CSV. This simulates pulling incident data from an external source.
REMOTE_INPUT_FILE = (
    "https://raw.githubusercontent.com/hellerchhseas/"
    "support-ticket-triage/refs/heads/main/data/incidents.csv"
)

# Choose which source the LLM triage workflow should use.
# For Lesson 3, we are intentionally using the remote GitHub-hosted dataset.
INPUT_FILE = REMOTE_INPUT_FILE

# Output file for LLM-generated triage results.
OUTPUT_FILE = "data/llm_triaged_incidents.csv"


# These are the only category values the LLM is allowed to return.
# Literal types help Pydantic and OpenAI Structured Outputs enforce consistency.
TriageCategory = Literal[
    "Billing",
    "Account Access",
    "Security / Compliance",
    "Product Question",
    "Technical Issue",
    "Other",
]


# These are the only urgency values the LLM is allowed to return.
TriageUrgency = Literal[
    "Low",
    "Medium",
    "High",
    "Critical",
]


# These are the only owner groups the LLM is allowed to return.
RecommendedOwner = Literal[
    "Finance Operations",
    "Service Desk",
    "Security Operations",
    "Customer Success",
    "Application Engineering",
]


class LLMTriageResult(BaseModel):
    """
    This class defines the exact structured output we want from the model.

    OpenAI Structured Outputs can use this Pydantic model as the schema.
    The model response is parsed into this object instead of free-form text.
    """

    triage_category: TriageCategory = Field(
        description="The best operational category for the incident."
    )
    triage_urgency: TriageUrgency = Field(
        description="The operational urgency inferred from the incident."
    )
    recommended_owner: RecommendedOwner = Field(
        description="The team that should own the incident."
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="A practical confidence score from 0.0 to 1.0.",
    )
    summary: str = Field(
        description="One concise sentence summarizing the incident."
    )
    next_action: str = Field(
        description="The next operational action the team should take."
    )
    reasoning_summary: str = Field(
        description="A short explanation of the evidence used for triage. Do not include hidden chain-of-thought."
    )


def build_incident_prompt(row: pd.Series) -> str:
    """
    Build the user prompt for one incident.

    We include the fields an analyst would need to triage the record.
    The LLM should infer triage outputs from this incident context.
    """

    return f"""
Incident Number: {row['number']}
Company: {row['company']}
Caller: {row['caller']}
Short Description: {row['short_description']}
Description: {row['description']}
Source Category: {row['category']}
Source Subcategory: {row['subcategory']}
Source Impact: {row['impact']}
Source Urgency: {row['urgency']}
Source Priority: {row['priority']}
Current Assignment Group: {row['assignment_group']}
Service: {row['service']}
Configuration Item: {row['configuration_item']}
Channel: {row['channel']}
Location: {row['location']}
"""


def triage_incident_with_llm(client: OpenAI, model: str, row: pd.Series) -> LLMTriageResult:
    """
    Send one incident to the LLM and return a structured triage result.

    The response_format parameter tells the SDK to parse the model response
    directly into the LLMTriageResult Pydantic object.
    """

    # This prompt defines the triage policy the LLM must follow.
    # The important change in Lesson 4.5 is that urgency is no longer described
    # vaguely. We give the model a stricter business-policy rubric and examples.
    system_prompt = """
    You are an expert ITSM incident triage analyst.

    Your job is to classify enterprise support incidents into structured operational triage fields.

    Classify each incident into exactly one triage category:
    - Billing
    - Account Access
    - Security / Compliance
    - Product Question
    - Technical Issue
    - Other

    Choose exactly one recommended owner:
    - Finance Operations
    - Service Desk
    - Security Operations
    - Customer Success
    - Application Engineering

    Category policy:
    - Billing: invoices, refunds, payment methods, renewal amounts, billing address, duplicate charges, seats billed, procurement contacts for invoices.
    - Account Access: login failures, password reset problems, locked-out users, inability to access admin portal or workspace.
    - Security / Compliance: SOC 2, ISO 27001, encryption, audit logs, access logs, security controls, penetration tests, compliance documentation.
    - Product Question: product capabilities, APIs, SAML, SCIM, webhooks, retry behavior, sandbox environments, rate limits, pricing tiers, configuration questions.
    - Technical Issue: production failures, integrations not processing, API errors, dashboards unavailable, duplicate records, workflow failures, system defects.
    - Other: vague or general requests that do not specify a product, billing, security, access, or technical issue.

    Urgency policy:
    Use this policy strictly. Do not rely on generic intuition.

    Critical:
    - Production outage or production processing failure.
    - Executive-visible service disruption.
    - Payroll cutoff, financial close cutoff, or other time-sensitive business cutoff.
    - Broad service impact affecting a team, region, or major business workflow.
    - Dashboard unavailable for executive users.
    - Production integration stopped processing records.

    High:
    - Duplicate records being created by a workflow.
    - API endpoint returning 500 errors.
    - Password reset email not received.
    - Customer charged twice or requesting refund for duplicate charge.
    - User cannot access an admin portal.
    - Important access issue blocking a work task, even if not a broad outage.
    - Repeated failures or operational degradation requiring prompt action.

    Medium:
    - One user locked out, but other users can work.
    - Security/compliance documentation request.
    - SOC 2, encryption, audit logs, access logs, or ISO 27001 requests.
    - Normal billing correction, invoice review, or billing address update.
    - Product capability question.
    - Webhook retry, SAML, SCIM, API, rate limit, or integration capability question.
    - General operational issue that does not indicate outage or severe business impact.

    Low:
    - General documentation request without a specific product area.
    - Pricing tier explanation.
    - Informational question with no operational impact.
    - Non-urgent how-to or learning request.

    Source field interpretation:
    - Source Impact, Source Urgency, and Source Priority are useful evidence.
    - If Source Urgency is "1 - High", strongly consider High or Critical unless the description clearly indicates an informational request.
    - If Source Priority is "1 - Critical", strongly consider Critical.
    - If Source Priority is "2 - High", strongly consider High.
    - If Source Priority is "5 - Planning", consider Low only for purely informational requests; otherwise Medium may be more appropriate.

    Examples:
    - Short Description: "Scheduled workflow creating duplicate records"
    Correct urgency: High
    Reason: duplicate records create downstream operational and data-quality risk.

    - Short Description: "One user locked out"
    Correct urgency: Medium
    Reason: a single-user lockout matters, but it is not a broad outage.

    - Short Description: "Password reset email not received"
    Correct urgency: High
    Reason: password recovery failure blocks access restoration.

    - Short Description: "Customer was charged twice"
    Correct urgency: High
    Reason: duplicate charge and refund issues require prompt financial correction.

    - Short Description: "Webhook retry behavior question"
    Correct urgency: Medium
    Reason: this is a specific technical product capability question, not merely general curiosity.

    - Short Description: "Billing address needs correction"
    Correct urgency: Medium
    Reason: billing account maintenance should be handled as normal work, not treated as low-priority general information.

    - Short Description: "General request for documentation"
    Correct category: Other
    Correct urgency: Low
    Correct owner: Service Desk
    Reason: no specific product, security, billing, access, or technical subject was provided.

    Return only the structured output required by the schema.
    """

    completion = client.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": build_incident_prompt(row)},
        ],
        response_format=LLMTriageResult,
    )

    return completion.choices[0].message.parsed


def run_llm_triage(limit: int) -> pd.DataFrame:
    """
    Run LLM triage over a limited number of incidents.

    We start with a small limit to keep cost low and make debugging easier.
    """

    # Read the realistic ITSM incident dataset.
    # INPUT_FILE can be either a local file path or a remote GitHub raw CSV URL.
    print(f"Reading incidents from: {INPUT_FILE}")
    incidents = pd.read_csv(INPUT_FILE)

    # Limit the number of rows for the first test run.
    incidents_to_process = incidents.head(limit)

    # Read model name from .env, with a safe default.
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Create the OpenAI client. The SDK reads OPENAI_API_KEY from the environment.
    client = OpenAI()

    output_rows = []

    # Process incidents one at a time.
    for _, row in incidents_to_process.iterrows():
        print(f"Triaging {row['number']}...")

        # Call the LLM and get a structured result.
        result = triage_incident_with_llm(client, model, row)

        # Preserve source fields and append LLM-generated fields.
        output_rows.append({
            "number": row["number"],
            "company": row["company"],
            "short_description": row["short_description"],
            "description": row["description"],
            "source_category": row["category"],
            "source_subcategory": row["subcategory"],
            "source_impact": row["impact"],
            "source_urgency": row["urgency"],
            "source_priority": row["priority"],
            "source_assignment_group": row["assignment_group"],
            "llm_triage_category": result.triage_category,
            "llm_triage_urgency": result.triage_urgency,
            "llm_recommended_owner": result.recommended_owner,
            "llm_confidence": result.confidence,
            "llm_summary": result.summary,
            "llm_next_action": result.next_action,
            "llm_reasoning_summary": result.reasoning_summary,
        })

    return pd.DataFrame(output_rows)


def main():
    """
    Command-line entry point for LLM triage.
    """

    # argparse lets us run different row limits from the terminal.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of incidents to triage with the LLM.",
    )
    args = parser.parse_args()

    # Run the LLM triage workflow.
    results = run_llm_triage(limit=args.limit)

    # Write the output to CSV.
    results.to_csv(OUTPUT_FILE, index=False)

    # Print a compact terminal summary.
    display_columns = [
        "number",
        "company",
        "llm_triage_urgency",
        "llm_triage_category",
        "llm_recommended_owner",
        "llm_confidence",
        "llm_summary",
    ]
    print(results[display_columns].to_string(index=False))

    print(f"\nWrote LLM triage results to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()