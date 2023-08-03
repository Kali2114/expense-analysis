import csv
from dataclasses import dataclass
from pickle import dump, load
from typing import List
import sys
import click

BIG_EXPENSIVE_THRESHOLD = 1000
DB_FILENAME = "budget.db"


@dataclass
class Expense:
    amount: int
    description: str
    id: int

    def __post_init__(self):
        if self.amount <= 0:
            raise ValueError("Wartość musi być dodatnią liczbą!")

    def is_big(self):
        return self.amount >= BIG_EXPENSIVE_THRESHOLD


def load_or_init():
    try:
        with open(DB_FILENAME, "rb") as stream:
            expenses = load(stream)
    except FileNotFoundError:
        expenses = []
    return expenses


def save_expenses(expenses):
    with open(DB_FILENAME, "wb") as stream:
        dump(expenses, stream)


def find_new_id(expenses):
    all_ids = {e.id for e in expenses}
    next_id = 1
    while next_id in all_ids:
        next_id += 1
    return next_id


def compute_total(expenses):
    amounts = [e.amount for e in expenses]
    return sum(amounts)


def print_report(expenses, total):
    if expenses:
        print("--ID--  -AMOUNT-  -BIG?-  --DESC--------------")
        for expense in expenses:
            if expense.is_big():
                big = "(!)"
            else:
                big = ""
            print(f"{expense.id:6}  {expense.amount:8}  {big:^6}  {expense.description}")
        print(f"TOTAL:   {total:8}")
    else:
        print("Nie podano żadnych wydatków!")


@click.group()
def cli():
    pass


@cli.command()
def report():
    expenses = load_or_init()
    total = compute_total(expenses)
    print_report(expenses, total)


@cli.command()
@click.argument("amount", type=int)
@click.argument("desc")
def add(amount, desc):
    expenses = load_or_init()
    next_id = find_new_id(expenses)
    try:
        new_expense = Expense(amount, desc, next_id)
    except ValueError as e:
        print(f":-( ERROR: {e.args[0]}")
        sys.exit(0)

    expenses.append(new_expense)
    save_expenses(expenses)
    print("Sukces!")


@cli.command()
@click.argument("csv_file")
def import_csv(csv_file):
    expenses = load_or_init()

    try:
        with open(csv_file) as stream:
            reader = csv.DictReader(stream)
            for row in reader:
                try:
                    amount = float(row["amount"])
                    description = row["description"]
                    next_id = find_new_id(expenses)
                    expense = Expense(amount, description, next_id)
                    expenses.append(expense)
                except ValueError as e:
                    print(f"ERROR: {e.args[0]}")
    except FileNotFoundError:
        print("Nie ma takiego pliku!")

    save_expenses(expenses)
    print("Zaimportowano.")


@cli.command()
@click.argument("csv_file")
def export_csv(csv_file):
    expenses = load_or_init()

    try:
        with open(csv_file, "w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["id", "amount", "description"])
            writer.writeheader()
            for expense in expenses:
                writer.writerow(
                    {"id": expense.id, "amount": expense.amount, "description": expense.description}
                )
    except Exception:
        print("Nie udało się wyeksportować do pliku CSV.")


@cli.command()
def export_python():
    expenses = load_or_init()
    print(expenses)


if __name__ == "__main__":
    cli()
