import pandas as pd


# These constants define the input and output files used by the application.
INPUT_FILE = "tickets.csv"
OUTPUT_FILE = "triaged_tickets.csv"


# CATEGORY_RULES is the core rules engine for the classifier.
# Each category has:
# - an owner team
# - strong keywords that are highly predictive of the category
# - weak keywords that provide weaker evidence
#
CATEGORY_RULES = {
    "Billing": {
        "owner": "Finance",
        "strong_keywords": [
            "invoice",
            "charged twice",
            "refund",
            "renewal amount",
            "billed",
            "billing address",
            "credit card",
            "payment method",
            "procurement contact",
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
        "owner": "Support",
        "strong_keywords": [
            "cannot access",
            "unable to log in",
            "forgot their password",
            "password reset",
            "reset my password",
            "locked out",
            "invite a teammate",
            "adding a new user",
            "add a new user",
        ],
        "weak_keywords": [
            "login",
            "password",
            "user",
            "workspace",
            "account",
        ],
    },
    "Security / Compliance": {
        "owner": "Security",
        "strong_keywords": [
            "soc 2",
            "penetration test",
            "data retention",
            "encryption policy",
            "mfa",
            "iso 27001",
            "encrypted at rest",
            "access logs",
        ],
        "weak_keywords": [
            "security",
            "controls",
            "compliance",
            "audit",
            "procurement process",
            "reviewer",
        ],
    },
    "Product Question": {
        "owner": "Customer Success",
        "strong_keywords": [
            "saml",
            "scim",
            "workday",
            "terraform",
            "webhook retries",
            "dead-letter queues",
            "rate limits",
            "sandbox environment",
            "role-based access control",
            "pricing tiers",
            "user-based pricing",
        ],
        "weak_keywords": [
            "api",
            "documentation",
            "explain",
            "configure",
            "support",
            "integrate",
            "how does",
            "how do i",
        ],
    },
    "Technical Issue": {
        "owner": "Engineering",
        "strong_keywords": [
            "production",
            "failing",
            "stopped syncing",
            "stopped processing",
            "timing out",
            "500 error",
            "system is down",
            "authentication errors",
            "blank page",
            "duplicate records",
            "dashboard is unavailable",
        ],
        "weak_keywords": [
            "slowly",
            "delayed",
            "sync",
            "integration",
            "workflow",
            "records",
            "loads",
            "fails",
        ],
    },
}


def classify_ticket(message: str) -> dict:
    """
    Classify a support ticket using transparent keyword rules.

    The function returns:
    - category
    - urgency
    - owner
    - confidence score
    - matched rules

    This makes the classifier explainable. Instead of only saying
    "this is Billing," the system can show which rules drove the decision.
    """

    # Normalize the message to lowercase so keyword matching is case-insensitive.
    message_lower = message.lower()

    # Default values are used if no category rules match the message.
    best_category = "Other"
    best_owner = "Support"
    best_score = 0
    best_matches = []

    # Loop through each category and calculate a score based on matched keywords.
    for category, rules in CATEGORY_RULES.items():
        score = 0
        matches = []

        # Strong keywords receive more weight because they are more predictive.
        for keyword in rules["strong_keywords"]:
            if keyword in message_lower:
                score += 3
                matches.append(f"strong:{keyword}")

        # Weak keywords receive less weight because they are more ambiguous.
        for keyword in rules["weak_keywords"]:
            if keyword in message_lower:
                score += 1
                matches.append(f"weak:{keyword}")

        # Keep whichever category has the highest score.
        if score > best_score:
            best_score = score
            best_category = category
            best_owner = rules["owner"]
            best_matches = matches

    # Urgency is calculated separately from category.
    # This matters because a Billing issue can be low or high urgency,
    # and a Technical Issue can be medium or critical.
    urgency_result = determine_urgency(message_lower)

    # Confidence is a rough operational score based on rule-match strength.
    confidence = calculate_confidence(best_score, urgency_result["score"])

    return {
        "category": best_category,
        "urgency": urgency_result["urgency"],
        "owner": best_owner,
        "confidence": confidence,
        "matched_rules": "; ".join(best_matches) if best_matches else "no_match",
    }


def determine_urgency(message_lower: str) -> dict:
    """
    Determine urgency from business-impact language.

    This function returns both the urgency label and the score used
    for confidence calculation.
    """

    # Critical phrases usually indicate production impact or severe business disruption.
    critical_phrases = [
        "blocking",
        "production",
        "system is down",
        "all regions",
        "entire support team",
        "stopped processing",
    ]

    # High phrases indicate meaningful urgency but may not be a full outage.
    high_phrases = [
        "today",
        "cannot access",
        "unable to log in",
        "500 error",
        "failed",
        "delayed reporting",
        "blank page",
        "duplicate records",
        "authentication errors",
        "executives are asking",
        "reset email never arrives",
    ]

    # Low phrases usually indicate questions, learning needs, or non-blocking issues.
    low_phrases = [
        "not blocking",
        "explain",
        "confusing",
        "sandbox",
        "invite a teammate",
        "how do i",
        "how does",
    ]

    # Check critical phrases first because they should override lower-priority signals.
    for phrase in critical_phrases:
        if phrase in message_lower:
            return {
                "urgency": "Critical",
                "score": 3,
                "matched_urgency_rule": phrase,
            }

    # Check high-priority phrases after critical phrases.
    for phrase in high_phrases:
        if phrase in message_lower:
            return {
                "urgency": "High",
                "score": 2,
                "matched_urgency_rule": phrase,
            }

    # Check low-priority phrases after higher-priority impact signals.
    for phrase in low_phrases:
        if phrase in message_lower:
            return {
                "urgency": "Low",
                "score": 1,
                "matched_urgency_rule": phrase,
            }

    # Medium is the default when there is no obvious urgent or low-priority signal.
    return {
        "urgency": "Medium",
        "score": 1,
        "matched_urgency_rule": "default_medium",
    }


def calculate_confidence(category_score: int, urgency_score: int) -> float:
    """
    Convert rule-match strength into a rough confidence score.

    This is not a true statistical probability. It is an operational heuristic
    that helps decide whether a ticket can be routed automatically or should
    be reviewed by a human.
    """

    # Combine category and urgency evidence into one simple score.
    combined_score = category_score + urgency_score

    # If no category matched, confidence should be low.
    if category_score == 0:
        return 0.25

    # Higher combined scores mean stronger evidence from the rules.
    if combined_score >= 6:
        return 0.95

    if combined_score >= 4:
        return 0.85

    if combined_score >= 3:
        return 0.70

    # Lowest non-zero confidence when there is only weak evidence.
    return 0.55


def summarize_ticket(message: str) -> str:
    """
    Create a short human-readable summary.

    This deterministic baseline simply truncates long messages.
    Later, an LLM can generate better natural-language summaries.
    """

    # If the message is already short, return it as-is.
    if len(message) <= 90:
        return message

    # Truncate long messages so the terminal output remains readable.
    return message[:87] + "..."


def recommend_next_action(category: str, urgency: str, owner: str, confidence: float) -> str:
    """
    Recommend the next operational action based on category, urgency, and confidence.

    This turns classification into workflow guidance.
    """

    # Low-confidence classifications should not be fully automated.
    # They should go to a human for review.
    if confidence < 0.60:
        return "Send to human triage because classifier confidence is low."

    # Critical issues should be escalated regardless of category.
    if urgency == "Critical":
        return f"Escalate immediately to {owner} and notify the account lead."

    # Category-specific recommendations provide the next operational step.
    if category == "Billing":
        return "Review invoice history and confirm whether a billing correction is required."

    if category == "Account Access":
        return "Verify user identity and begin access recovery workflow."

    if category == "Security / Compliance":
        return "Send approved security documentation or route to security review."

    if category == "Product Question":
        return "Route to customer success with relevant documentation."

    if category == "Technical Issue":
        return "Collect logs, reproduction steps, and recent change history."

    # Fallback recommendation for uncategorized or ambiguous tickets.
    return "Review manually and assign to the appropriate team."


def triage_tickets(input_file: str = INPUT_FILE) -> pd.DataFrame:
    """
    Load tickets and return a triaged DataFrame.

    This function is separated from main() so other scripts, such as evaluate.py,
    can reuse the same triage logic without duplicating code.
    """

    # Load the source CSV into a pandas DataFrame.
    tickets = pd.read_csv(input_file)

    # This list will hold one enriched row per ticket.
    triaged_rows = []

    # Process each ticket one row at a time.
    for _, row in tickets.iterrows():
        # Run the classification logic on the ticket message.
        classification = classify_ticket(row["message"])

        # Generate a short readable summary.
        summary = summarize_ticket(row["message"])

        # Generate the recommended next action for the ticket.
        next_action = recommend_next_action(
            classification["category"],
            classification["urgency"],
            classification["owner"],
            classification["confidence"],
        )

        # Build the enriched output row.
        triaged_rows.append({
            "ticket_id": row["ticket_id"],
            "customer": row["customer"],
            "message": row["message"],
            "category": classification["category"],
            "urgency": classification["urgency"],
            "owner": classification["owner"],
            "confidence": classification["confidence"],
            "matched_rules": classification["matched_rules"],
            "summary": summary,
            "next_action": next_action,
        })

    # Convert the enriched rows back into a DataFrame.
    return pd.DataFrame(triaged_rows)


def main():
    """
    Main entry point for running the ticket triage application from the terminal.
    """

    # Run the triage workflow.
    triaged_tickets = triage_tickets(INPUT_FILE)

    # These are the columns we want to show in the terminal.
    # We do not print every field because too much output becomes hard to read.
    display_columns = [
        "ticket_id",
        "customer",
        "urgency",
        "category",
        "owner",
        "confidence",
        "summary",
        "next_action",
    ]

    # Print a clean terminal view of the triaged tickets.
    print(triaged_tickets[display_columns].to_string(index=False))

    # Write the full enriched dataset to a CSV file.
    triaged_tickets.to_csv(OUTPUT_FILE, index=False)

    print(f"\nWrote triaged tickets to {OUTPUT_FILE}")


# This ensures main() only runs when this file is executed directly.
# It prevents main() from automatically running when another file imports functions from main.py.
if __name__ == "__main__":
    main()