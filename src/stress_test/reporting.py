"""Outputs to answer:
- What macro path was assumed (baseline vs adverse)?
- What loss rates/losses did the models imply by bucket?
- What happened to capital ratios over time?
- Which banks breach the hurdle and by how much?
- What is the system shortfall?
"""

from __future__ import annotations
from pathlib import Path
from matplotlib import pyplot as plt
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

def write_cet1_ratio_paths_csv(cet1_ratio_paths: pd.DataFrame, out_dir: Path) -> Path:
    """Write CET1 Ratio Paths"""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "cet1_ratio_paths.csv"
    cet1_ratio_paths.to_csv(out_path, index=False)
    return out_path

def write_loss_paths_csv(loss_paths: pd.DataFrame, out_dir: Path) -> Path:
    """Write loss paths"""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "loss_paths.csv"
    loss_paths.to_csv(out_path, index=False)
    return out_path

def write_losses_by_bucket_csv(losses_by_bucket: pd.DataFrame, out_dir: Path) -> Path:
    """Write losses by bucket"""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "losses_by_bucket.csv"
    losses_by_bucket.to_csv(out_path, index=False)
    return out_path

def plot_cet1_ratio_paths(cet1_ratio_paths: pd.DataFrame, out_dir: Path) -> Path:
    """Plot CET1 Ratio Paths"""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "cet1_ratio_paths.png"
    hurdle = 7
    df = cet1_ratio_paths.copy()
    required_cols = {"scenario", "bank", "quarter", "cet1_ratio (%)"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"cet1_ratio_paths missing required columns: {missing}")
    df = df[["scenario", "bank", "quarter", "cet1_ratio (%)"]].copy()
    df = df.sort_values(["bank", "scenario", "quarter"])
    colour_cycle = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])
    banks = list(pd.unique(df["bank"]))
    bank_colour = {
        b: colour_cycle[i % len(colour_cycle)] if colour_cycle else None
        for i, b in enumerate(banks)
    }
    scenario_linestyle = {
        "baseline": "-",
        "adverse": "--"
    }
    fig, ax = plt.subplots()
    scenarios = list(pd.unique(df["scenario"]))
    for bank in banks:
        for scenario in scenarios:
            sub = df[(df["bank"] == bank) & (df["scenario"] == scenario)]
            if sub.empty:
                continue
            s_key = str(scenario).lower()
            ax.plot(
                sub["quarter"],
                sub["cet1_ratio (%)"],
                label=f"{bank} ({scenario})",
                linestyle=scenario_linestyle.get(s_key, "-"),
                color=bank_colour.get(bank, None),
                linewidth=1
            )
    plt.axhline(y=hurdle, color='black', alpha=0.5, linestyle='-', label='CET1 hurdle (7%)')
    ax.set_title("CET1 ratio paths")
    ax.set_ylabel("CET1 ratio (%)")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(loc="best", fontsize="small")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path

def plot_total_losses_paths(loss_paths: pd.DataFrame, out_dir: Path) -> Path:
    """Plot total losses path"""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "total_losses_paths.png"
    df = loss_paths.copy()
    required_cols = {"scenario", "bank", "quarter", "total_losses_t"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"loss_paths missing required columns: {missing}")
    df = df[["scenario", "bank", "quarter", "total_losses_t"]].copy()
    df = df.sort_values(["bank", "scenario", "quarter"])
    colour_cycle = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])
    banks = list(pd.unique(df["bank"]))
    bank_colour = {
        b: colour_cycle[i % len(colour_cycle)] if colour_cycle else None
        for i, b in enumerate(banks)
    }
    scenario_linestyle = {
        "baseline": "-",
        "adverse": "--"
    }
    fig, ax = plt.subplots()
    scenarios = list(pd.unique(df["scenario"]))
    for bank in banks:
        for scenario in scenarios:
            sub = df[(df["bank"] == bank) & (df["scenario"] == scenario)]
            if sub.empty:
                continue
            s_key = str(scenario).lower()
            ax.plot(
                sub["quarter"],
                sub["total_losses_t"],
                label=f"{bank} ({scenario})",
                linestyle=scenario_linestyle.get(s_key, "-"),
                color=bank_colour.get(bank, None),
                linewidth=1
            )

    ax.set_title("Total Losses paths")
    ax.set_ylabel("Total Losses (£bn)")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(loc="best", fontsize="small")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path

def plot_trough_cet1_ratio_adverse(trough_summary: pd.DataFrame, out_dir: Path) -> Path:
    """Plot trough CET1 ratio vs hurdle (adverse)"""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "trough_cet1_ratio_adverse.png"
    hurdle = 7
    df = trough_summary.copy()
    df = df[df["scenario"]=="adverse"]
    required_cols = {"bank", "trough_quarter", "trough_cet1_ratio (%)"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"trough_summary missing required columns: {missing}")
    df["bank_trough_quarter"] = df["bank"].astype(str) + " (" + df["trough_quarter"].astype(str) + ")"
    df = df[["bank_trough_quarter", "trough_cet1_ratio (%)"]]
    fig, ax = plt.subplots()
    ax.bar(df["bank_trough_quarter"], df["trough_cet1_ratio (%)"])
    ax.set_title("Trough CET1 ratio (adverse scenario)")
    ax.set_ylabel("CET1 ratio (%)")
    plt.axhline(y=hurdle, color='black', linestyle='--', label='CET1 hurdle (7%)')
    ax.tick_params(axis="x", rotation=15)
    ax.legend(loc="best", fontsize="small")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path




def plot_results_figures(
        *,
        cet1_ratio_paths: pd.DataFrame | None,
        loss_paths: pd.DataFrame | None,
        trough_summary: pd.DataFrame | None,
        out_dir: Path,
        plot_figures: bool
) -> list[Path]:
    plotted: list[Path] = []
    if plot_figures:
        if cet1_ratio_paths is None or loss_paths is None or trough_summary is None:
            raise ValueError("cet1_ratio_paths, loss_paths and trough_summary are required when plot_figures=True")
        plotted.append(plot_cet1_ratio_paths(cet1_ratio_paths, out_dir))
        plotted.append(plot_total_losses_paths(loss_paths, out_dir))
        plotted.append(plot_trough_cet1_ratio_adverse(trough_summary, out_dir))
    return plotted

def write_results_tables(
    *,
    banks: list[Bank],
    system_results: pd.DataFrame | None,
    trough_summary: pd.DataFrame | None,
    cet1_ratio_paths: pd.DataFrame | None,
    loss_paths: pd.DataFrame | None,
    losses_by_bucket: pd.DataFrame | None,
    out_dir: Path,
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
    write_results:
        Whether to write system_results.csv and trough_summary.csv

    Returns
    -------
    list[Path]
        Paths written.
    """

    written: list[Path] = []

    if write_results:
        if system_results is None or trough_summary is None or cet1_ratio_paths is None or loss_paths is None or losses_by_bucket is None:
            raise ValueError("system_results, trough_summary, cet1_ratio_paths and loss_paths are required when write_results=True")
        written.append(write_system_results_csv(system_results, out_dir))
        written.append(write_trough_summary_csv(trough_summary, out_dir))
        written.append(write_cet1_ratio_paths_csv(cet1_ratio_paths, out_dir))
        written.append(write_loss_paths_csv(loss_paths, out_dir))
        written.append(write_losses_by_bucket_csv(losses_by_bucket, out_dir))

    return written

