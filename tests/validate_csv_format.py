#!/usr/bin/env python3
"""
Validates that all generated CSVs follow the EZBookkeeping format.
"""
import csv
import sys
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"

EXPECTED_HEADER = [
    "Time", "Timezone", "Type", "Category", "Sub Category",
    "Account", "Account Currency", "Amount",
    "Account2", "Account2 Currency", "Account2 Amount",
    "Geographic Location", "Tags", "Description"
]

VALID_TYPES = {"Expense", "Income", "Transfer"}


def validate_csv(csv_path: Path) -> list:
    errors = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)

            if header != EXPECTED_HEADER:
                errors.append(f"Header mismatch: got {header}")
                return errors

            for i, row in enumerate(reader, start=2):
                if len(row) != len(EXPECTED_HEADER):
                    errors.append(f"Row {i}: wrong column count ({len(row)} vs {len(EXPECTED_HEADER)})")
                    continue

                time_val = row[0]
                timezone = row[1]
                type_val = row[2]
                category = row[3]
                account_currency = row[6]
                amount = row[7]

                if timezone != "-03:00":
                    errors.append(f"Row {i}: timezone '{timezone}' != '-03:00'")

                if type_val not in VALID_TYPES:
                    errors.append(f"Row {i}: invalid type '{type_val}'")

                if account_currency != "BRL":
                    errors.append(f"Row {i}: currency '{account_currency}' != 'BRL'")

                try:
                    amt = float(amount)
                    if amt < 0:
                        errors.append(f"Row {i}: negative amount {amt} (should be abs)")
                except ValueError:
                    errors.append(f"Row {i}: non-numeric amount '{amount}'")

                if not category:
                    errors.append(f"Row {i}: empty category")

                if type_val == "Transfer":
                    acc2_currency = row[9]
                    acc2_amount = row[10]
                    if acc2_currency and acc2_currency != "BRL":
                        errors.append(f"Row {i}: Account2 currency '{acc2_currency}' != 'BRL'")

    except Exception as e:
        errors.append(f"Read error: {e}")

    return errors


def main():
    csv_files = sorted(RESULTS_DIR.glob("*.csv"))
    if not csv_files:
        print("No CSV files found in results/")
        return 1

    print("=" * 60)
    print("  CSV Format Validation")
    print("=" * 60)
    print()

    all_pass = True
    for csv_path in csv_files:
        errors = validate_csv(csv_path)
        if errors:
            print(f"[FAIL] {csv_path.name}")
            for e in errors[:5]:
                print(f"       {e}")
            all_pass = False
        else:
            print(f"[ OK ] {csv_path.name}")

    print()
    print("-" * 60)
    status = "ALL PASS" if all_pass else "FAILURES FOUND"
    print(f"  {status}")
    print("-" * 60)
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
