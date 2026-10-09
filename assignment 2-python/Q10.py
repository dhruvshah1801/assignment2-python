import os
import sys

import pandas as pd
import matplotlib

# Use a non-interactive backend for saving chart images.
matplotlib.use("Agg")

import matplotlib.pyplot as plt


IDENTIFIER_COLUMNS = ["enrollment", "name"]


def load_dataset(file_path):
    """Load the CSV dataset and validate required columns."""

    if not os.path.isfile(file_path):
        raise FileNotFoundError(
            f"Input file not found: {file_path}"
        )

    dataframe = pd.read_csv(file_path)

    if dataframe.empty:
        raise ValueError("The input CSV contains no data rows.")

    for column in IDENTIFIER_COLUMNS:
        if column not in dataframe.columns:
            raise ValueError(
                f"Required column '{column}' is missing."
            )

    subject_columns = [
        column for column in dataframe.columns
        if column not in IDENTIFIER_COLUMNS
    ]

    if not subject_columns:
        raise ValueError("No subject columns were found.")

    return dataframe, subject_columns


def clean_dataset(dataframe, subject_columns):
    """
    Clean missing and invalid marks.

    Missing or invalid marks are replaced with the median
    of the corresponding subject.
    """

    cleaned = dataframe.copy()

    # Remove rows without essential student identifiers.
    cleaned["name"] = cleaned["name"].astype("string").str.strip()
    cleaned = cleaned.dropna(subset=["enrollment", "name"])

    cleaned = cleaned[cleaned["name"] != ""]

    # Validate enrollment identifiers.
    cleaned["enrollment"] = pd.to_numeric(
        cleaned["enrollment"],
        errors="coerce"
    )

    cleaned = cleaned.dropna(subset=["enrollment"])

    if cleaned.empty:
        raise ValueError(
            "No valid student records remain after cleaning."
        )

    # Reject duplicate enrollment identifiers.
    if cleaned["enrollment"].duplicated().any():
        raise ValueError(
            "Duplicate enrollment identifiers were found."
        )

    # Clean subject marks.
    for subject in subject_columns:

        cleaned[subject] = pd.to_numeric(
            cleaned[subject],
            errors="coerce"
        )

        # Marks outside 0 to 100 are treated as missing.
        invalid_marks = (
            (cleaned[subject] < 0)
            | (cleaned[subject] > 100)
        )

        cleaned.loc[invalid_marks, subject] = float("nan")

        # Fill missing values using the subject median.
        median_value = cleaned[subject].median()

        if pd.isna(median_value):
            # If an entire subject column is missing,
            # use zero as a documented fallback.
            median_value = 0

        cleaned[subject] = cleaned[subject].fillna(
            median_value
        )

    cleaned["enrollment"] = cleaned["enrollment"].astype(int)

    return cleaned


def calculate_summary(cleaned, subject_columns):
    """Calculate subject-wise summary statistics."""

    summary = []

    for subject in subject_columns:
        marks = cleaned[subject]

        summary.append({
            "subject": subject,
            "count": len(marks),
            "average": marks.mean(),
            "minimum": marks.min(),
            "maximum": marks.max(),
            "median": marks.median()
        })

    return pd.DataFrame(summary)


def assign_grade(percentage):
    """Assign a grade based on the student's average marks."""

    if percentage >= 90:
        return "A"

    if percentage >= 80:
        return "B"

    if percentage >= 70:
        return "C"

    if percentage >= 60:
        return "D"

    return "F"


def export_grade_distribution(cleaned, subject_columns, output_dir):
    """Export a bar chart showing the grade distribution."""

    student_average = cleaned[subject_columns].mean(axis=1)

    grades = student_average.apply(assign_grade)

    distribution = (
        grades.value_counts()
        .reindex(["A", "B", "C", "D", "F"], fill_value=0)
    )

    plt.figure(figsize=(8, 5))

    distribution.plot(kind="bar")

    plt.title("Student Grade Distribution")
    plt.xlabel("Grade")
    plt.ylabel("Number of Students")
    plt.xticks(rotation=0)
    plt.tight_layout()

    file_path = os.path.join(
        output_dir, "grade_distribution.png"
    )

    plt.savefig(file_path, dpi=150)
    plt.close()


def export_subject_average(summary, output_dir):
    """Export a chart showing average marks by subject."""

    plt.figure(figsize=(9, 5))

    plt.bar(
        summary["subject"],
        summary["average"]
    )

    plt.title("Subject-Wise Average Marks")
    plt.xlabel("Subject")
    plt.ylabel("Average Marks")
    plt.ylim(0, 100)
    plt.tight_layout()

    file_path = os.path.join(
        output_dir, "subject_average.png"
    )

    plt.savefig(file_path, dpi=150)
    plt.close()


def export_top_performers(cleaned, subject_columns, output_dir):
    """Export a chart showing the top ten students."""

    results = cleaned[
        ["enrollment", "name"] + subject_columns
    ].copy()

    results["average"] = results[subject_columns].mean(axis=1)

    top_students = results.sort_values(
        ["average", "enrollment"],
        ascending=[False, True]
    ).head(10)

    plt.figure(figsize=(10, 6))

    plt.barh(
        top_students["name"],
        top_students["average"]
    )

    plt.title("Top Student Performers")
    plt.xlabel("Average Marks")
    plt.ylabel("Student")
    plt.xlim(0, 100)

    plt.gca().invert_yaxis()
    plt.tight_layout()

    file_path = os.path.join(
        output_dir, "top_performers.png"
    )

    plt.savefig(file_path, dpi=150)
    plt.close()


def main():
    """Run the data-cleaning and visualization pipeline."""

    try:
        input_path = input(
            "Enter input CSV path: "
        ).strip()

        output_dir = input(
            "Enter output directory: "
        ).strip()

        if not input_path or not output_dir:
            raise ValueError(
                "Input path and output directory are required."
            )

        os.makedirs(output_dir, exist_ok=True)

        # Step 1: Load data.
        dataframe, subject_columns = load_dataset(input_path)

        # Step 2: Clean data.
        cleaned = clean_dataset(
            dataframe, subject_columns
        )

        # Step 3: Calculate summary statistics.
        summary = calculate_summary(
            cleaned, subject_columns
        )

        # Step 4: Save cleaned data and summary.
        cleaned_path = os.path.join(
            output_dir, "cleaned_marks.csv"
        )

        summary_path = os.path.join(
            output_dir, "summary.csv"
        )

        cleaned.to_csv(cleaned_path, index=False)
        summary.to_csv(summary_path, index=False)

        # Step 5: Export visualizations.
        export_grade_distribution(
            cleaned, subject_columns, output_dir
        )

        export_subject_average(
            summary, output_dir
        )

        export_top_performers(
            cleaned, subject_columns, output_dir
        )

        print("\nProcessing completed successfully.")

        print("Generated files:")

        for filename in [
            "cleaned_marks.csv",
            "summary.csv",
            "grade_distribution.png",
            "subject_average.png",
            "top_performers.png"
        ]:
            print(os.path.join(output_dir, filename))

    except (ValueError, FileNotFoundError, pd.errors.ParserError) as error:
        print(f"Input error: {error}", file=sys.stderr)

    except OSError as error:
        print(f"File system error: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()