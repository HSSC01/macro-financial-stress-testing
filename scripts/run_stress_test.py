"""Command-line entry point for the macro-financial stress testing framework.

This script is intentionally a thin orchestrator:
- Builds stylised bank balance sheets
- Optionally prints starting-position summaries
- Optionally runs the full stress test (scenario → losses → CET1 path → trough/shortfall)
- Writes results to outputs/tables/

Examples:
  # Print starting positions only
  python3 scripts/run_stress_test.py --print-banks

  # Write starting positions CSV only
  python3 scripts/run_stress_test.py --write-starting-csv

  # Full stress test + write tables
  python3 scripts/run_stress_test.py --run-stress --write-results-csv

  # Full stress test for a single bank
  python3 scripts/run_stress_test.py --bank "HSBC" --run-stress --write-results-csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd

import stress_test.engine as eng
import stress_test.reporting as rpt
from stress_test.balance_sheet import Bank, make_stylised_banks


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_TABLES_DIR = REPO_ROOT / "outputs" / "tables"



# Formatting


def format_money_bn(x: float) -> str:
    return f"£{x:,.2f}bn"


def format_pct(x: float) -> str:
    return f"{100.0 * x:,.2f}%"


def bank_buckets_dataframe(bank: Bank) -> pd.DataFrame:
    rows: list[dict] = []
    for bucket_name, bucket in bank.buckets.items():
        rwa = getattr(bucket, "rwa", bucket.ead * bucket.rw)
        rows.append(
            {
                "bucket": bucket_name,
                "EAD_bn": float(bucket.ead),
                "RW": float(bucket.rw),
                "RWA_bn": float(rwa),
                "LGD": float(bucket.lgd),
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("bucket").reset_index(drop=True)
    return df


def format_bank_summary(bank: Bank) -> str:
    lines: list[str] = []

    lines.append(f"{bank.name}")
    lines.append("-" * len(bank.name))
    lines.append(f"Total EAD:  {format_money_bn(bank.total_ead)}")
    lines.append(f"Total RWA:  {format_money_bn(bank.total_rwa)}")
    lines.append(f"CET1:       {format_money_bn(bank.cet1)}")
    lines.append(f"CET1 ratio: {format_pct(bank.cet1_ratio)}")

    if getattr(bank, "overlays", None):
        lines.append("")
        lines.append("Overlays (shares):")
        for k, v in bank.overlays.items():
            lines.append(f"  - {k}: {format_pct(float(v))}")

    df = bank_buckets_dataframe(bank)
    lines.append("")
    lines.append("Buckets:")
    if df.empty:
        lines.append("  (no buckets)")
    else:
        df_disp = df.copy()
        for c in ["EAD_bn", "RW", "RWA_bn", "LGD"]:
            df_disp[c] = df_disp[c].map(lambda x: f"{float(x):,.3f}")
        lines.append(df_disp.to_string(index=False))

    return "\n".join(lines)



# Selection + writing utilities


def select_banks(banks: Iterable[Bank], bank_name: str | None) -> list[Bank]:
    if bank_name is None:
        return list(banks)

    wanted = bank_name.strip().lower()
    selected = [b for b in banks if b.name.strip().lower() == wanted]

    if not selected:
        available = ", ".join(sorted({b.name for b in banks}))
        raise SystemExit(f"Unknown bank '{bank_name}'. Available: {available}")

    return selected



# Command Line Interface

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run starting-position summary and (optionally) the full stress test."
    )

    p.add_argument(
        "--bank",
        type=str,
        default=None,
        help="Optional: run for a single bank name (must match exactly, e.g. 'HSBC').",
    )

    p.add_argument(
        "--print-banks",
        action="store_true",
        help="Print starting-position summaries to the console.",
    )

    p.add_argument(
        "--write-starting-csv",
        action="store_true",
        help="Write outputs/tables/bank_starting_positions.csv",
    )

    p.add_argument(
        "--run-stress",
        action="store_true",
        help="Run the full stress test (fit satellite models, project scenarios, compute trough/shortfall).",
    )

    p.add_argument(
        "--print-system-results",
        action="store_true",
        help="Print the full system_results panel to the console (can be very verbose).",
    )

    p.add_argument(
        "--write-results-csv",
        action="store_true",
        help="Write outputs/tables/system_results.csv and outputs/tables/trough_summary.csv (requires --run-stress).",
    )

    return p.parse_args()


def main() -> None:
    args = parse_args()

    # 1) Instantiate banks
    banks = select_banks(make_stylised_banks(), args.bank)

    # 2) Optional: console output (starting positions)
    if args.print_banks:
        for i, bank in enumerate(banks):
            if i:
                print("\n" + "=" * 80 + "\n")
            print(format_bank_summary(bank))

    # 3) Optional: write starting positions table
    if args.write_starting_csv:
        out_path = rpt.write_starting_positions_csv(banks, OUTPUT_TABLES_DIR)
        print(f"Wrote: {out_path}")

    # 4) Optional: full stress test
    if args.run_stress:
        # Fit satellite models (synthetic history)
        models = eng.fit_models_from_synthetic_history()

        # Project loss rates for baseline + adverse over 12 quarters
        projected_loss_rates = eng.build_projected_loss_rates(models=models, horizon_q=12)

        # Run the stress test mechanics
        system_results = eng.run_system(banks=banks, projected_loss_rates=projected_loss_rates)

        # Compute trough/shortfall
        trough_summary = eng.compute_trough_summary(system_results, banks=banks)

        # CET1 ratio paths
        cet1_ratio_paths = system_results.drop(columns=["total_losses_t"])

        # Loss paths (total)
        loss_paths = system_results.drop(columns=["cet1_ratio", "cet1"])

        # Losses by bucket
        losses_by_bucket = eng.compute_losses_by_bucket(banks=banks, projected_loss_rates=projected_loss_rates)

        if args.print_system_results:
            print(system_results)

        print("\nTrough / shortfall summary:\n")
        print(trough_summary)

        if args.write_results_csv:
            paths = rpt.write_results_tables(
                banks=banks,
                system_results=system_results,
                trough_summary=trough_summary,
                cet1_ratio_paths=cet1_ratio_paths,
                loss_paths=loss_paths,
                losses_by_bucket=losses_by_bucket,
                out_dir=OUTPUT_TABLES_DIR,
                write_results=True,
            )
            for p in paths:
                print(f"Wrote: {p}")

    else:
        if args.write_results_csv:
            raise SystemExit("--write-results-csv requires --run-stress")


if __name__ == "__main__":
    main()