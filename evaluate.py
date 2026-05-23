import pandas as pd

from main import triage_tickets


# This file contains the manually labeled expected answers.
# It acts as our small ground-truth dataset.
EXPECTED_RESULTS_FILE = "expected_results.csv"


def calculate_accuracy(results: pd.DataFrame, actual_column: str, expected_column: str) -> float:
    """
    Calculate the percentage of rows where actual output matches expected output.
    """

    # Count how many rows have the same value in the actual and expected columns.
    correct_count = (results[actual_column] == results[expected_column]).sum()

    # Count the total number of evaluated rows.
    total_count = len(results)

    # Return accuracy as a decimal, such as 0.86 for 86%.
    return correct_count / total_count


def print_field_failures(results: pd.DataFrame, actual_column: str, expected_column: str) -> None:
    """
    Print rows where a specific field did not match the expected result.

    This helps us diagnose exactly where the classifier is failing.
    """

    # Filter the dataset to only rows where actual and expected values differ.
    failures = results[results[actual_column] != results[expected_column]]

    # If there are no failures, report that the field passed all examples.
    if failures.empty:
        print(f"\nNo failures for {actual_column}.")
        return

    # Print each failed row with enough context to understand the mistake.
    print(f"\nFailures for {actual_column}:")
    for _, row in failures.iterrows():
        print(
            f"- Ticket {row['ticket_id']}: "
            f"expected={row[expected_column]}, "
            f"actual={row[actual_column]}, "
            f"message=\"{row['message']}\""
        )


def main():
    """
    Evaluate classifier output against expected results.

    This turns the project from a working script into a measurable system.
    """

    # Run the same triage logic used by main.py.
    actual_results = triage_tickets()

    # Load the manually labeled expected results.
    expected_results = pd.read_csv(EXPECTED_RESULTS_FILE)

    # Join actual and expected results by ticket_id so each row can be compared.
    results = actual_results.merge(expected_results, on="ticket_id", how="inner")

    # Calculate accuracy for each major output field.
    category_accuracy = calculate_accuracy(
        results,
        actual_column="category",
        expected_column="expected_category",
    )

    urgency_accuracy = calculate_accuracy(
        results,
        actual_column="urgency",
        expected_column="expected_urgency",
    )

    owner_accuracy = calculate_accuracy(
        results,
        actual_column="owner",
        expected_column="expected_owner",
    )

    # Print high-level evaluation metrics.
    print("\nEvaluation Results")
    print("==================")
    print(f"Total evaluated tickets: {len(results)}")
    print(f"Category accuracy: {category_accuracy:.0%}")
    print(f"Urgency accuracy:  {urgency_accuracy:.0%}")
    print(f"Owner accuracy:    {owner_accuracy:.0%}")

    # Print detailed failures so we know what to fix next.
    print_field_failures(
        results,
        actual_column="category",
        expected_column="expected_category",
    )

    print_field_failures(
        results,
        actual_column="urgency",
        expected_column="expected_urgency",
    )

    print_field_failures(
        results,
        actual_column="owner",
        expected_column="expected_owner",
    )


# This ensures the evaluator only runs when this file is executed directly.
if __name__ == "__main__":
    main()