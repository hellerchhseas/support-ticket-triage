import pandas as pd

from db import (
    get_table_counts,
    initialize_database,
    load_incidents_from_dataframe,
)


# The incident source file is the realistic ITSM dataset generated in Lesson 2.5.
INCIDENTS_FILE = "data/incidents.csv"


def main() -> None:
    """
    Initialize the SQLite database and load source incidents.

    This script is a simple setup utility for Lesson 7.
    """

    # Create database tables if they do not already exist.
    initialize_database()

    # Load the incident CSV into a dataframe.
    incidents_df = pd.read_csv(INCIDENTS_FILE)

    # Insert or update incidents in the database.
    loaded_count = load_incidents_from_dataframe(incidents_df)

    # Print database table counts to confirm setup worked.
    counts = get_table_counts()

    print(f"Loaded {loaded_count} incidents into the database.")
    print("Current table counts:")
    for table_name, count in counts.items():
        print(f"- {table_name}: {count}")


if __name__ == "__main__":
    main()