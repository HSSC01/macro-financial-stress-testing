import pandas as pd
import stress_test.balance_sheet as bs
from stress_test.satellite import project_loss_rates, fit_bucket_models
from stress_test.synthetic_data import make_synthetic_history
from stress_test.scenarios import make_baseline, make_adverse


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


# Capital Dynamics

def simulate_cet1_path(cet1_0: float, total_losses: pd.Series) -> pd.Series:
    """CET1_t = CET1_0 - cumulative_losses_t"""
    return pd.Series(cet1_0 - total_losses.cumsum(), index=total_losses.index, name="cet1")

def compute_cet1_ratio(cet1_path: pd.Series, rwa: float) -> pd.Series:
    if rwa <= 0:
        raise ValueError("RWA must be positive")
    return pd.Series(cet1_path / rwa, index=cet1_path.index, name="cet1_ratio")

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
    out["cet1_ratio"] = cet1_ratio
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
                "cet1_ratio": bank_out["cet1_ratio"]
            })
            rows.append(tidy)
    return pd.concat(rows, ignore_index=True)

# Convenience: full pipeline up to projected loss rates

def fit_models_from_synthetic_history(periods: int = 80, seed: int = 184):
    macro_hist, loss_hist = make_synthetic_history(periods=periods, seed=seed)
    return fit_bucket_models(macro_hist, loss_hist)

def build_projected_loss_rates(models: dict, horizon_q: int = 12, severity: float = 1.0) -> dict[str, pd.DataFrame]:
    baseline = make_baseline(horizon_q=horizon_q)
    adverse = make_adverse(baseline, severity=severity)
    return {
        "baseline": project_loss_rates_all_buckets(models, baseline),
        "adverse": project_loss_rates_all_buckets(models, adverse)
    }

if __name__ == "__main__":
    models = fit_models_from_synthetic_history(periods=80, seed=184)
    projected = build_projected_loss_rates(models, horizon_q=12, severity=1.0)
    banks = bs.make_stylised_banks()
    results = run_system(banks, projected)
    print(results.head())