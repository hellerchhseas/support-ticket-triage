import pandas as pd

from main import triage_tickets


# The expected results file contains ground-truth labels for evaluation.
EXPECTED_RESULTS_FILE = "data/expected_results.csv"


def calculate_accuracy(results: pd.DataFrame, actual_column: str, expected_column: str) -> float:
    """
    Calculate accuracy for one output field.
    """

    # Count rows where actual and expected values match.
    correct_count = (results[actual_column] == results[expected_column]).sum()

    # Count total evaluated rows.
    total_count = len(results)

    # Return the percent correct as a decimal.
    return correct_count / total_count


def print_field_failures(results: pd.DataFrame, actual_column: str, expected_column: str) -> None:
    """
    Print rows where a specific classifier output does not match the expected label.
    """

    # Filter to only failed rows for this field.
    failures = results[results[actual_column] != results[expected_column]]

    # If there are no failures, report a clean pass.
    if failures.empty:
        print(f"\nNo failures for {actual_column}.")
        return

    # Print failed examples with enough context to debug them.
    print(f"\nFailures for {actual_column}:")
    for _, row in failures.iterrows():
        print(
            f"- {row['number']}: "
            f"expected={row[expected_column]}, "
            f"actual={row[actual_column]}, "
            f"short_description=\"{row['short_description']}\""
        )


def print_distribution(results: pd.DataFrame, column: str) -> None:
    """
    Print the distribution of values in a column.

    This helps us understand class balance in the dataset.
    """

    print(f"\nDistribution for {column}:")
    print(results[column].value_counts().to_string())


def main():
    """
    Evaluate triage outputs against expected results.
    """

    # Run the triage classifier against the incident dataset.
    actual_results = triage_tickets()

    # Load expected labels.
    expected_results = pd.read_csv(EXPECTED_RESULTS_FILE)

    # Join actual and expected results by incident number.
    results = actual_results.merge(expected_results, on="number", how="inner")

    # Calculate accuracy for each evaluated field.
    category_accuracy = calculate_accuracy(
        results,
        actual_column="triage_category",
        expected_column="expected_triage_category",
    )

    urgency_accuracy = calculate_accuracy(
        results,
        actual_column="triage_urgency",
        expected_column="expected_urgency",
    )

    owner_accuracy = calculate_accuracy(
        results,
        actual_column="recommended_owner",
        expected_column="expected_owner",
    )

    review_accuracy = calculate_accuracy(
        results,
        actual_column="requires_human_review",
        expected_column="expected_requires_human_review",
    )

    # Print headline evaluation metrics.
    print("\nEvaluation Results")
    print("==================")
    print(f"Total evaluated incidents: {len(results)}")
    print(f"Category accuracy:      {category_accuracy:.0%}")
    print(f"Urgency accuracy:       {urgency_accuracy:.0%}")
    print(f"Owner accuracy:         {owner_accuracy:.0%}")
    print(f"Human review accuracy:  {review_accuracy:.0%}")

    # Print distribution analysis to understand dataset shape.
    print_distribution(results, "expected_triage_category")
    print_distribution(results, "expected_urgency")
    print_distribution(results, "triage_category")
    print_distribution(results, "triage_urgency")

    # Print detailed failures.
    print_field_failures(
        results,
        actual_column="triage_category",
        expected_column="expected_triage_category",
    )

    print_field_failures(
        results,
        actual_column="triage_urgency",
        expected_column="expected_urgency",
    )

    print_field_failures(
        results,
        actual_column="recommended_owner",
        expected_column="expected_owner",
    )

    print_field_failures(
        results,
        actual_column="requires_human_review",
        expected_column="expected_requires_human_review",
    )


if __name__ == "__main__":
    main()