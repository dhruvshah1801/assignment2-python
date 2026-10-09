import csv
import sys
from decimal import Decimal, InvalidOperation

import mysql.connector
from mysql.connector import Error


def read_student_csv(file_path):
    """Read and validate student records from CSV."""

    students = []

    with open(file_path, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        required_columns = {"student_id", "name", "spi"}

        if not reader.fieldnames or not required_columns.issubset(
            reader.fieldnames
        ):
            raise ValueError(
                "student.csv must contain student_id, name, and spi."
            )

        for line_number, row in enumerate(reader, start=2):
            try:
                student_id = int(row["student_id"])
                name = row["name"].strip()
                spi = Decimal(row["spi"].strip())

                if student_id <= 0:
                    raise ValueError("Student ID must be positive.")

                if not name:
                    raise ValueError("Student name cannot be empty.")

                if not spi.is_finite() or not Decimal("0") <= spi <= Decimal("10"):
                    raise ValueError("SPI must be between 0 and 10.")

                students.append((student_id, name, spi))

            except (ValueError, InvalidOperation, AttributeError) as error:
                raise ValueError(
                    f"Invalid student record at line {line_number}: {error}"
                ) from error

    return students


def read_registration_csv(file_path):
    """Read and validate course registrations from CSV."""

    registrations = []

    with open(file_path, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        required_columns = {"student_id", "course_id"}

        if not reader.fieldnames or not required_columns.issubset(
            reader.fieldnames
        ):
            raise ValueError(
                "registration.csv must contain student_id and course_id."
            )

        for line_number, row in enumerate(reader, start=2):
            try:
                student_id = int(row["student_id"])
                course_id = row["course_id"].strip()

                if student_id <= 0:
                    raise ValueError("Student ID must be positive.")

                if not course_id:
                    raise ValueError("Course ID cannot be empty.")

                registrations.append((student_id, course_id))

            except (ValueError, AttributeError) as error:
                raise ValueError(
                    f"Invalid registration at line {line_number}: {error}"
                ) from error

    return registrations


def create_tables(connection):
    """Create the required tables if they do not exist."""

    cursor = connection.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Student (
                student_id INT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                spi DECIMAL(3,1) NOT NULL,
                CHECK (spi >= 0 AND spi <= 10)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS CourseRegistration (
                student_id INT NOT NULL,
                course_id VARCHAR(30) NOT NULL,
                PRIMARY KEY (student_id, course_id),
                FOREIGN KEY (student_id)
                    REFERENCES Student(student_id)
            )
        """)

        # Supports filtering by course and ordering by student SPI.
        cursor.execute("""
            CREATE INDEX idx_registration_course
            ON CourseRegistration(course_id)
        """)

        connection.commit()

    except Error:
        connection.rollback()
        raise

    finally:
        cursor.close()


def insert_students(connection, students):
    """Insert student records without duplicating existing IDs."""

    cursor = connection.cursor()

    try:
        query = """
            INSERT INTO Student (student_id, name, spi)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                spi = VALUES(spi)
        """

        cursor.executemany(query, students)
        connection.commit()

    except Error:
        connection.rollback()
        raise

    finally:
        cursor.close()


def insert_registrations(connection, registrations):
    """Insert registrations without duplicating existing records."""

    cursor = connection.cursor()

    try:
        query = """
            INSERT INTO CourseRegistration (student_id, course_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                course_id = VALUES(course_id)
        """

        cursor.executemany(query, registrations)
        connection.commit()

    except Error:
        connection.rollback()
        raise

    finally:
        cursor.close()


def fetch_course_students(connection, course_id, spi_threshold):
    """
    Return students registered for the specified course
    whose SPI is strictly greater than the threshold.
    """

    cursor = connection.cursor()

    try:
        query = """
            SELECT
                s.student_id,
                s.name,
                s.spi,
                cr.course_id
            FROM Student AS s
            INNER JOIN CourseRegistration AS cr
                ON s.student_id = cr.student_id
            WHERE cr.course_id = %s
              AND s.spi > %s
            ORDER BY s.spi DESC, s.student_id ASC
        """

        # Parameterized query prevents SQL injection.
        cursor.execute(query, (course_id, spi_threshold))

        return cursor.fetchall()

    finally:
        cursor.close()


def main():
    """Connect to MySQL and execute the analytics workflow."""

    # Replace these values with your own MySQL credentials.
    database_config = {
        "host": "localhost",
        "user": "root",
        "password": "Dhruv1801@",
        "database": "student_analytics"
    }

    connection = None

    try:
        # Validate CSV files before connecting to the database.
        student_file = "student.csv"
        registration_file = "registration.csv"

        students = read_student_csv(student_file)
        registrations = read_registration_csv(registration_file)

        course_id = input("Enter course ID: ").strip()

        if not course_id:
            raise ValueError("Course ID cannot be empty.")

        spi_threshold = Decimal(
            input("Enter SPI threshold: ").strip()
        )

        if (
            not spi_threshold.is_finite()
            or not Decimal("0") <= spi_threshold <= Decimal("10")
        ):
            raise ValueError("SPI threshold must be between 0 and 10.")

        connection = mysql.connector.connect(**database_config)

        if not connection.is_connected():
            print("Could not connect to MySQL.")
            return

        print("Connected to MySQL successfully.")

        create_tables(connection)

        insert_students(connection, students)

        insert_registrations(connection, registrations)

        results = fetch_course_students(
            connection,
            course_id,
            spi_threshold
        )

        print("\nStudent ID | Name | SPI | Course ID")
        print("-" * 42)

        if not results:
            print("No matching students found.")
        else:
            for student_id, name, spi, result_course_id in results:
                print(
                    f"{student_id} | {name} | "
                    f"{spi} | {result_course_id}"
                )

    except (OSError, ValueError, InvalidOperation) as error:
        print(f"Input error: {error}")

    except Error as error:
        print(f"MySQL database error: {error}")

    finally:
        if connection is not None and connection.is_connected():
            connection.close()
            print("\nMySQL connection closed.")


if __name__ == "__main__":
    main()