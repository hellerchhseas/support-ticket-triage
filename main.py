import pandas as pd

INPUT_FILE = "tickets.csv"
OUTPUT_FILE = "triaged_tickets.csv"

def classify_ticket(message: str) -> dict:
    """
    Classify a support ticket based on simple keyword rules.

    This first version is intentionally deterministic.
    Before adding AI, we want a baseline that is easy to inspect,
    debug, and explain.
    """
    message_lower = message.lower()

    if any(word in message_lower for word in ["invoice", "charged", "refund", "renewal"]):
        category = "Billing"
        owner = "Finance"
    elif any(word in message_lower for word in ["cannot access", "password", "login", "reset"]):
        category = "Account Access"
        owner = "Support"
    elif any(word in message_lower for word in ["security", "soc 2", "controls", "compliance"]):
        category = "Security / Compliance"
        owner = "Security"
    elif any(word in message_lower for word in ["api", "saml", "scim", "documentation", "pricing"]):
        category = "Product Question"
        owner = "Customer Success"
    elif any(word in message_lower for word in ["failing", "stopped", "syncing", "production", "integration"]):
        category = "Technical Issue"
        owner = "Engineering"
    else:
        category = "Other"
        owner = "Support"

    urgency = determine_urgency(message_lower)

    return {
        "category": category,
        "urgency": urgency,
        "owner": owner,
    }


def determine_urgency(message_lower: str) -> str:
    """
    Determine urgency from business impact language.
    """
    if any(phrase in message_lower for phrase in ["blocking", "production", "failing", "stopped"]):
        return "Critical"
    elif any(phrase in message_lower for phrase in ["charged twice", "cannot access", "today"]):
        return "High"
    elif any(phrase in message_lower for phrase in ["slowly", "not blocking", "question", "explain"]):
        return "Low"
    else:
        return "Medium"

def summarize_ticket(message: str) -> str:
    """
    Create a short human-readable summary.

    This is a crude baseline. Later, an LLM can produce better summaries.
    """
    if len(message) <= 90:
        return message

    return message[:87] + "..."


def recommend_next_action(category: str, urgency: str, owner: str) -> str:
    """
    Recommend the next operational action based on category and urgency.
    """
    if urgency == "Critical":
        return f"Escalate immediately to {owner} and notify the account lead."

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

    return "Review manually and assign to the appropriate team."


def main():
    tickets = pd.read_csv(INPUT_FILE)

    triaged_rows = []

    for _, row in tickets.iterrows():
        classification = classify_ticket(row["message"])

        summary = summarize_ticket(row["message"])
        next_action = recommend_next_action(
            classification["category"],
            classification["urgency"],
            classification["owner"],
        )

        triaged_rows.append({
            "ticket_id": row["ticket_id"],
            "customer": row["customer"],
            "message": row["message"],
            "category": classification["category"],
            "urgency": classification["urgency"],
            "owner": classification["owner"],
            "summary": summary,
            "next_action": next_action,
        })

    triaged_tickets = pd.DataFrame(triaged_rows)

    display_columns = [
        "ticket_id",
        "customer",
        "urgency",
        "category",
        "owner",
        "summary",
        "next_action",
    ]

    print(triaged_tickets[display_columns].to_string(index=False))

    triaged_tickets.to_csv(OUTPUT_FILE, index=False)

    print(f"\nWrote triaged tickets to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()