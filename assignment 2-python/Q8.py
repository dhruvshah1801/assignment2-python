MOD = 1_000_000_007
BLOCKED = -1


def maximum_score_path(matrix, n, m):
    """
    Calculate the maximum path score and the number of paths
    achieving that score.

    Allowed movements:
    1. Right
    2. Down
    3. Diagonally down-right
    """

    # Unreachable cells have score None and zero paths.
    dp = [[None] * m for _ in range(n)]
    ways = [[0] * m for _ in range(n)]

    # The starting cell must not be blocked.
    if matrix[0][0] == BLOCKED:
        return None, 0

    dp[0][0] = matrix[0][0]
    ways[0][0] = 1

    for i in range(n):
        for j in range(m):

            # Skip the starting cell.
            if i == 0 and j == 0:
                continue

            # Blocked cells cannot be used.
            if matrix[i][j] == BLOCKED:
                continue

            best_score = None
            number_of_ways = 0

            # Previous cell from above.
            if i > 0 and dp[i - 1][j] is not None:
                best_score = dp[i - 1][j]
                number_of_ways = ways[i - 1][j]

            # Previous cell from the left.
            if j > 0 and dp[i][j - 1] is not None:
                candidate = dp[i][j - 1]

                if best_score is None or candidate > best_score:
                    best_score = candidate
                    number_of_ways = ways[i][j - 1]

                elif candidate == best_score:
                    number_of_ways = (
                        number_of_ways + ways[i][j - 1]
                    ) % MOD

            # Previous cell from diagonally above-left.
            if i > 0 and j > 0 and dp[i - 1][j - 1] is not None:
                candidate = dp[i - 1][j - 1]

                if best_score is None or candidate > best_score:
                    best_score = candidate
                    number_of_ways = ways[i - 1][j - 1]

                elif candidate == best_score:
                    number_of_ways = (
                        number_of_ways + ways[i - 1][j - 1]
                    ) % MOD

            # Store the best reachable score.
            if best_score is not None:
                dp[i][j] = best_score + matrix[i][j]
                ways[i][j] = number_of_ways

    # Check whether the destination is reachable.
    if dp[n - 1][m - 1] is None:
        return None, 0

    return dp[n - 1][m - 1], ways[n - 1][m - 1]


def main():
    """Read the matrix, validate input, and print the answer."""

    try:
        dimensions = input().split()

        if len(dimensions) != 2:
            raise ValueError("Enter n and m.")

        n, m = map(int, dimensions)

        if not (1 <= n <= 2000 and 1 <= m <= 2000):
            raise ValueError("n and m must be between 1 and 2000.")

        if n * m > 2_000_000:
            raise ValueError("Matrix contains too many cells.")

        matrix = []

        for _ in range(n):
            row = list(map(int, input().split()))

            if len(row) != m:
                raise ValueError(
                    f"Each row must contain exactly {m} values."
                )

            matrix.append(row)

        score, count = maximum_score_path(matrix, n, m)

        if score is None:
            print("IMPOSSIBLE")
        else:
            print(score, count)

    except ValueError as error:
        print(f"Input error: {error}")


if __name__ == "__main__":
    main()