import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class ProductHTMLParser(HTMLParser):
    """Extract product information from saved HTML pages."""

    def __init__(self):
        super().__init__(convert_charrefs=True)

        self.products = []
        self.current_product = None
        self.current_field = None
        self.current_depth = 0

    @staticmethod
    def get_field(attributes):
        """Identify whether an HTML element represents a field."""

        attrs = dict(attributes)

        # Check common data attributes.
        if attrs.get("itemprop") in ("name", "price", "ratingValue"):
            return {
                "name": "name",
                "price": "price",
                "ratingValue": "rating"
            }[attrs["itemprop"]]

        # Check class and id names.
        label = (
            attrs.get("class", "") + " " +
            attrs.get("id", "")
        ).lower()

        if re.search(r"product[-_ ]?name|item[-_ ]?name", label):
            return "name"

        if re.search(r"price|amount", label):
            return "price"

        if re.search(r"rating|stars", label):
            return "rating"

        return None

    def handle_starttag(self, tag, attrs):
        """Process the beginning of an HTML element."""

        attrs_dict = dict(attrs)
        classes = attrs_dict.get("class", "").lower()

        # Start a new product card.
        if self.current_product is None and re.search(
            r"(^|\s)product(?:\s|$|-|_)", classes
        ):
            self.current_product = {
                "name": "",
                "price": "",
                "rating": ""
            }
            self.current_depth = 1
            return

        if self.current_product is not None:
            self.current_depth += 1

            field = self.get_field(attrs)

            if field:
                self.current_field = field

            # Support common structured price/rating attributes.
            if attrs_dict.get("itemprop") == "price":
                self.current_product["price"] = (
                    attrs_dict.get("content", "")
                    or self.current_product["price"]
                )

            if attrs_dict.get("itemprop") == "ratingValue":
                self.current_product["rating"] = (
                    attrs_dict.get("content", "")
                    or self.current_product["rating"]
                )

    def handle_data(self, data):
        """Collect text belonging to product fields."""

        if self.current_product is not None and self.current_field:
            self.current_product[self.current_field] += data.strip()

    def handle_endtag(self, tag):
        """Finish a product card when its outer element closes."""

        if self.current_product is None:
            return

        self.current_depth -= 1

        if self.current_depth <= 0:
            product = self.current_product

            if (
                product["name"].strip()
                and product["price"].strip()
                and product["rating"].strip()
            ):
                self.products.append({
                    "name": product["name"].strip(),
                    "price": product["price"].strip(),
                    "rating": product["rating"].strip()
                })

            self.current_product = None
            self.current_field = None
            self.current_depth = 0


def normalize_price(price_text):
    """Convert a price string into a numeric value."""

    cleaned = re.sub(r"[^0-9.]", "", price_text)

    if not cleaned:
        raise ValueError("Missing product price")

    value = float(cleaned)

    if value < 0:
        raise ValueError("Price cannot be negative")

    return value


def normalize_rating(rating_text):
    """Convert rating text into a number between 0 and 5."""

    match = re.search(r"\d+(?:\.\d+)?", rating_text)

    if not match:
        raise ValueError("Invalid product rating")

    rating = float(match.group())

    if not 0 <= rating <= 5:
        raise ValueError("Rating must be between 0 and 5")

    return rating


def scrape_products(file_path):
    """Read one HTML file and extract its products."""

    try:
        html = Path(file_path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        print(f"Cannot read {file_path}: {error}", file=sys.stderr)
        return []

    parser = ProductHTMLParser()

    try:
        parser.feed(html)
        parser.close()
    except Exception as error:
        print(f"HTML parsing error in {file_path}: {error}",
              file=sys.stderr)
        return []

    valid_products = []

    for product in parser.products:
        try:
            valid_products.append({
                "name": product["name"].strip(),
                "price": normalize_price(product["price"]),
                "rating": normalize_rating(product["rating"])
            })
        except ValueError as error:
            print(
                f"Skipping invalid product in {file_path}: {error}",
                file=sys.stderr
            )

    return valid_products


def rank_products(file_paths, k):
    """Deduplicate products and return the top K ranked products."""

    unique_products = {}

    for file_path in file_paths:
        for product in scrape_products(file_path):
            # Use case-insensitive names to identify duplicates.
            key = product["name"].casefold()

            # Retain the best-ranked version of each product.
            existing = unique_products.get(key)

            if existing is None:
                unique_products[key] = product
            else:
                new_rank = (
                    -product["rating"],
                    product["price"],
                    product["name"].casefold()
                )

                old_rank = (
                    -existing["rating"],
                    existing["price"],
                    existing["name"].casefold()
                )

                if new_rank < old_rank:
                    unique_products[key] = product

    # Highest rating first, then lowest price, then name.
    ranked = sorted(
        unique_products.values(),
        key=lambda product: (
            -product["rating"],
            product["price"],
            product["name"].casefold()
        )
    )

    return ranked[:k]


def main():
    """Read the number of files, file paths, and K."""

    try:
        number_of_files = int(input("Enter number of HTML files: "))

        if number_of_files < 1:
            raise ValueError("At least one HTML file is required.")

        file_paths = []

        for index in range(number_of_files):
            file_paths.append(
                input(f"Enter path of HTML file {index + 1}: ").strip()
            )

        k = int(input("Enter K: "))

        if k < 1:
            raise ValueError("K must be at least 1.")

    except ValueError as error:
        print(f"Invalid input: {error}")
        return

    products = rank_products(file_paths, k)

    if not products:
        print("No valid products found.")
        return

    for product in products:
        price = (
            str(int(product["price"]))
            if product["price"].is_integer()
            else str(product["price"])
        )

        print(
            f"{product['name']} {price} {product['rating']:.1f}"
        )


if __name__ == "__main__":
    main()