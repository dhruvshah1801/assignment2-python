import re
import sys
from collections import defaultdict


def extract_emails(file_path):
    """
    Extract unique valid email addresses from a text file.

    Returns:
        Dictionary containing email counts and smallest
        email address for each domain.
    """

    # Validate the input file.
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()
    except (OSError, UnicodeError) as error:
        print(f"Error reading input file: {error}")
        return None

    # Match common email formats with the required domains.
    email_pattern = re.compile(
        r"(?<![A-Za-z0-9.!#$%&'*+/=?^_`{|}~@-])"
        r"([A-Za-z0-9_+-][A-Za-z0-9._+-]*"
        r"@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
        r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*"
        r"\.(?:com|edu|org))"
        r"(?![A-Za-z0-9._%+-])",
        re.IGNORECASE
    )

    # A set removes duplicate email addresses.
    unique_emails = {
        match.group(1).lower()
        for match in email_pattern.finditer(text)
    }

    domain_emails = defaultdict(set)

    # Group email addresses by their top-level domain.
    for email in unique_emails:
        domain = email.rsplit(".", 1)[-1]
        domain_emails[domain].add(email)

    results = {}

    # Process domains in lexicographical order.
    for domain in sorted(domain_emails):
        emails = domain_emails[domain]

        results[domain] = {
            "count": len(emails),
            "smallest_email": min(emails)
        }

    return results


def main():
    """Read input and display email statistics."""

    if len(sys.argv) != 2:
        print("Usage: python Enrollment_Assignment2_Q1.py <text_file>")
        return

    results = extract_emails(sys.argv[1])

    if results is None:
        return

    for domain, details in results.items():
        print(
            f"{domain} {details['count']} "
            f"{details['smallest_email']}"
        )


if __name__ == "__main__":
    main()