import json
import mysql.connector
from mysql.connector import Error


# Only these tables and columns are allowed.
TABLES = {
    "student": {
        "student_id": "s.student_id",
        "name": "s.name",
        "spi": "s.spi"
    },
    "course": {
        "course_id": "c.course_id",
        "course_name": "c.course_name"
    },
    "courseregistration": {
        "student_id": "cr.student_id",
        "course_id": "cr.course_id"
    }
}

# Only approved columns may be selected or filtered.
ALLOWED_COLUMNS = {
    "student.student_id": "s.student_id",
    "student.name": "s.name",
    "student.spi": "s.spi",
    "course.course_id": "c.course_id",
    "course.course_name": "c.course_name",
    "courseregistration.student_id": "cr.student_id",
    "courseregistration.course_id": "cr.course_id"
}

OPERATORS = {"=", ">", "<", ">=", "<=", "LIKE", "!="}

ORDER_DIRECTIONS = {"ASC", "DESC"}


def build_query(request):
    """Validate the request and build a parameterized SQL query."""

    columns = request.get("columns", [])
    conditions = request.get("where", [])
    order = request.get("order", [])
    limit = request.get("limit", 10)

    if not isinstance(columns, list) or not columns:
        raise ValueError("At least one column must be selected.")

    if not isinstance(conditions, list):
        raise ValueError("WHERE conditions must be a list.")

    if not isinstance(order, list):
        raise ValueError("ORDER BY must be a list.")

    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError("LIMIT must be an integer.")

    if not 1 <= limit <= 1000:
        raise ValueError("LIMIT must be between 1 and 1000.")

    # Validate selected columns against the whitelist.
    selected_columns = []

    for column in columns:
        if not isinstance(column, str):
            raise ValueError("Column names must be strings.")

        key = column.lower()

        if key not in ALLOWED_COLUMNS:
            raise ValueError(f"Invalid column: {column}")

        selected_columns.append(ALLOWED_COLUMNS[key])

    # Determine the required tables.
    required_tables = set()

    for column in columns:
        required_tables.add(column.split(".")[0].lower())

    for condition in conditions:
        if not isinstance(condition, dict):
            raise ValueError("Each condition must be an object.")

        column = condition.get("column")

        if not isinstance(column, str):
            raise ValueError("Condition column must be a string.")

        key = column.lower()

        if key not in ALLOWED_COLUMNS:
            raise ValueError(f"Invalid condition column: {column}")

        operator = condition.get("operator")

        if not isinstance(operator, str):
            raise ValueError("Invalid operator.")

        operator = operator.upper()

        if operator not in OPERATORS:
            raise ValueError(f"Unsupported operator: {operator}")

        if "value" not in condition:
            raise ValueError("Each condition must contain a value.")

        required_tables.add(column.split(".")[0].lower())

    for item in order:
        if not isinstance(item, dict):
            raise ValueError("Each order item must be an object.")

        column = item.get("column")

        if not isinstance(column, str):
            raise ValueError("ORDER BY column must be a string.")

        if column.lower() not in ALLOWED_COLUMNS:
            raise ValueError(f"Invalid ORDER BY column: {column}")

        direction = item.get("direction", "ASC")

        if not isinstance(direction, str):
            raise ValueError("Sort direction must be a string.")

        if direction.upper() not in ORDER_DIRECTIONS:
            raise ValueError("Sort direction must be ASC or DESC.")

        required_tables.add(column.split(".")[0].lower())

    # Add the registration table when joining student and course.
    if "student" in required_tables and "course" in required_tables:
        required_tables.add("courseregistration")

    # Construct a fixed, safe FROM clause.
    if "courseregistration" in required_tables:
        from_clause = """
            Student AS s
            INNER JOIN CourseRegistration AS cr
                ON s.student_id = cr.student_id
            INNER JOIN Course AS c
                ON cr.course_id = c.course_id
        """

    elif "student" in required_tables:
        from_clause = "Student AS s"

    elif "course" in required_tables:
        from_clause = "Course AS c"

    else:
        raise ValueError("No valid table was selected.")

    # Build WHERE using placeholders.
    where_parts = []
    parameters = []

    for condition in conditions:
        column = ALLOWED_COLUMNS[condition["column"].lower()]
        operator = condition["operator"].upper()
        value = condition["value"]

        if operator == "LIKE" and not isinstance(value, str):
            raise ValueError("LIKE requires a string value.")

        if isinstance(value, (dict, list)):
            raise ValueError("Condition values must be simple values.")

        if operator == "LIKE":
            where_parts.append(f"{column} LIKE %s")
            parameters.append(value)

        else:
            where_parts.append(f"{column} {operator} %s")
            parameters.append(value)

    query = "SELECT " + ", ".join(selected_columns)
    query += " FROM " + " ".join(from_clause.split())

    if where_parts:
        query += " WHERE " + " AND ".join(where_parts)

    # Validate and construct ORDER BY.
    if order:
        order_parts = []

        for item in order:
            column = ALLOWED_COLUMNS[item["column"].lower()]
            direction = item.get("direction", "ASC").upper()

            order_parts.append(f"{column} {direction}")

        query += " ORDER BY " + ", ".join(order_parts)

    # LIMIT is validated as an integer.
    query += f" LIMIT {limit}"

    return query, parameters


def main():
    """Read a JSON request, execute the query, and display results."""

    database_config = {
        "host": "localhost",
        "user": "root",
        "password": "Dhruv1801@",
        "database": "student_analytics"
    }

    connection = None
    cursor = None

    try:
        print("Enter query request as JSON:")

        request_text = input().strip()
        request = json.loads(request_text)

        if not isinstance(request, dict):
            raise ValueError("The request must be a JSON object.")

        query, parameters = build_query(request)

        print("\nSQL_OK")
        print("SQL Template:")
        print(query)
        print("Parameters:", parameters)

        connection = mysql.connector.connect(**database_config)
        cursor = connection.cursor()

        # Parameterized execution protects filter values.
        cursor.execute(query, tuple(parameters))

        rows = cursor.fetchall()

        print("\nQuery Results:")

        for row in rows:
            print(row)

        if not rows:
            print("No matching records found.")

    except (ValueError, json.JSONDecodeError) as error:
        print(f"Invalid query request: {error}")

    except Error as error:
        print(f"MySQL error: {error}")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    main()