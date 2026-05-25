from db import get_table_counts, read_table


def main() -> None:
    """
    Print simple database diagnostics.

    This helps verify what is currently stored in SQLite.
    """

    counts = get_table_counts()

    print("Database table counts:")
    for table_name, count in counts.items():
        print(f"- {table_name}: {count}")

    print("\nSample incidents:")
    print(read_table("incidents", limit=5).to_string(index=False))

    print("\nSample triage predictions:")
    print(read_table("triage_predictions", limit=5).to_string(index=False))

    print("\nSample review decisions:")
    print(read_table("review_decisions", limit=5).to_string(index=False))


if __name__ == "__main__":
    main()