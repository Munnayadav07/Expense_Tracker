"""A small, menu-driven expense tracker backed by a CSV file."""

import csv
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


CSV_FIELDS = ("id", "date", "category", "description", "amount")
DEFAULT_DATA_FILE = Path(__file__).resolve().parent / "data" / "expenses.csv"


@dataclass(frozen=True)
class Expense:
    """One expense record."""

    id: int
    date: date
    category: str
    description: str
    amount: Decimal


class ExpenseTracker:
    """Read and write expense records in a CSV file."""

    def __init__(self, csv_path: Path = DEFAULT_DATA_FILE) -> None:
        self.csv_path = Path(csv_path)

    def _read_expenses(self) -> list[Expense]:
        """Load and validate every row so corrupt data is reported clearly."""
        if not self.csv_path.exists():
            return []

        try:
            with self.csv_path.open("r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                if reader.fieldnames != list(CSV_FIELDS):
                    raise ValueError(
                        f"CSV must have these columns in order: {', '.join(CSV_FIELDS)}."
                    )

                expenses = []
                seen_ids = set()
                for line_number, row in enumerate(reader, start=2):
                    if None in row or any(row.get(field) is None for field in CSV_FIELDS):
                        raise ValueError(f"CSV row {line_number} has an invalid number of columns.")
                    try:
                        expense = Expense(
                            id=int(row["id"]),
                            date=date.fromisoformat(row["date"]),
                            category=row["category"].strip(),
                            description=row["description"].strip(),
                            amount=self._parse_amount(row["amount"]),
                        )
                    except (TypeError, ValueError) as error:
                        raise ValueError(f"CSV row {line_number} is invalid: {error}") from error
                    if expense.id <= 0 or expense.id in seen_ids:
                        raise ValueError(f"CSV row {line_number} has a duplicate or invalid ID.")
                    if not expense.category or not expense.description:
                        raise ValueError(f"CSV row {line_number} has an empty category or description.")
                    seen_ids.add(expense.id)
                    expenses.append(expense)
                return expenses
        except csv.Error as error:
            raise ValueError(f"Could not parse CSV file: {error}") from error

    @staticmethod
    def _parse_amount(value: str) -> Decimal:
        """Parse a positive monetary amount with no more than two decimal places."""
        try:
            amount = Decimal(value.strip())
        except (InvalidOperation, AttributeError) as error:
            raise ValueError("Amount must be a valid number.") from error
        if not amount.is_finite() or amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        if amount.as_tuple().exponent < -2:
            raise ValueError("Amount cannot have more than two decimal places.")
        return amount

    def _write_expenses(self, expenses: list[Expense]) -> None:
        """Write all records, creating the parent data directory if needed."""
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for expense in expenses:
                writer.writerow(
                    {
                        "id": expense.id,
                        "date": expense.date.isoformat(),
                        "category": expense.category,
                        "description": expense.description,
                        "amount": f"{expense.amount:.2f}",
                    }
                )

    def add_expense(
        self, expense_date: date, category: str, description: str, amount: Decimal
    ) -> Expense:
        """Validate and save a new expense, returning its assigned ID."""
        category = category.strip()
        description = description.strip()
        if not category or not description:
            raise ValueError("Category and description cannot be empty.")
        amount = self._parse_amount(str(amount))

        expenses = self._read_expenses()
        expense = Expense(
            id=max((item.id for item in expenses), default=0) + 1,
            date=expense_date,
            category=category,
            description=description,
            amount=amount,
        )
        expenses.append(expense)
        self._write_expenses(expenses)
        return expense

    def delete_expense(self, expense_id: int) -> bool:
        """Delete an expense by ID and report whether one was found."""
        expenses = self._read_expenses()
        remaining = [expense for expense in expenses if expense.id != expense_id]
        if len(remaining) == len(expenses):
            return False
        self._write_expenses(remaining)
        return True

    def get_expenses(self) -> list[Expense]:
        """Return all expenses ordered by date and then ID."""
        return sorted(self._read_expenses(), key=lambda expense: (expense.date, expense.id))

    def monthly_total(self, year: int, month: int) -> Decimal:
        """Return the total spending in the requested calendar month."""
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12.")
        return sum(
            (
                expense.amount
                for expense in self._read_expenses()
                if expense.date.year == year and expense.date.month == month
            ),
            start=Decimal("0.00"),
        )


def prompt_date() -> date:
    """Read a date in ISO format from the user."""
    return date.fromisoformat(input("Date (YYYY-MM-DD): ").strip())


def prompt_amount() -> Decimal:
    """Read and validate a monetary amount from the user."""
    return ExpenseTracker._parse_amount(input("Amount: "))


def print_expenses(expenses: list[Expense]) -> None:
    """Display expenses in a compact, readable table."""
    if not expenses:
        print("No expenses found.")
        return

    print(f"\n{'ID':<5} {'Date':<12} {'Category':<18} {'Description':<32} {'Amount':>10}")
    print("-" * 82)
    for expense in expenses:
        print(
            f"{expense.id:<5} {expense.date.isoformat():<12} "
            f"{expense.category[:17]:<18} {expense.description[:31]:<32} "
            f"{expense.amount:>10.2f}"
        )


def run_menu(tracker: ExpenseTracker) -> None:
    """Run the interactive menu until the user chooses to exit."""
    while True:
        print("\n=== Expense Tracker ===")
        print("1. Add expense")
        print("2. Delete expense")
        print("3. View all expenses")
        print("4. Calculate monthly spending")
        print("5. Exit")
        choice = input("Choose an option (1-5): ").strip()

        try:
            if choice == "1":
                expense_date = prompt_date()
                category = input("Category: ")
                description = input("Description: ")
                amount = prompt_amount()
                expense = tracker.add_expense(expense_date, category, description, amount)
                print(f"Expense added with ID {expense.id}.")
            elif choice == "2":
                expense_id = int(input("Expense ID to delete: ").strip())
                if tracker.delete_expense(expense_id):
                    print("Expense deleted.")
                else:
                    print(f"No expense found with ID {expense_id}.")
            elif choice == "3":
                print_expenses(tracker.get_expenses())
            elif choice == "4":
                month_text = input("Month (YYYY-MM): ").strip()
                selected_month = datetime.strptime(month_text, "%Y-%m").date()
                total = tracker.monthly_total(selected_month.year, selected_month.month)
                print(f"Total spending for {selected_month:%Y-%m}: {total:.2f}")
            elif choice == "5":
                print("Goodbye.")
                return
            else:
                print("Please choose a number from 1 to 5.")
        except (ValueError, OSError) as error:
            print(f"Could not complete that action: {error}")


def main() -> None:
    """Start the application and handle an expected keyboard interruption."""
    try:
        run_menu(ExpenseTracker())
    except KeyboardInterrupt:
        print("\nGoodbye.")


if __name__ == "__main__":
    main()
