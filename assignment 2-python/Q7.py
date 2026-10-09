import json
import math
import sys
from collections import defaultdict


def read_json_lines(file_path):
    """
    Generator that reads one JSON record at a time.

    Yields:
        Line number and parsed JSON data.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):

            if not line.strip():
                continue

            try:
                record = json.loads(line)

                if not isinstance(record, dict):
                    yield line_number, None, "Record must be a JSON object."
                    continue

                yield line_number, record, None

            except json.JSONDecodeError:
                yield line_number, None, "Invalid JSON."


def transform_record(record):
    """
    Validate and transform a sensor record.

    Returns a normalized record or raises ValueError.
    """

    required_fields = {
        "device_id",
        "timestamp",
        "temperature_c",
        "humidity"
    }

    if not required_fields.issubset(record):
        raise ValueError("Missing required fields.")

    device_id = record["device_id"]
    timestamp = record["timestamp"]

    if not isinstance(device_id, str) or not device_id.strip():
        raise ValueError("Invalid device ID.")

    if not isinstance(timestamp, str) or not timestamp.strip():
        raise ValueError("Invalid timestamp.")

    temperature = record["temperature_c"]
    humidity = record["humidity"]

    # Reject booleans, strings, and non-numeric values.
    if (
        isinstance(temperature, bool)
        or not isinstance(temperature, (int, float))
        or not math.isfinite(temperature)
    ):
        raise ValueError("Temperature must be a finite number.")

    if (
        isinstance(humidity, bool)
        or not isinstance(humidity, (int, float))
        or not math.isfinite(humidity)
    ):
        raise ValueError("Humidity must be a finite number.")

    if not 0 <= humidity <= 100:
        raise ValueError("Humidity must be between 0 and 100.")

    return {
        "device_id": device_id.strip(),
        "timestamp": timestamp.strip(),
        "temperature_c": float(temperature),
        "humidity": float(humidity)
    }


def process_records(file_path):
    """
    Generator-based ETL pipeline.

    Yields:
        Valid transformed records.
    """

    for line_number, record, error in read_json_lines(file_path):

        if error:
            print(
                f"Corrupted record at line {line_number}: {error}",
                file=sys.stderr
            )
            continue

        try:
            yield transform_record(record)

        except ValueError as error:
            print(
                f"Corrupted record at line {line_number}: {error}",
                file=sys.stderr
            )


def aggregate_records(file_path):
    """Aggregate temperature statistics by device."""

    statistics = defaultdict(
        lambda: {
            "count": 0,
            "min": None,
            "max": None,
            "sum": 0.0,
            "corrupted": 0
        }
    )

    # Count corrupted records for devices whose IDs are available.
    for line_number, record, error in read_json_lines(file_path):

        device_id = None

        if isinstance(record, dict):
            value = record.get("device_id")

            if isinstance(value, str) and value.strip():
                device_id = value.strip()

        if error:
            device_id = device_id or "UNKNOWN"
            statistics[device_id]["corrupted"] += 1
            continue

        try:
            transformed = transform_record(record)

        except ValueError as error:
            device_id = device_id or "UNKNOWN"
            statistics[device_id]["corrupted"] += 1

            print(
                f"Corrupted record at line {line_number}: {error}",
                file=sys.stderr
            )
            continue

        device_id = transformed["device_id"]
        temperature = transformed["temperature_c"]

        item = statistics[device_id]

        item["count"] += 1
        item["sum"] += temperature

        if item["min"] is None or temperature < item["min"]:
            item["min"] = temperature

        if item["max"] is None or temperature > item["max"]:
            item["max"] = temperature

    return statistics


def display_statistics(statistics):
    """Display the aggregated statistics in sorted order."""

    print(
        "Device ID | Count | Min Temp | Max Temp | "
        "Avg Temp | Corrupted"
    )

    print("-" * 72)

    for device_id in sorted(statistics):

        item = statistics[device_id]
        count = item["count"]

        if count:
            average = item["sum"] / count

            print(
                f"{device_id} | {count} | "
                f"{item['min']:.2f} | "
                f"{item['max']:.2f} | "
                f"{average:.2f} | "
                f"{item['corrupted']}"
            )

        else:
            print(
                f"{device_id} | 0 | N/A | N/A | N/A | "
                f"{item['corrupted']}"
            )


def main():
    """Run the generator-based sensor ETL pipeline."""

    file_path = input(
        "Enter JSON Lines file path: "
    ).strip()

    if not file_path:
        print("File path cannot be empty.")
        return

    try:
        statistics = aggregate_records(file_path)
        display_statistics(statistics)

    except OSError as error:
        print(f"File error: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()