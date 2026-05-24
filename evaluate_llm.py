import pandas as pd


# The LLM output file is produced by llm_triage.py.
LLM_RESULTS_FILE = "data/llm_triaged_incidents.csv"

# Expected labels are the ground truth from Lesson 2.5.
EXPECTED_RESULTS_FILE = "data/expected_results.csv"


def calculate_accuracy(results: pd.DataFrame, actual_column: str, expected_column: str) -> float:
    """
    Calculate the percentage of rows where actual output matches expected output.
    """

    correct_count = (results[actual_column] == results[expected_column]).sum()
    total_count = len(results)

    return correct_count / total_count


def print_failures(results: pd.DataFrame, actual_column: str, expected_column: str) -> None:
    """
    Print mismatches between LLM output and expected labels.
    """

    failures = results[results[actual_column] != results[expected_column]]

    if failures.empty:
        print(f"\nNo failures for {actual_column}.")
        return

    print(f"\nFailures for {actual_column}:")
    for _, row in failures.iterrows():
        print(
            f"- {row['number']}: "
            f"expected={row[expected_column]}, "
            f"actual={row[actual_column]}, "
            f"short_description=\"{row['short_description']}\""
        )


def main():
    """
    Evaluate LLM triage results against expected labels.
    """

    # Load LLM-generated triage results.
    llm_results = pd.read_csv(LLM_RESULTS_FILE)

    # Load expected labels.
    expected_results = pd.read_csv(EXPECTED_RESULTS_FILE)

    # Join on incident number.
    results = llm_results.merge(expected_results, on="number", how="inner")

    # Score the main LLM outputs.
    category_accuracy = calculate_accuracy(
        results,
        "llm_triage_category",
        "expected_triage_category",
    )
    urgency_accuracy = calculate_accuracy(
        results,
        "llm_triage_urgency",
        "expected_urgency",
    )
    owner_accuracy = calculate_accuracy(
        results,
        "llm_recommended_owner",
        "expected_owner",
    )

    # Print headline metrics.
    print("\nLLM Evaluation Results")
    print("======================")
    print(f"Total evaluated incidents: {len(results)}")
    print(f"Category accuracy: {category_accuracy:.0%}")
    print(f"Urgency accuracy:  {urgency_accuracy:.0%}")
    print(f"Owner accuracy:    {owner_accuracy:.0%}")

    # Print detailed failure analysis.
    print_failures(results, "llm_triage_category", "expected_triage_category")
    print_failures(results, "llm_triage_urgency", "expected_urgency")
    print_failures(results, "llm_recommended_owner", "expected_owner")


if __name__ == "__main__":
    main()