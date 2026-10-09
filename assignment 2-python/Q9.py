class Product:
    """Represent an individual inventory product."""

    def __init__(self, name, stock, purchase_price, selling_price):
        self.name = name
        self.stock = stock
        self.purchase_price = purchase_price
        self.selling_price = selling_price

    def __repr__(self):
        return (
            f"{self.name} stock={self.stock} "
            f"purchase={self.purchase_price} "
            f"selling={self.selling_price}"
        )


class Inventory:
    """Manage products and support inventory operations."""

    def __init__(self):
        self.products = {}

    def add_product(self, product):
        """Add a new product without overwriting existing stock."""

        if product.name in self.products:
            raise ValueError(
                f"Product '{product.name}' already exists."
            )

        self.products[product.name] = product

    def delete_product(self, name):
        """Delete a product by name."""

        if name not in self.products:
            raise ValueError(f"Product '{name}' does not exist.")

        del self.products[name]

    def update_stock(self, name, quantity):
        """Increase or decrease the stock quantity."""

        if name not in self.products:
            raise ValueError(f"Product '{name}' does not exist.")

        new_stock = self.products[name].stock + quantity

        if new_stock < 0:
            raise ValueError("Stock cannot become negative.")

        self.products[name].stock = new_stock

    def total_value(self):
        """Calculate total inventory value using purchase prices."""

        return sum(
            product.stock * product.purchase_price
            for product in self.products.values()
        )

    def __add__(self, other):
        """
        Merge two inventories.

        For products with the same name:
        - Add stock quantities.
        - Keep the minimum purchase price.
        - Keep the maximum selling price.
        """

        if not isinstance(other, Inventory):
            return NotImplemented

        merged = Inventory()

        # Copy products from the first inventory.
        for name, product in self.products.items():
            merged.products[name] = Product(
                product.name,
                product.stock,
                product.purchase_price,
                product.selling_price
            )

        # Merge products from the second inventory.
        for name, product in other.products.items():

            if name not in merged.products:
                merged.products[name] = Product(
                    product.name,
                    product.stock,
                    product.purchase_price,
                    product.selling_price
                )

            else:
                existing = merged.products[name]

                existing.stock += product.stock

                existing.purchase_price = min(
                    existing.purchase_price,
                    product.purchase_price
                )

                existing.selling_price = max(
                    existing.selling_price,
                    product.selling_price
                )

        return merged

    def __lt__(self, other):
        """Compare inventories by total purchase value."""

        if not isinstance(other, Inventory):
            return NotImplemented

        return self.total_value() < other.total_value()

    def __repr__(self):
        return "\n".join(
            repr(self.products[name])
            for name in sorted(self.products)
        )


def read_inventory():
    """Read product details and construct an inventory."""

    inventory = Inventory()

    count = int(input("Number of products: "))

    if not 0 <= count <= 500000:
        raise ValueError("Invalid number of products.")

    for _ in range(count):
        parts = input().split()

        if len(parts) != 4:
            raise ValueError(
                "Enter: name stock purchase_price selling_price"
            )

        name = parts[0]
        stock = int(parts[1])
        purchase_price = int(parts[2])
        selling_price = int(parts[3])

        if stock < 0:
            raise ValueError("Stock cannot be negative.")

        if purchase_price < 0 or selling_price < 0:
            raise ValueError("Prices cannot be negative.")

        if selling_price < purchase_price:
            raise ValueError(
                "Selling price cannot be less than purchase price."
            )

        inventory.add_product(
            Product(name, stock, purchase_price, selling_price)
        )

    return inventory


def main():
    """Read inventories and perform the selected operation."""

    try:
        print("Inventory A:")
        inventory_a = read_inventory()

        print("Inventory B:")
        inventory_b = read_inventory()

        operation = input(
            "Operation (MERGE or COMPARE): "
        ).strip().upper()

        if operation == "MERGE":
            merged = inventory_a + inventory_b

            print("Merged Inventory:")

            for name in sorted(merged.products):
                print(merged.products[name])

            print("Total Inventory Value:", merged.total_value())

        elif operation == "COMPARE":
            value_a = inventory_a.total_value()
            value_b = inventory_b.total_value()

            print("Inventory A Value:", value_a)
            print("Inventory B Value:", value_b)

            if value_a > value_b:
                print("Inventory A has greater value.")
            elif value_b > value_a:
                print("Inventory B has greater value.")
            else:
                print("Both inventories have equal value.")

        else:
            raise ValueError("Operation must be MERGE or COMPARE.")

    except ValueError as error:
        print("Input error:", error)


if __name__ == "__main__":
    main()