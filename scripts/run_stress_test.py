"""Command-line entry point for running stress tests.
- Instantiate stylised banks from balance_sheet
- Print readable starting-position summary per bank
- Write a CSV summary to outputs/tables

Run:
    python3 scripts/run_stress_test.py
    python3 scripts/run_stress_test.py --bank "HSBC" --write-csv
"""

from __future__ import annotations
import argparse
from pathlib import Path
from typing import Iterable
import pandas as pd
from stress_test.balance_sheet import Bank, make_stylised_banks

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_TABLES_DIR = REPO_ROOT / "outputs" / "tables"

def format_money_bn(x: float) -> str:
    """Format a float as £bn with 2dp."""
    return f"£{x:,.2f}bn"

def format_pct(x: float) -> str:
    """Format a decimal ratio as a percentage with 2dp."""
    return f"{100.0 * x:,.2f}%"

def bank_buckets_dataframe(bank: Bank) -> pd.DataFrame:
    """Create a bucket-level dataframe for display/export."""
    rows = []
    for bucket_name, bucket in bank.buckets.items():
        rwa = getattr(bucket, "rwa", bucket.ead * bucket.rw)
        rows.append({
            "bucket": bucket_name,
            "EAD_bn": float(bucket.ead),
            "RW": float(bucket.rw),
            "RWA_bn": float(rwa),
            "LGD": float(bucket.lgd)
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("bucket").reset_index(drop=True)
        df["EAD_bn"] = df["EAD_bn"].round(3)
        df["RWA_bn"] = df["RWA_bn"].round(3)
        df["RW"] = df["RW"].round(3)
        df["LGD"] = df["LGD"].round(3)
    return df
    
def format_bank_summary(bank: Bank) -> str:
    """Return a summary for a single bank."""
    lines: list[str] = []
    lines.append(f"{bank.name}")
    lines.append("-" * len(bank.name))
    lines.append(f"Total EAD: {format_money_bn(bank.total_ead)}")
    lines.append(f"Total RWA: {format_money_bn(bank.total_rwa)}")   
    lines.append(f"CET1: {format_money_bn(bank.cet1)}")
    lines.append(f"CET1 ratio: {format_pct(bank.cet1_ratio)}")
    
    if getattr(bank, "overlays", None):
        lines.append("")
        lines.append("Overlays (shares):")
        for k, v in bank.overlays.items():
            lines.append(f" - {k}: {format_pct(float(v))}")

    df = bank_buckets_dataframe(bank)
    lines.append("")
    lines.append("Buckets:")
    if df.empty:
        lines.append(" (no buckets)")
    else:
        df_disp = df.copy()
        df_disp["EAD_bn"] = df_disp["EAD_bn"].map(lambda x: f"{x:,.3f}")
        df_disp["RWA_bn"] = df_disp["RWA_bn"].map(lambda x: f"{x:,.3f}")
        df_disp["RW"] = df_disp["RW"].map(lambda x: f"{x:,.3f}")
        df_disp["LGD"] = df_disp["LGD"].map(lambda x: f"{x:,.3f}")

        lines.append(df_disp.to_string(index=False))

    return "\n".join(lines)

def select_banks(banks: Iterable[Bank], bank_name: str | None) -> list[Bank]:
    if bank_name is None:
        return list(banks)
    wanted = bank_name.strip().lower()
    selected = [b for b in banks if b.name.strip().lower() == wanted]
    if not selected:
        available = ", ".join(sorted({b.name for b in banks}))
        raise SystemExit(f"Unknown bank '{bank_name}'. Available: {available}")
    return selected

def write_starting_positions_csv(banks: list[Bank]) -> Path:
    """Write single CSV with headline starting positions for all banks."""
    OUTPUT_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for b in banks:
        rows.append({
            "bank": b.name,
            "total_ead_bn": float(b.total_ead),
            "total_rwa_bn": float(b.total_rwa),
            "cet1_bn": float(b.cet1),
            "cet1_ratio": float(b.cet1_ratio),
            **{f"overlay__{k}": float(v) for k, v in getattr(b, "overlays", {}).items()}
        })

    df = pd.DataFrame(rows)
    out_path = OUTPUT_TABLES_DIR / "bank_starting_positions.csv"
    df.to_csv(out_path, index=False)
    return out_path

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run bank starting-position summary.")
    p.add_argument(
        "--bank",
        type=str,
        default=None,
        help="Optional: run for a single bank name (must match exactly)."
    )
    p.add_argument(
        "--write-csv",
        action="store_true",
        help="Write outputs/tables/bank_starting_positions.csv"
    )
    return p.parse_args()

def main() -> None:
    args = parse_args()
    banks = make_stylised_banks()
    banks = select_banks(banks, args.bank)
    for i, bank in enumerate(banks):
        if i:
            print("\n" + "=" * 80 + "\n")
        print(format_bank_summary(bank))
    if args.write_csv:
        out_path = write_starting_positions_csv(banks)
        print(f"\nWrote: {out_path}")

if __name__ == "__main__":
    main()