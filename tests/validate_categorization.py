#!/usr/bin/env python3
"""
Validates categorization and account matching for all generated CSVs.
"""
import csv
import sys
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"

EXPECTED_ACCOUNTS = {
    "Extrato_banco_do_brasil_052026": "Banco do Brasil Rodrigo",
    "inter_rodrigo_Extrato-01-05-2026-a-31-05-2026-OFX": "Conta Inter Rodrigo",
    "xp_rodrigo_digital_extrato_de_01-05-2026_ate_31-05-2026": "Conta Digital XP Rodrigo",
    "Fatura_xp_2026-06-15": "CC XP Rodrigo",
    "rico_carine_digital_extrato_de_01-05-2026_ate_31-05-2026": "Conta Digital Rico Carine",
    "carine_rico_extrato_investimento_de_01-05-2026_ate_31-05-2026": "Conta Investimento Rico Carine",
    "rodrigo_nubank_digital_extrato_60330829_01MAI2026_31MAI2026": "NuConta Rodrigo",
    "Nubank_fatura_rodrigo_2026-06-15": "CC NuBank Rodrigo",
    "rodrigo_xp_investimentoextrato_de_01-05-2026_ate_31-05-2026": "Conta Investimento XP Rodrigo",
}


def validate_csv(csv_path: Path) -> dict:
    stem = csv_path.stem
    expected_account = EXPECTED_ACCOUNTS.get(stem)
    result = {
        "file": csv_path.name,
        "expected_account": expected_account,
        "actual_account": None,
        "total_txns": 0,
        "categorized": 0,
        "uncategorized": 0,
        "account_ok": False,
    }

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            result["total_txns"] += 1
            account = row.get("Account", "")
            if not result["actual_account"] and account:
                result["actual_account"] = account

            category = row.get("Category", "")
            if category and category != "Diversos":
                result["categorized"] += 1
            else:
                result["uncategorized"] += 1

    if expected_account and result["actual_account"]:
        result["account_ok"] = result["actual_account"].strip() == expected_account.strip()

    return result


def main():
    csv_files = sorted(RESULTS_DIR.glob("*.csv"))
    if not csv_files:
        print("No CSV files found in results/")
        return 1

    print("=" * 60)
    print("  Categorization & Account Matching Validation")
    print("=" * 60)
    print()

    all_accounts_ok = True
    total_categorized = 0
    total_txns = 0

    for csv_path in csv_files:
        r = validate_csv(csv_path)
        total_txns += r["total_txns"]
        total_categorized += r["categorized"]

        acc_status = "OK" if r["account_ok"] else "WRONG"
        if not r["expected_account"]:
            acc_status = "SKIP"

        cat_pct = (r["categorized"] / r["total_txns"] * 100) if r["total_txns"] > 0 else 0

        if not r["account_ok"] and r["expected_account"]:
            all_accounts_ok = False

        print(f"[{acc_status:>5}] {r['file']}")
        print(f"        Account: {r['actual_account']}")
        print(f"        Categorized: {r['categorized']}/{r['total_txns']} ({cat_pct:.0f}%)")
        print()

    overall_pct = (total_categorized / total_txns * 100) if total_txns > 0 else 0

    print("-" * 60)
    print(f"  Accounts: {'ALL CORRECT' if all_accounts_ok else 'ERRORS FOUND'}")
    print(f"  Categorization: {total_categorized}/{total_txns} ({overall_pct:.0f}%) beyond 'Diversos'")
    print("-" * 60)

    return 0 if all_accounts_ok else 1


if __name__ == "__main__":
    sys.exit(main())
