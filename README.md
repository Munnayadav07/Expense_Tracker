# Expense Tracker

A menu-driven command-line expense tracker written in Python. It uses only the
Python standard library and stores expenses in a CSV file.

## Features

- Add an expense with a date, category, description, and amount.
- Delete an expense by its ID.
- View all expenses, ordered by date.
- Calculate total spending for a selected month.
- Validate dates and positive monetary amounts (up to two decimal places).
- Report invalid CSV data and file errors without terminating the menu.

## Requirements

- Python 3.9 or newer
- No third-party packages

## Run

From the project directory:

```console
python expense_tracker.py
```

The application reads and writes `data/expenses.csv`, relative to
`expense_tracker.py`. The repository includes sample rows; you can edit or
remove them before starting with an empty tracker. If the file is missing, it
will be created the first time an expense is added.

Amounts should be entered as positive numbers with no more than two decimal
places. Dates use `YYYY-MM-DD`, and monthly totals use `YYYY-MM`.

## Run tests

```console
python -m unittest discover -s tests -v
```

## Project structure

```text
expense-tracker/
├── data/
│   └── expenses.csv       # Sample expense data and application storage
├── tests/
│   └── test_expense_tracker.py
├── expense_tracker.py     # Application, CSV storage, and menu
└── README.md
```

## CSV format

The CSV file has the following columns, in order:

| Column | Description |
| --- | --- |
| `id` | Positive integer used to select an expense for deletion |
| `date` | Expense date in `YYYY-MM-DD` format |
| `category` | Expense category |
| `description` | Short expense description |
| `amount` | Positive amount with up to two decimal places |
