import pandas as pd
import stress_test.balance_sheet as bs
from stress_test.satellite import project_loss_rates, fit_bucket_models
# from stress_test.synthetic_data import make_synthetic_history
from stress_test.scenarios import make_baseline, make_adverse
import stress_test.data.data as data


def project_loss_rates_all_buckets(models: dict, scenario_df: pd.DataFrame) -> pd.DataFrame:
    """Project loss rates for all buckets under a single scenario."""
    return pd.DataFrame(
        {
            bucket: project_loss_rates(model, scenario_df)
            for bucket, model in models.items()
        }
    )


def compute_credit_losses(ead_by_bucket: pd.Series, loss_rates: pd.DataFrame) -> pd.DataFrame:
    """Compute credit losses per bucket and total losses per quarter."""
    losses_df = pd.DataFrame(index=loss_rates.index)
    for bucket in loss_rates.columns:
        if bucket not in ead_by_bucket.index:
            raise KeyError(f"EAD missing bucket '{bucket}'")
        losses_df[bucket] = ead_by_bucket[bucket] * loss_rates[bucket]

    losses_df["total_losses_t"] = losses_df.sum(axis=1)
    return losses_df

def compute_losses_by_bucket(banks: list[bs.Bank], projected_loss_rates: dict[str, pd.DataFrame]) -> pd.DataFrame:
        rows: list[pd.DataFrame] = []
        for bank in banks:
            ead_by_bucket = bank_ead_series(bank)

            for scenario, lr_df in projected_loss_rates.items():
                losses_df = compute_credit_losses(ead_by_bucket, lr_df)
                bucket_losses = losses_df.drop(columns=["total_losses_t"], errors="ignore")

                out = (pd.concat([lr_df.stack(), bucket_losses.stack()], axis=1).reset_index())
                out.columns = ["quarter", "bucket", "loss_rate", "losses_bn"]
                out.insert(0, "bank", bank.name)
                out.insert(0, "scenario", scenario)
                rows.append(out)
        
        return pd.concat(rows, ignore_index=True)

# Capital Dynamics

def simulate_cet1_path(cet1_0: float, total_losses: pd.Series) -> pd.Series:
    """CET1_t = CET1_0 - cumulative_losses_t"""
    return pd.Series(cet1_0 - total_losses.cumsum(), index=total_losses.index, name="cet1")

def compute_cet1_ratio(cet1_path: pd.Series, rwa: float) -> pd.Series:
    if rwa <= 0:
        raise ValueError("RWA must be positive")
    return pd.Series(cet1_path / rwa * 100, index=cet1_path.index, name="cet1_ratio")

# Bank-level orchestration

def bank_ead_series(bank: bs.Bank) -> pd.Series:
    """Extract EAD by bucket from a Bank object."""
    return pd.Series({bucket_name: bucket.ead for bucket_name, bucket in bank.buckets.items()}, name="ead")

def run_bank(bank: bs.Bank, loss_rates: pd.DataFrame) -> pd.DataFrame:
    """Run a single bank through a single scenario loss-rate panel"""
    ead = bank_ead_series(bank)
    losses = compute_credit_losses(ead, loss_rates)
    cet1_path = simulate_cet1_path(bank.cet1, losses["total_losses_t"])
    cet1_ratio = compute_cet1_ratio(cet1_path, bank.total_rwa)
    out = losses.copy()
    out["cet1"] = cet1_path
    out["cet1_ratio (%)"] = cet1_ratio
    return out

def run_system(banks: list[bs.Bank], projected_loss_rates: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Run all banks for all scenarios"""
    rows: list[pd.DataFrame] = []
    for scen_name, lr in projected_loss_rates.items():
        for bank in banks:
            bank_out = run_bank(bank, lr)
            tidy = pd.DataFrame({
                "scenario": scen_name,
                "bank": bank.name,
                "quarter": bank_out.index.astype(str),
                "total_losses_t": bank_out["total_losses_t"],
                "cet1": bank_out["cet1"],
                "cet1_ratio (%)": bank_out["cet1_ratio (%)"]
            })
            rows.append(tidy)
    return pd.concat(rows, ignore_index=True)

# Convenience: full pipeline up to projected loss rates

def fit_models_from_history(seed: int = 184):
    macro_hist = data.macro_hist()
    loss_hist = data.synthetic_loss_rates().reindex(macro_hist.index)
    return fit_bucket_models(macro_hist, loss_hist)

def build_projected_loss_rates(models: dict, horizon_q: int = 12, severity: float = 1.0) -> dict[str, pd.DataFrame]:
    baseline = make_baseline(horizon_q=horizon_q)
    adverse = make_adverse(baseline, severity=severity)
    return {
        "baseline": project_loss_rates_all_buckets(models, baseline),
        "adverse": project_loss_rates_all_buckets(models, adverse)
    }

def compute_trough_summary(results: pd.DataFrame, banks: list[bs.Bank], *, hurdle: float = 0.07) -> pd.DataFrame:
    """Compute trough CET1 ratio and capital shortfall to a hurdle.
    Parameters
    ----------
    results:
        Output of `run_system(...)` with columns: scenario, bank, quarter, total_losses_t, cet1, cet1_ratio.
    banks:
        List of Bank objects used in the run (provides starting CET1 and RWA).
    hurdle:
        CET1 ratio hurdle (e.g., 0.07 for 7%).
        
    Returns
    -------
    pd.DataFrame
        One row per (scenario, bank) with:
        - start_cet1_ratio
        - trough_quarter
        - trough_cet1
        - trough_cet1_ratio
        - breach
        - shortfall_gbp
    """
    required = {"scenario", "bank", "quarter", "total_losses_t", "cet1", "cet1_ratio (%)"}
    missing = required.difference(results.columns)
    if missing:
        raise KeyError(f"Results missing columns: {missing}")
    
    bank_map: dict[str, bs.Bank] = {b.name: b for b in banks}

    # Locate trough row per (scenario, bank)
    tmp = results.copy()
    tmp["cet1_ratio (%)"] = pd.to_numeric(tmp["cet1_ratio (%)"], errors="coerce")
    idx = tmp.groupby(["scenario", "bank"])["cet1_ratio (%)"].idxmin()
    trough_rows = tmp.loc[idx].reset_index(drop=True)

    out_rows: list[dict] = []
    for _, r in trough_rows.iterrows():
        bank_name = r["bank"]
        if bank_name not in bank_map:
            raise KeyError(f"Bank '{bank_name}' not found in banks list")
        bank = bank_map[bank_name]
        start_ratio = bank.cet1 / bank.total_rwa * 100
        trough_cet1 = float(r["cet1"])
        trough_ratio = float(r["cet1_ratio (%)"])
        rwa = float(bank.total_rwa)

        shortfall = max(0.0, hurdle * rwa - trough_cet1)
        out_rows.append({
            "scenario": r["scenario"],
            "bank": bank_name,
            "start_cet1_ratio (%)": start_ratio,
            "trough_quarter": r["quarter"],
            "trough_cet1": trough_cet1,
            "trough_cet1_ratio (%)": trough_ratio,
            "breach (hurdle = 7%)": trough_ratio < hurdle,
            "shortfall_gbp": shortfall
        })
    return pd.DataFrame(out_rows)


    