#!/usr/bin/env python3
"""
Batch validation script for Phase 1.
Processes all 9 samples in dry-run mode (no file moves) and reports results.
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services import (
    AccountMatcher,
    BBParser,
    ConversionPipeline,
    DateExtractor,
    MercadoPagoParser,
    OFXFileReader,
    OFXParser,
    ProcessorRegistry,
    RicoInvestimentoParser,
    RicoParser,
    TextNormalizer,
    TransactionCategorizer,
    TransactionPostProcessor,
    XPCCParser,
    XPContaParser,
)
from services.processors import (
    BBProcessor,
    MercadoPagoProcessor,
    OFXProcessor,
    RicoInvestimentoProcessor,
    RicoProcessor,
    XPCCProcessor,
    XPContaProcessor,
)

SAMPLES_DIR = Path(__file__).parent.parent / "samples"
RESULTS_DIR = Path(__file__).parent / "results"

PHASE1_SAMPLES = [
    "Extrato_banco_do_brasil_052026.ofx",
    "inter_rodrigo_Extrato-01-05-2026-a-31-05-2026-OFX.ofx",
    "xp_rodrigo_digital_extrato_de_01-05-2026_ate_31-05-2026.ofx",
    "Fatura_xp_2026-06-15.csv",
    "rico_carine_digital_extrato_de_01-05-2026_ate_31-05-2026.ofx",
    "carine_rico_extrato_investimento_de_01-05-2026_ate_31-05-2026.xlsx",
    "rodrigo_nubank_digital_extrato_60330829_01MAI2026_31MAI2026.ofx",
    "Nubank_fatura_rodrigo_2026-06-15.ofx",
    "rodrigo_xp_investimentoextrato_de_01-05-2026_ate_31-05-2026.xlsx",
]


def build_services():
    project_root = Path(__file__).parent.parent
    categorias_file = project_root / "categorias.yaml"
    contas_file = project_root / "contas.yaml"

    text_normalizer = TextNormalizer()
    date_extractor = DateExtractor()
    categorizer = TransactionCategorizer(
        rules_file=str(categorias_file) if categorias_file.exists() else None
    )
    file_reader = OFXFileReader()

    ofx_parser = OFXParser(text_normalizer, categorizer, date_extractor)
    mercadopago_parser = MercadoPagoParser(text_normalizer, categorizer, date_extractor)
    rico_parser = RicoParser(categorizer)
    rico_investimento_parser = RicoInvestimentoParser(categorizer)
    xp_cc_parser = XPCCParser(text_normalizer, categorizer, date_extractor)
    xp_conta_parser = XPContaParser(text_normalizer, categorizer, date_extractor)
    bb_parser = BBParser(categorizer)

    account_matcher = AccountMatcher(
        config_file=str(contas_file) if contas_file.exists() else None
    )
    postprocessor = TransactionPostProcessor()

    processors = [
        XPCCProcessor(xp_cc_parser),
        XPContaProcessor(xp_conta_parser),
        BBProcessor(bb_parser),
        RicoProcessor(rico_parser),
        MercadoPagoProcessor(mercadopago_parser),
        OFXProcessor(file_reader, ofx_parser),
        RicoInvestimentoProcessor(rico_investimento_parser),
    ]

    registry = ProcessorRegistry(processors)
    return registry, account_matcher, postprocessor, date_extractor


def run_sample(filename, registry, account_matcher, postprocessor, date_extractor):
    file_path = SAMPLES_DIR / filename
    result = {
        "filename": filename,
        "exists": file_path.exists(),
        "processor": None,
        "account": None,
        "transactions": 0,
        "error": None,
        "csv_written": False,
    }

    if not file_path.exists():
        result["error"] = "FILE NOT FOUND"
        return result

    # Step 1: Find processor
    processor = registry.find(file_path)
    if not processor:
        result["error"] = "NO PROCESSOR FOUND"
        return result
    result["processor"] = processor.name

    # Step 2: Parse
    try:
        transactions = processor.parse(file_path)
        if not transactions:
            result["error"] = "PARSE RETURNED EMPTY"
            return result
        result["transactions"] = len(transactions)
    except Exception as e:
        result["error"] = f"PARSE ERROR: {e}"
        return result

    # Step 3: Account matching
    account = account_matcher.match_account(filename)
    result["account"] = account
    if not account:
        result["error"] = "NO ACCOUNT MATCH"
        return result

    # Step 4: Post-process
    try:
        transactions = postprocessor.process(transactions, account)
    except Exception as e:
        result["error"] = f"POSTPROCESS ERROR: {e}"
        return result

    # Step 5: Write CSV (dry-run to results dir)
    try:
        from services.ezbookkeeping_csv_writer import EZBookkeepingCSVWriter

        csv_path = RESULTS_DIR / f"{file_path.stem}.csv"
        writer = EZBookkeepingCSVWriter()
        writer.create_csv_file(csv_path)
        for txn in transactions:
            if txn["type"] == "transfer":
                writer.write_transfer(
                    txn["date"], txn["amount"], txn["description"],
                    txn["category"], txn["subcategory"], account,
                )
            elif txn["type"] == "expense":
                writer.write_expense(
                    txn["date"], txn["amount"], txn["description"],
                    txn["category"], txn["subcategory"], account,
                )
            elif txn["type"] == "income":
                writer.write_income(
                    txn["date"], txn["amount"], txn["description"],
                    txn["category"], txn["subcategory"], account,
                )
        writer.close()
        result["csv_written"] = True
    except Exception as e:
        result["error"] = f"CSV WRITE ERROR: {e}"
        return result

    return result


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    registry, account_matcher, postprocessor, date_extractor = build_services()

    print("=" * 70)
    print("  OFX-CONVERTER — Phase 1 Batch Validation")
    print("=" * 70)
    print()

    results = []
    for filename in PHASE1_SAMPLES:
        r = run_sample(filename, registry, account_matcher, postprocessor, date_extractor)
        results.append(r)

    # Print results table
    ok_count = 0
    fail_count = 0

    for r in results:
        if r["error"]:
            status = "FAIL"
            fail_count += 1
            detail = r["error"]
        else:
            status = " OK "
            ok_count += 1
            detail = f"{r['transactions']} txns | {r['account']}"

        print(f"[{status}] {r['filename']}")
        print(f"       Processor: {r['processor'] or '-'}")
        print(f"       Detail: {detail}")
        print()

    print("-" * 70)
    print(f"  TOTAL: {ok_count}/{len(results)} OK, {fail_count} FAILED")
    print("-" * 70)

    # Save report
    report_path = RESULTS_DIR / "baseline_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("Phase 1 Baseline Report\n")
        f.write("=" * 50 + "\n\n")
        for r in results:
            status = "OK" if not r["error"] else "FAIL"
            f.write(f"[{status}] {r['filename']}\n")
            f.write(f"  Processor: {r['processor']}\n")
            f.write(f"  Account: {r['account']}\n")
            f.write(f"  Transactions: {r['transactions']}\n")
            if r["error"]:
                f.write(f"  Error: {r['error']}\n")
            f.write("\n")

    print(f"\nReport saved to: {report_path}")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
