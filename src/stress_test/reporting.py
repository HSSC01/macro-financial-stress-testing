"""Outputs to answer:
- What macro path was assumed (baseline vs adverse)?
- What loss rates/losses did the models imply by bucket?
- What happened to capital ratios over time?
- Which banks breach the hurdle and by how much?
- What is the system shortfall?
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from stress_test.balance_sheet import Bank


def write_starting_positions_csv(banks: list[Bank], out_dir: Path) -> Path:
    """Write headline starting positions for all banks."""
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for b in banks:
        rows.append(
            {
                "bank": b.name,
                "total_ead_bn": float(b.total_ead),
                "total_rwa_bn": float(b.total_rwa),
                "cet1_bn": float(b.cet1),
                "cet1_ratio": float(b.cet1_ratio),
                **{f"overlay__{k}": float(v) for k, v in getattr(b, "overlays", {}).items()},
            }
        )

    df = pd.DataFrame(rows)
    out_path = out_dir / "bank_starting_positions.csv"
    df.to_csv(out_path, index=False)
    return out_path


def write_system_results_csv(system_results: pd.DataFrame, out_dir: Path) -> Path:
    """Write the full system results panel."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "system_results.csv"
    system_results.to_csv(out_path, index=False)
    return out_path


def write_trough_summary_csv(trough_summary: pd.DataFrame, out_dir: Path) -> Path:
    """Write trough CET1 ratio and shortfall table."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "trough_summary.csv"
    trough_summary.to_csv(out_path, index=False)
    return out_path


def write_results_tables(
    *,
    banks: list[Bank],
    system_results: pd.DataFrame | None,
    trough_summary: pd.DataFrame | None,
    out_dir: Path,
    write_starting: bool,
    write_results: bool,
) -> list[Path]:
    """Convenience wrapper to write the standard table pack.

    Parameters
    ----------
    banks:
        Bank objects used in the run.
    system_results:
        Output of engine.run_system(...). Required if write_results=True.
    trough_summary:
        Output of engine.compute_trough_summary(...). Required if write_results=True.
    out_dir:
        Directory to write CSVs into.
    write_starting:
        Whether to write bank_starting_positions.csv
    write_results:
        Whether to write system_results.csv and trough_summary.csv

    Returns
    -------
    list[Path]
        Paths written.
    """

    written: list[Path] = []

    if write_starting:
        written.append(write_starting_positions_csv(banks, out_dir))

    if write_results:
        if system_results is None or trough_summary is None:
            raise ValueError("system_results and trough_summary are required when write_results=True")
        written.append(write_system_results_csv(system_results, out_dir))
        written.append(write_trough_summary_csv(trough_summary, out_dir))

    return written
