import re
import tkinter as tk
from tkinter import ttk, messagebox

import mysql.connector
from mysql.connector import Error


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Dhruv1801@",
    "database": "contact_manager"
}


def validate_email(email):
    """Check whether the email address has a valid basic format."""

    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return bool(re.fullmatch(pattern, email))


def validate_phone(phone):
    """Validate a phone number containing 7 to 15 digits."""

    return bool(re.fullmatch(r"\+?[0-9]{7,15}", phone))


class ContactManager:
    """Tkinter contact manager backed by MySQL."""

    def __init__(self, root):
        self.root = root
        self.root.title("Contact Manager")
        self.root.geometry("950x600")

        self.connection = None

        self.create_connection()

        if self.connection is None:
            self.root.after(100, self.root.destroy)
            return

        self.create_table()
        self.create_widgets()
        self.load_contacts()

        self.root.protocol("WM_DELETE_WINDOW", self.close_application)

    def create_connection(self):
        """Connect to the MySQL database."""

        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)

            if not self.connection.is_connected():
                raise Error("Unable to connect to MySQL.")

        except Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not connect to MySQL:\n{error}"
            )
            self.connection = None

    def create_table(self):
        """Create the contacts table."""

        cursor = self.connection.cursor()

        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Contact (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(254) NOT NULL UNIQUE,
                    phone VARCHAR(16) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    notes TEXT
                )
            """)

            cursor.execute("""
                CREATE INDEX idx_contact_name
                ON Contact(name)
            """)

            cursor.execute("""
                CREATE INDEX idx_contact_phone
                ON Contact(phone)
            """)

            self.connection.commit()

        except Error as error:
            self.connection.rollback()
            messagebox.showerror("Database Error", str(error))

        finally:
            cursor.close()

    def create_widgets(self):
        """Create the contact form, buttons, and results table."""

        form = ttk.LabelFrame(self.root, text="Contact Details")
        form.pack(fill="x", padx=10, pady=10)

        self.entries = {}

        fields = [
            ("Name", "name"),
            ("Email", "email"),
            ("Phone", "phone"),
            ("Category", "category"),
            ("Notes", "notes")
        ]

        for index, (label, key) in enumerate(fields):
            ttk.Label(form, text=label).grid(
                row=index, column=0, padx=5, pady=4, sticky="w"
            )

            entry = ttk.Entry(form, width=45)
            entry.grid(row=index, column=1, padx=5, pady=4, sticky="w")

            self.entries[key] = entry

        self.entries["category"].insert(0, "Personal")

        button_frame = ttk.Frame(form)
        button_frame.grid(
            row=0, column=2, rowspan=5, padx=15, pady=5
        )

        ttk.Button(
            button_frame, text="Add Contact",
            command=self.add_contact
        ).pack(fill="x", pady=4)

        ttk.Button(
            button_frame, text="Update Contact",
            command=self.update_contact
        ).pack(fill="x", pady=4)

        ttk.Button(
            button_frame, text="Delete Contact",
            command=self.delete_contact
        ).pack(fill="x", pady=4)

        ttk.Button(
            button_frame, text="Clear Form",
            command=self.clear_form
        ).pack(fill="x", pady=4)

        search_frame = ttk.Frame(self.root)
        search_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(search_frame, text="Search:").pack(side="left")

        self.search_entry = ttk.Entry(search_frame, width=35)
        self.search_entry.pack(side="left", padx=5)

        self.search_field = tk.StringVar(value="name")

        ttk.Combobox(
            search_frame,
            textvariable=self.search_field,
            values=["name", "email", "phone"],
            state="readonly",
            width=10
        ).pack(side="left", padx=5)

        ttk.Button(
            search_frame, text="Search",
            command=self.search_contacts
        ).pack(side="left", padx=5)

        ttk.Button(
            search_frame, text="Show All",
            command=self.load_contacts
        ).pack(side="left", padx=5)

        columns = (
            "id", "name", "email",
            "phone", "category", "notes"
        )

        self.tree = ttk.Treeview(
            self.root,
            columns=columns,
            show="headings",
            height=15
        )

        for column in columns:
            self.tree.heading(
                column, text=column.title()
            )
            self.tree.column(column, width=130)

        self.tree.column("id", width=50)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.select_contact
        )

    def get_form_data(self):
        """Read and validate contact details."""

        data = {
            key: entry.get().strip()
            for key, entry in self.entries.items()
        }

        if not data["name"]:
            raise ValueError("Name is required.")

        if not validate_email(data["email"]):
            raise ValueError("Enter a valid email address.")

        if not validate_phone(data["phone"]):
            raise ValueError(
                "Phone must contain 7 to 15 digits, "
                "optionally starting with +."
            )

        if not data["category"]:
            raise ValueError("Category is required.")

        return data

    def execute_write(self, query, values):
        """Execute a database write safely."""

        cursor = self.connection.cursor()

        try:
            cursor.execute(query, values)
            self.connection.commit()
            return cursor.lastrowid

        except Error:
            self.connection.rollback()
            raise

        finally:
            cursor.close()

    def add_contact(self):
        """Insert a new contact."""

        try:
            data = self.get_form_data()

            self.execute_write("""
                INSERT INTO Contact
                    (name, email, phone, category, notes)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                data["name"],
                data["email"],
                data["phone"],
                data["category"],
                data["notes"]
            ))

            messagebox.showinfo(
                "Success", "Contact added successfully."
            )

            self.clear_form()
            self.load_contacts()

        except ValueError as error:
            messagebox.showwarning("Invalid Input", str(error))

        except Error as error:
            if error.errno == 1062:
                messagebox.showwarning(
                    "Duplicate Email",
                    "This email address already exists."
                )
            else:
                messagebox.showerror("Database Error", str(error))

    def update_contact(self):
        """Update the selected contact."""

        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "Selection Required",
                "Select a contact to update."
            )
            return

        try:
            data = self.get_form_data()
            contact_id = self.tree.item(selected[0])["values"][0]

            self.execute_write("""
                UPDATE Contact
                SET name = %s, email = %s, phone = %s,
                    category = %s, notes = %s
                WHERE id = %s
            """, (
                data["name"],
                data["email"],
                data["phone"],
                data["category"],
                data["notes"],
                contact_id
            ))

            messagebox.showinfo(
                "Success", "Contact updated successfully."
            )

            self.load_contacts()

        except ValueError as error:
            messagebox.showwarning("Invalid Input", str(error))

        except Error as error:
            if error.errno == 1062:
                messagebox.showwarning(
                    "Duplicate Email",
                    "This email address belongs to another contact."
                )
            else:
                messagebox.showerror("Database Error", str(error))

    def delete_contact(self):
        """Delete the selected contact."""

        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "Selection Required",
                "Select a contact to delete."
            )
            return

        if not messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this contact?"
        ):
            return

        contact_id = self.tree.item(selected[0])["values"][0]

        try:
            self.execute_write(
                "DELETE FROM Contact WHERE id = %s",
                (contact_id,)
            )

            self.clear_form()
            self.load_contacts()

            messagebox.showinfo(
                "Success", "Contact deleted successfully."
            )

        except Error as error:
            messagebox.showerror("Database Error", str(error))

    def display_rows(self, rows):
        """Display database records in the table."""

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in rows:
            self.tree.insert("", "end", values=row)

    def load_contacts(self):
        """Load all contacts in alphabetical order."""

        cursor = self.connection.cursor()

        try:
            cursor.execute("""
                SELECT id, name, email, phone, category, notes
                FROM Contact
                ORDER BY name ASC, id ASC
            """)

            self.display_rows(cursor.fetchall())

        except Error as error:
            messagebox.showerror("Database Error", str(error))

        finally:
            cursor.close()

    def search_contacts(self):
        """Search contacts by name, email, or phone."""

        keyword = self.search_entry.get().strip()

        if not keyword:
            self.load_contacts()
            return

        allowed_fields = {
            "name": "name",
            "email": "email",
            "phone": "phone"
        }

        field = allowed_fields.get(self.search_field.get())

        if field is None:
            messagebox.showerror(
                "Invalid Search", "Unsupported search field."
            )
            return

        cursor = self.connection.cursor()

        try:
            query = f"""
                SELECT id, name, email, phone, category, notes
                FROM Contact
                WHERE {field} LIKE %s
                ORDER BY name ASC, id ASC
            """

            cursor.execute(query, (f"%{keyword}%",))
            self.display_rows(cursor.fetchall())

        except Error as error:
            messagebox.showerror("Database Error", str(error))

        finally:
            cursor.close()

    def select_contact(self, event=None):
        """Fill the form when a table row is selected."""

        selected = self.tree.selection()

        if not selected:
            return

        values = self.tree.item(selected[0])["values"]

        keys = [
            "name", "email", "phone",
            "category", "notes"
        ]

        for index, key in enumerate(keys, start=1):
            self.entries[key].delete(0, tk.END)

            if values[index] is not None:
                self.entries[key].insert(0, str(values[index]))

    def clear_form(self):
        """Clear all contact fields."""

        for entry in self.entries.values():
            entry.delete(0, tk.END)

        self.entries["category"].insert(0, "Personal")

    def close_application(self):
        """Close the database connection and GUI."""

        if self.connection and self.connection.is_connected():
            self.connection.close()

        self.root.destroy()


def main():
    """Start the contact management application."""

    root = tk.Tk()
    ContactManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()