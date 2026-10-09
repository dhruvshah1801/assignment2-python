from collections import defaultdict, deque
from datetime import datetime
import sys


def parse_timestamp(timestamp):
    """Convert HH:MM:SS into seconds since midnight."""

    try:
        parsed = datetime.strptime(timestamp, "%H:%M:%S")

        return (
            parsed.hour * 3600
            + parsed.minute * 60
            + parsed.second
        )

    except ValueError as error:
        raise ValueError(
            f"Invalid timestamp: {timestamp}"
        ) from error


def detect_anomalies(logs, x, t):
    """
    Detect successful logins preceded by at least X failures
    within T minutes, from a different IP address.
    """

    # Store failed logins separately for each user.
    failures = defaultdict(deque)

    # Record the first suspicious success for each user.
    suspicious_users = {}

    window_seconds = t * 60

    # Process logs in chronological order.
    logs.sort(key=lambda record: record[0])

    for timestamp, user, ip, status in logs:

        user_failures = failures[user]

        # Remove failures outside the sliding window.
        while (
            user_failures
            and timestamp - user_failures[0][0] > window_seconds
        ):
            user_failures.popleft()

        if status == "FAIL":
            user_failures.append((timestamp, ip))

        elif status == "SUCCESS":

            # A suspicious success must follow enough failures
            # and originate from an IP different from a failure.
            different_ip_failures = [
                failure_ip
                for _, failure_ip in user_failures
                if failure_ip != ip
            ]

            if (
                len(user_failures) >= x
                and different_ip_failures
                and user not in suspicious_users
            ):
                suspicious_users[user] = timestamp

    return suspicious_users


def format_timestamp(seconds):
    """Convert seconds back to HH:MM:SS."""

    hours = (seconds // 3600) % 24
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def main():
    """Read log records and print suspicious users."""

    try:
        first_line = input().split()

        if len(first_line) != 2:
            raise ValueError("First line must contain X and T.")

        x, t = map(int, first_line)

        if not 1 <= x <= 100:
            raise ValueError("X must be between 1 and 100.")

        if not 1 <= t <= 1440:
            raise ValueError("T must be between 1 and 1440.")

        n = int(input())

        if not 0 <= n <= 200000:
            raise ValueError("Invalid number of log records.")

        logs = []

        for _ in range(n):
            parts = input().split()

            if len(parts) != 4:
                raise ValueError(
                    "Each log must contain timestamp, user, IP, status."
                )

            timestamp_text, user, ip, status = parts

            if not user or not ip:
                raise ValueError("User and IP cannot be empty.")

            status = status.upper()

            if status not in {"FAIL", "SUCCESS"}:
                raise ValueError(
                    "Status must be FAIL or SUCCESS."
                )

            timestamp = parse_timestamp(timestamp_text)

            logs.append(
                (timestamp, user, ip, status)
            )

        suspicious = detect_anomalies(logs, x, t)

        for user in sorted(suspicious):
            print(
                f"{user} {format_timestamp(suspicious[user])}"
            )

    except (ValueError, EOFError) as error:
        print(f"Input error: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()