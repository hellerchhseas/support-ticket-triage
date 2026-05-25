import pandas as pd


# These constants define the input and output files used by the application.
# The input now points to the more realistic ITSM incident dataset.
# Local source file used for normal development
LOCAL_INPUT_FILE = "data/incidents.csv"

# Remote GitHub-hosted source file used to simulate pulling from an external data source.
REMOTE_INPUT_FILE = "https://raw.githubusercontent.com/hellerchhseas/support-ticket-triage/refs/heads/main/data/incidents.csv"

# Choose which input source the app should use.
INPUT_FILE = REMOTE_INPUT_FILE
OUTPUT_FILE = "data/triaged_incidents.csv"


# CATEGORY_RULES is the rules engine for our triage classifier.
# Each category has:
# - an owner team
# - strong keywords that are highly predictive
# - weak keywords that provide weaker supporting evidence
CATEGORY_RULES = {
    "Billing": {
        "owner": "Finance Operations",
        "strong_keywords": [
            "invoice",
            "charged twice",
            "refund",
            "renewal amount",
            "billed",
            "billing address",
            "credit card",
            "payment method",
            "billing profile",
        ],
        "weak_keywords": [
            "renewal",
            "subscription",
            "pricing",
            "seats",
            "line items",
        ],
    },
    "Account Access": {
        "owner": "Service Desk",
        "strong_keywords": [
            "cannot access",
            "unable to log in",
            "forgot their password",
            "password reset",
            "reset my password",
            "locked out",
            "admin portal",
        ],
        "weak_keywords": [
            "login",
            "password",
            "user",
            "workspace",
            "account",
            "access",
        ],
    },
    "Security / Compliance": {
        "owner": "Security Operations",
        "strong_keywords": [
            "soc 2",
            "penetration test",
            "data retention",
            "encryption policy",
            "encrypted at rest",
            "access logs",
            "audit team",
        ],
        "weak_keywords": [
            "security",
            "controls",
            "compliance",
            "audit",
            "procurement",
            "reviewer",
        ],
    },
    "Product Question": {
        "owner": "Customer Success",
        "strong_keywords": [
            "saml",
            "scim",
            "webhook retries",
            "dead-letter queues",
            "pricing tiers",
            "user pricing",
            "enterprise pricing",
        ],
        "weak_keywords": [
            "api",
            "documentation",
            "explanation",
            "explain",
            "configure",
            "support",
            "whether",
            "asks",
            "wants to know",
        ],
    },
    "Technical Issue": {
        "owner": "Application Engineering",
        "strong_keywords": [
            "production",
            "stopped processing",
            "stopped syncing",
            "500 errors",
            "unavailable",
            "duplicate records",
            "workflow",
            "api endpoint",
            "integration",
        ],
        "weak_keywords": [
            "delayed",
            "sync",
            "records",
            "release",
            "downstream",
            "dashboard",
        ],
    },
}


def build_classification_text(row: pd.Series) -> str:
    """
    Combine the most useful text fields into one string for classification.

    Real ticketing systems usually split information across fields.
    For triage, short_description and description are usually the most useful.
    """

    return f"{row['short_description']} {row['description']}"


def classify_ticket(text: str) -> dict:
    """
    Classify a ticket using transparent keyword rules.

    Returns:
    - triage category
    - owner group
    - confidence score
    - matched rules

    This makes the decision inspectable and easier to debug.
    """

    # Normalize to lowercase for case-insensitive keyword matching.
    text_lower = text.lower()

    # Default values are used if no rules match.
    best_category = "Other"
    best_owner = "Service Desk"
    best_score = 0
    best_matches = []

    # Score each possible category and retain the highest-scoring one.
    for category, rules in CATEGORY_RULES.items():
        score = 0
        matches = []

        # Strong keywords receive higher weight because they are more predictive.
        for keyword in rules["strong_keywords"]:
            if keyword in text_lower:
                score += 3
                matches.append(f"strong:{keyword}")

        # Weak keywords receive lower weight because they are more ambiguous.
        for keyword in rules["weak_keywords"]:
            if keyword in text_lower:
                score += 1
                matches.append(f"weak:{keyword}")

        # Keep the best-scoring category.
        if score > best_score:
            best_score = score
            best_category = category
            best_owner = rules["owner"]
            best_matches = matches

    # Determine urgency separately because urgency is not the same as category.
    urgency_result = determine_urgency(text_lower)

    # Convert rule strength into a simple operational confidence score.
    confidence = calculate_confidence(best_score, urgency_result["score"])

    return {
        "triage_category": best_category,
        "triage_urgency": urgency_result["urgency"],
        "recommended_owner": best_owner,
        "confidence": confidence,
        "matched_rules": "; ".join(best_matches) if best_matches else "no_match",
    }


def determine_urgency(text_lower: str) -> dict:
    """
    Determine urgency from business-impact language.

    This is separate from the source ITSM urgency field because our classifier
    is trying to infer operational urgency from the ticket text.
    """

    # Critical phrases suggest severe production or business impact.
    critical_phrases = [
        "production",
        "stopped processing",
        "unavailable",
        "executives are asking",
        "payroll cutoff",
    ]

    # High phrases suggest meaningful urgency but not necessarily a total outage.
    high_phrases = [
        "500 errors",
        "duplicate records",
        "cannot reset",
        "reset email never arrives",
        "charged twice",
        "cannot access",
    ]

    # Low phrases suggest informational or non-blocking requests.
    low_phrases = [
        "general documentation",
        "pricing tiers",
        "additional user pricing",
        "wants an explanation",
    ]

    # Check most severe signals first.
    for phrase in critical_phrases:
        if phrase in text_lower:
            return {"urgency": "Critical", "score": 3}

    # Then check high-priority signals.
    for phrase in high_phrases:
        if phrase in text_lower:
            return {"urgency": "High", "score": 2}

    # Then check low-priority signals.
    for phrase in low_phrases:
        if phrase in text_lower:
            return {"urgency": "Low", "score": 1}

    # Medium is the default when there is no clear signal.
    return {"urgency": "Medium", "score": 1}


def calculate_confidence(category_score: int, urgency_score: int) -> float:
    """
    Convert rule-match strength into a rough confidence score.

    This is not a statistical probability. It is a practical routing heuristic.
    """

    # Add category evidence and urgency evidence together.
    combined_score = category_score + urgency_score

    # If no category matched, confidence is low.
    if category_score == 0:
        return 0.25

    # Higher score means more rule evidence.
    if combined_score >= 6:
        return 0.95

    if combined_score >= 4:
        return 0.85

    if combined_score >= 3:
        return 0.70

    return 0.55


def requires_human_review(confidence: float, triage_urgency: str) -> bool:
    """
    Decide whether the ticket should be reviewed by a human.

    Low-confidence tickets should be reviewed.
    Critical tickets should also be reviewed because they carry higher risk.
    """

    if confidence < 0.70:
        return True

    if triage_urgency == "Critical":
        return True

    return False


def summarize_incident(row: pd.Series) -> str:
    """
    Create a short summary from the incident fields.

    This is a deterministic baseline. Later, an LLM can generate better summaries.
    """

    return row["short_description"]


def recommend_next_action(category: str, urgency: str, owner: str, confidence: float) -> str:
    """
    Recommend the next operational step based on the triage result.
    """

    # Low-confidence classifications should not be fully automated.
    if confidence < 0.70:
        return "Send to human triage because classifier confidence is low."

    # Critical issues should be escalated quickly.
    if urgency == "Critical":
        return f"Escalate immediately to {owner} and notify the account lead."

    # Category-specific guidance.
    if category == "Billing":
        return "Review invoice, payment, and account billing history."

    if category == "Account Access":
        return "Verify user identity and begin access recovery workflow."

    if category == "Security / Compliance":
        return "Route to security operations with approved documentation workflow."

    if category == "Product Question":
        return "Route to customer success with relevant product documentation."

    if category == "Technical Issue":
        return "Collect logs, reproduction steps, and recent change history."

    return "Review manually and assign to the appropriate team."


def triage_tickets(input_file: str = INPUT_FILE) -> pd.DataFrame:
    """
    Load incidents and return an enriched triage DataFrame.

    This function is reused by both main.py and evaluate.py.
    """

    # Load the ServiceNow-style incident export.
    incidents = pd.read_csv(input_file)

    # This list will hold enriched incident rows.
    triaged_rows = []

    # Process each incident individually.
    for _, row in incidents.iterrows():
        # Combine relevant text fields for classification.
        classification_text = build_classification_text(row)

        # Run the rules-based classifier.
        classification = classify_ticket(classification_text)

        # Build a short deterministic summary.
        summary = summarize_incident(row)

        # Recommend the next operational action.
        next_action = recommend_next_action(
            classification["triage_category"],
            classification["triage_urgency"],
            classification["recommended_owner"],
            classification["confidence"],
        )

        # Build the enriched output row.
        triaged_rows.append({
            "number": row["number"],
            "opened_at": row["opened_at"],
            "company": row["company"],
            "short_description": row["short_description"],
            "description": row["description"],
            "source_category": row["category"],
            "source_subcategory": row["subcategory"],
            "source_impact": row["impact"],
            "source_urgency": row["urgency"],
            "source_priority": row["priority"],
            "source_assignment_group": row["assignment_group"],
            "triage_category": classification["triage_category"],
            "triage_urgency": classification["triage_urgency"],
            "recommended_owner": classification["recommended_owner"],
            "confidence": classification["confidence"],
            "requires_human_review": requires_human_review(
                classification["confidence"],
                classification["triage_urgency"],
            ),
            "matched_rules": classification["matched_rules"],
            "summary": summary,
            "next_action": next_action,
        })

    # Convert enriched rows to a DataFrame.
    return pd.DataFrame(triaged_rows)


def main():
    """
    Run the incident triage workflow from the terminal.
    """

    # Run triage.
    triaged_incidents = triage_tickets(INPUT_FILE)

    # Select a readable subset of columns for terminal display.
    display_columns = [
        "number",
        "company",
        "triage_urgency",
        "triage_category",
        "recommended_owner",
        "confidence",
        "requires_human_review",
        "summary",
    ]

    # Print a terminal-friendly table.
    print(triaged_incidents[display_columns].to_string(index=False))

    # Write full output to CSV.
    triaged_incidents.to_csv(OUTPUT_FILE, index=False)

    print(f"\nWrote triaged incidents to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()