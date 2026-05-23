import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


# This script generates a synthetic ServiceNow-style incident dataset.
# It creates both:
# 1. data/incidents.csv — realistic source incident data
# 2. data/expected_results.csv — ground-truth labels for evaluation


# Set a random seed so the generated dataset is repeatable.
# Repeatability matters because we want stable evaluation results.
random.seed(42)


# Define output paths in one place so they are easy to change later.
DATA_DIR = Path("data")
INCIDENTS_FILE = DATA_DIR / "incidents.csv"
EXPECTED_RESULTS_FILE = DATA_DIR / "expected_results.csv"


# These companies and callers make the dataset feel more realistic.
# They are synthetic and not intended to represent real support records.
COMPANIES = [
    "Acme Corp",
    "Globex",
    "Initech",
    "Umbrella Health",
    "Stark Industries",
    "Wayne Enterprises",
    "Hooli",
    "Massive Dynamic",
    "Nakatomi Trading",
    "Cyberdyne Systems",
    "Oceanic Airlines",
    "Primatech Paper",
    "Pied Piper",
    "Dunder Mifflin",
    "Roxxon Energy",
]

CALLERS = [
    "Jordan Blake",
    "Morgan Lee",
    "Taylor Smith",
    "Casey Nguyen",
    "Riley Johnson",
    "Avery Patel",
    "Quinn Davis",
    "Jamie Wilson",
    "Cameron Brown",
    "Drew Martinez",
]


# The services and configuration items mimic fields often seen in ITSM records.
SERVICES = [
    "Customer Portal",
    "Admin Portal",
    "Billing Platform",
    "Integration Platform",
    "Reporting Dashboard",
    "Identity and Access",
    "Security Review",
    "Developer Platform",
]

CONFIGURATION_ITEMS = [
    "Okta SSO",
    "Salesforce Connector",
    "Billing Engine",
    "Webhook Gateway",
    "API Gateway",
    "Data Warehouse Sync",
    "User Management",
    "Executive Dashboard",
]


# Assignment groups are the teams that should own the ticket.
ASSIGNMENT_GROUP_BY_CATEGORY = {
    "Billing": "Finance Operations",
    "Account Access": "Service Desk",
    "Security / Compliance": "Security Operations",
    "Product Question": "Customer Success",
    "Technical Issue": "Application Engineering",
    "Other": "Service Desk",
}


# This list defines realistic ticket templates.
# Each template includes both source-system fields and expected triage labels.
TICKET_TEMPLATES = [
    {
        "triage_category": "Technical Issue",
        "short_description": "Production integration stopped processing new records",
        "description": "The production Salesforce integration stopped processing new records and business users are missing updates.",
        "category": "Software",
        "subcategory": "Integration",
        "impact": "2 - Medium",
        "urgency": "1 - High",
        "priority": "2 - High",
        "expected_urgency": "Critical",
    },
    {
        "triage_category": "Technical Issue",
        "short_description": "Dashboard unavailable for executive users",
        "description": "The reporting dashboard is unavailable and executives are asking for an immediate status update.",
        "category": "Software",
        "subcategory": "Reporting",
        "impact": "1 - High",
        "urgency": "1 - High",
        "priority": "1 - Critical",
        "expected_urgency": "Critical",
    },
    {
        "triage_category": "Technical Issue",
        "short_description": "API endpoint returning 500 errors",
        "description": "The customer is receiving 500 errors from the API endpoint after the latest release.",
        "category": "Software",
        "subcategory": "API",
        "impact": "2 - Medium",
        "urgency": "2 - Medium",
        "priority": "3 - Moderate",
        "expected_urgency": "High",
    },
    {
        "triage_category": "Technical Issue",
        "short_description": "Scheduled workflow creating duplicate records",
        "description": "A scheduled workflow is creating duplicate records in the downstream system.",
        "category": "Software",
        "subcategory": "Workflow",
        "impact": "2 - Medium",
        "urgency": "2 - Medium",
        "priority": "3 - Moderate",
        "expected_urgency": "High",
    },
    {
        "triage_category": "Account Access",
        "short_description": "User cannot access admin portal",
        "description": "A payroll administrator cannot access the admin portal before the payroll cutoff.",
        "category": "Access",
        "subcategory": "Login",
        "impact": "2 - Medium",
        "urgency": "1 - High",
        "priority": "2 - High",
        "expected_urgency": "Critical",
    },
    {
        "triage_category": "Account Access",
        "short_description": "Password reset email not received",
        "description": "The user cannot reset their password because the reset email never arrives.",
        "category": "Access",
        "subcategory": "Password Reset",
        "impact": "3 - Low",
        "urgency": "2 - Medium",
        "priority": "4 - Low",
        "expected_urgency": "High",
    },
    {
        "triage_category": "Account Access",
        "short_description": "One user locked out",
        "description": "One user is locked out of the workspace but other users can log in successfully.",
        "category": "Access",
        "subcategory": "Account Lockout",
        "impact": "3 - Low",
        "urgency": "3 - Low",
        "priority": "5 - Planning",
        "expected_urgency": "Medium",
    },
    {
        "triage_category": "Billing",
        "short_description": "Invoice total appears incorrect",
        "description": "The invoice total appears incorrect for the April renewal and the customer wants a review.",
        "category": "Inquiry",
        "subcategory": "Invoice",
        "impact": "3 - Low",
        "urgency": "2 - Medium",
        "priority": "4 - Low",
        "expected_urgency": "Medium",
    },
    {
        "triage_category": "Billing",
        "short_description": "Customer was charged twice",
        "description": "The customer reports they were charged twice and needs a refund.",
        "category": "Inquiry",
        "subcategory": "Payment",
        "impact": "2 - Medium",
        "urgency": "2 - Medium",
        "priority": "3 - Moderate",
        "expected_urgency": "High",
    },
    {
        "triage_category": "Billing",
        "short_description": "Billing address needs correction",
        "description": "The customer needs the billing address corrected before the next invoice is issued.",
        "category": "Inquiry",
        "subcategory": "Billing Profile",
        "impact": "3 - Low",
        "urgency": "3 - Low",
        "priority": "5 - Planning",
        "expected_urgency": "Medium",
    },
    {
        "triage_category": "Security / Compliance",
        "short_description": "SOC 2 report requested",
        "description": "The customer's procurement team needs the latest SOC 2 Type II report for vendor review.",
        "category": "Security",
        "subcategory": "Compliance Documentation",
        "impact": "3 - Low",
        "urgency": "2 - Medium",
        "priority": "4 - Low",
        "expected_urgency": "Medium",
    },
    {
        "triage_category": "Security / Compliance",
        "short_description": "Question about encryption at rest",
        "description": "A security reviewer is asking whether customer data is encrypted at rest.",
        "category": "Security",
        "subcategory": "Data Protection",
        "impact": "3 - Low",
        "urgency": "2 - Medium",
        "priority": "4 - Low",
        "expected_urgency": "Medium",
    },
    {
        "triage_category": "Security / Compliance",
        "short_description": "Access logs requested for audit",
        "description": "The audit team needs access logs for the last quarter.",
        "category": "Security",
        "subcategory": "Audit",
        "impact": "2 - Medium",
        "urgency": "2 - Medium",
        "priority": "3 - Moderate",
        "expected_urgency": "Medium",
    },
    {
        "triage_category": "Product Question",
        "short_description": "Question about SAML and SCIM support",
        "description": "The customer wants to know whether the API supports SAML authentication and SCIM provisioning.",
        "category": "Inquiry",
        "subcategory": "Product Capability",
        "impact": "3 - Low",
        "urgency": "3 - Low",
        "priority": "5 - Planning",
        "expected_urgency": "Medium",
    },
    {
        "triage_category": "Product Question",
        "short_description": "Webhook retry behavior question",
        "description": "The customer asks whether webhook retries and dead-letter queues are supported.",
        "category": "Inquiry",
        "subcategory": "Developer Platform",
        "impact": "3 - Low",
        "urgency": "3 - Low",
        "priority": "5 - Planning",
        "expected_urgency": "Medium",
    },
    {
        "triage_category": "Product Question",
        "short_description": "Pricing tier explanation requested",
        "description": "The customer wants an explanation of enterprise pricing tiers and additional user pricing.",
        "category": "Inquiry",
        "subcategory": "Pricing",
        "impact": "3 - Low",
        "urgency": "3 - Low",
        "priority": "5 - Planning",
        "expected_urgency": "Low",
    },
    {
        "triage_category": "Other",
        "short_description": "General request for documentation",
        "description": "The customer is asking for general documentation but did not specify the product area.",
        "category": "Inquiry",
        "subcategory": "General",
        "impact": "3 - Low",
        "urgency": "3 - Low",
        "priority": "5 - Planning",
        "expected_urgency": "Low",
    },
]


def build_priority_from_impact_urgency(impact: str, urgency: str) -> str:
    """
    Return a simple priority value based on impact and urgency.

    This mimics the ServiceNow concept that priority is commonly derived
    from impact and urgency using priority lookup rules.
    """

    # Convert labels like "1 - High" into their numeric values.
    impact_value = int(impact.split(" - ")[0])
    urgency_value = int(urgency.split(" - ")[0])

    # Simple priority matrix for synthetic data.
    if impact_value == 1 and urgency_value == 1:
        return "1 - Critical"

    if impact_value == 1 or urgency_value == 1:
        return "2 - High"

    if impact_value == 2 and urgency_value == 2:
        return "3 - Moderate"

    if impact_value == 3 and urgency_value == 3:
        return "5 - Planning"

    return "4 - Low"


def generate_incident_number(index: int) -> str:
    """
    Generate a ServiceNow-style incident number.

    ServiceNow incident numbers commonly use an INC prefix.
    """

    return f"INC{index:07d}"


def generate_dataset(row_count: int = 300) -> None:
    """
    Generate synthetic incidents and expected evaluation labels.
    """

    # Make sure the data directory exists before writing files.
    DATA_DIR.mkdir(exist_ok=True)

    incidents = []
    expected_results = []

    # Use a fixed base date so generated timestamps are stable.
    base_time = datetime(2026, 5, 1, 8, 0, 0)

    for index in range(1, row_count + 1):
        # Select a ticket template. The template controls the business scenario.
        template = random.choice(TICKET_TEMPLATES)

        # Generate realistic-looking metadata.
        opened_at = base_time + timedelta(
            days=random.randint(0, 20),
            hours=random.randint(0, 8),
            minutes=random.randint(0, 59),
        )
        updated_at = opened_at + timedelta(
            hours=random.randint(0, 24),
            minutes=random.randint(0, 59),
        )

        company = random.choice(COMPANIES)
        caller = random.choice(CALLERS)
        service = random.choice(SERVICES)
        configuration_item = random.choice(CONFIGURATION_ITEMS)

        expected_owner = ASSIGNMENT_GROUP_BY_CATEGORY[template["triage_category"]]

        # Recalculate priority from impact and urgency so the dataset is internally consistent.
        priority = build_priority_from_impact_urgency(
            template["impact"],
            template["urgency"],
        )

        incident_number = generate_incident_number(index)

        # This row simulates a source-system export from an ITSM tool.
        incidents.append({
            "number": incident_number,
            "opened_at": opened_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "caller": caller,
            "company": company,
            "short_description": template["short_description"],
            "description": template["description"],
            "category": template["category"],
            "subcategory": template["subcategory"],
            "impact": template["impact"],
            "urgency": template["urgency"],
            "priority": priority,
            "state": random.choice(["New", "In Progress", "On Hold"]),
            "assignment_group": expected_owner,
            "assigned_to": "",
            "channel": random.choice(["Portal", "Email", "Phone", "Chat"]),
            "service": service,
            "configuration_item": configuration_item,
            "location": random.choice(["Remote", "New York", "Chicago", "San Francisco", "Washington DC"]),
            "resolution_notes": "",
        })

        # This row contains the expected labels for our classifier evaluation.
        expected_results.append({
            "number": incident_number,
            "expected_triage_category": template["triage_category"],
            "expected_urgency": template["expected_urgency"],
            "expected_owner": expected_owner,
            "expected_priority": priority,
            "expected_requires_human_review": "False",
        })

    # Write the synthetic incident export.
    with INCIDENTS_FILE.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=incidents[0].keys())
        writer.writeheader()
        writer.writerows(incidents)

    # Write the expected evaluation labels.
    with EXPECTED_RESULTS_FILE.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=expected_results[0].keys())
        writer.writeheader()
        writer.writerows(expected_results)

    print(f"Wrote {len(incidents)} incidents to {INCIDENTS_FILE}")
    print(f"Wrote {len(expected_results)} expected results to {EXPECTED_RESULTS_FILE}")


if __name__ == "__main__":
    generate_dataset(row_count=300)