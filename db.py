import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd


# ------------------------------------------------------------
# Database path
# ------------------------------------------------------------
# SQLite stores the entire database in a local file.
# We keep it under data/ because it is project data, not source code.
DB_FILE = Path("data/triage_workflow.db")


def get_utc_timestamp() -> str:
    """
    Return the current UTC timestamp as an ISO-formatted string.

    Using UTC avoids confusion when logs or review decisions are created
    across different machines or time zones.
    """

    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    """
    Open a connection to the SQLite database.

    The database file is created automatically if it does not exist.
    """

    DB_FILE.parent.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_FILE)

    # This lets sqlite return rows that can be accessed like dictionaries.
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database() -> None:
    """
    Create database tables if they do not already exist.

    This function is safe to run multiple times because each CREATE TABLE
    statement uses IF NOT EXISTS.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # incidents stores the source incident records.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS incidents (
            number TEXT PRIMARY KEY,
            company TEXT,
            caller TEXT,
            short_description TEXT,
            description TEXT,
            source_category TEXT,
            source_subcategory TEXT,
            source_impact TEXT,
            source_urgency TEXT,
            source_priority TEXT,
            source_assignment_group TEXT,
            service TEXT,
            configuration_item TEXT,
            channel TEXT,
            location TEXT,
            loaded_at TEXT
        )
        """
    )

    # triage_predictions stores outputs from rules, LLM, and hybrid triage.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS triage_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_number TEXT,
            triage_mode TEXT,
            triage_category TEXT,
            triage_urgency TEXT,
            recommended_owner TEXT,
            confidence REAL,
            requires_human_review INTEGER,
            summary TEXT,
            next_action TEXT,
            reasoning_summary TEXT,
            created_at TEXT,
            FOREIGN KEY (incident_number) REFERENCES incidents(number)
        )
        """
    )

    # review_decisions stores human decisions and overrides.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS review_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_number TEXT,
            reviewed_category TEXT,
            reviewed_urgency TEXT,
            reviewed_owner TEXT,
            review_status TEXT,
            review_notes TEXT,
            decision_source TEXT,
            decided_at TEXT,
            FOREIGN KEY (incident_number) REFERENCES incidents(number)
        )
        """
    )

    connection.commit()
    connection.close()


def load_incidents_from_dataframe(df: pd.DataFrame) -> int:
    """
    Load source incidents into the incidents table.

    Existing incidents are updated using INSERT OR REPLACE.
    This keeps the table aligned with the latest source dataset.
    """

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    loaded_at = get_utc_timestamp()
    row_count = 0

    for _, row in df.iterrows():
        cursor.execute(
            """
            INSERT OR REPLACE INTO incidents (
                number,
                company,
                caller,
                short_description,
                description,
                source_category,
                source_subcategory,
                source_impact,
                source_urgency,
                source_priority,
                source_assignment_group,
                service,
                configuration_item,
                channel,
                location,
                loaded_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("number"),
                row.get("company"),
                row.get("caller", ""),
                row.get("short_description"),
                row.get("description"),
                row.get("category", row.get("source_category", "")),
                row.get("subcategory", row.get("source_subcategory", "")),
                row.get("impact", row.get("source_impact", "")),
                row.get("urgency", row.get("source_urgency", "")),
                row.get("priority", row.get("source_priority", "")),
                row.get("assignment_group", row.get("source_assignment_group", "")),
                row.get("service", ""),
                row.get("configuration_item", ""),
                row.get("channel", ""),
                row.get("location", ""),
                loaded_at,
            ),
        )
        row_count += 1

    connection.commit()
    connection.close()

    return row_count


def save_triage_prediction(
    incident_number: str,
    triage_mode: str,
    triage_category: str,
    triage_urgency: str,
    recommended_owner: str,
    confidence: float,
    requires_human_review: bool,
    summary: str,
    next_action: str,
    reasoning_summary: str,
) -> int:
    """
    Save a single triage prediction.

    This stores what the system recommended before any human review decision.
    """

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO triage_predictions (
            incident_number,
            triage_mode,
            triage_category,
            triage_urgency,
            recommended_owner,
            confidence,
            requires_human_review,
            summary,
            next_action,
            reasoning_summary,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            incident_number,
            triage_mode,
            triage_category,
            triage_urgency,
            recommended_owner,
            confidence,
            int(requires_human_review),
            summary,
            next_action,
            reasoning_summary,
            get_utc_timestamp(),
        ),
    )

    prediction_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return prediction_id


def save_review_decision(
    incident_number: str,
    reviewed_category: str,
    reviewed_urgency: str,
    reviewed_owner: str,
    review_status: str,
    review_notes: str,
    decision_source: str,
) -> int:
    """
    Save a human review decision.

    The decision_source field tells us whether the reviewer approved the hybrid
    recommendation, used rules, used LLM, or manually overrode the result.
    """

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO review_decisions (
            incident_number,
            reviewed_category,
            reviewed_urgency,
            reviewed_owner,
            review_status,
            review_notes,
            decision_source,
            decided_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            incident_number,
            reviewed_category,
            reviewed_urgency,
            reviewed_owner,
            review_status,
            review_notes,
            decision_source,
            get_utc_timestamp(),
        ),
    )

    decision_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return decision_id


def get_latest_review_decisions() -> pd.DataFrame:
    """
    Return the latest review decision for each incident.

    This is useful for restoring review state in the Streamlit app.
    """

    initialize_database()

    connection = get_connection()

    query = """
        SELECT rd.*
        FROM review_decisions rd
        INNER JOIN (
            SELECT incident_number, MAX(decided_at) AS latest_decided_at
            FROM review_decisions
            GROUP BY incident_number
        ) latest
        ON rd.incident_number = latest.incident_number
        AND rd.decided_at = latest.latest_decided_at
    """

    df = pd.read_sql_query(query, connection)

    connection.close()

    return df


def get_table_counts() -> dict:
    """
    Return row counts for the major database tables.

    This is a simple way to verify the database is being populated.
    """

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    counts = {}

    for table_name in ["incidents", "triage_predictions", "review_decisions"]:
        cursor.execute(f"SELECT COUNT(*) AS count FROM {table_name}")
        counts[table_name] = cursor.fetchone()["count"]

    connection.close()

    return counts


def read_table(table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
    """
    Read a table into a dataframe for debugging or inspection.

    The table name should come from trusted code, not arbitrary user input.
    """

    initialize_database()

    connection = get_connection()

    query = f"SELECT * FROM {table_name}"

    if limit is not None:
        query += f" LIMIT {limit}"

    df = pd.read_sql_query(query, connection)

    connection.close()

    return df