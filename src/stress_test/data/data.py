import pandas as pd
import numpy as np
import stress_test.data.processed_data as prd
import stress_test.config as cfg
from pathlib import Path

# Macro History
processed_data = prd.load_processed_macro_data()
output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

def macro_hist():
    frames = []
    for name, df in processed_data.items():
        d = df.copy()
        d["quarter"] = pd.PeriodIndex(d["quarter"], freq=cfg.FREQUENCY)

        value_cols = [c for c in d.columns if c != "quarter"]
        d = d.set_index("quarter")[value_cols]
        d = d.rename(columns={c: f"{c}" for c in value_cols})
        frames.append(d)

    macro_hist = pd.concat(frames, axis=1, join="outer").sort_index().reset_index()
    macro_hist = macro_hist.dropna().reset_index(drop=True)
    macro_hist["quarter"] = pd.PeriodIndex(macro_hist["quarter"], freq="Q")
    macro_hist = macro_hist.set_index("quarter")
    macro_hist.to_csv(output_dir / "macro_hist.csv", index=True)

    return macro_hist


# Loss Rates
def synthetic_loss_rates(macro_hist: pd.DataFrame=macro_hist(), seed: int | None = 184) -> pd.DataFrame:
    """Generate synthetic bucket-level loss rates based on and consistent with real macro histories.

    Returns:
    - loss_rates_df: quarterly loss-rate data with one column per portfolio bucket (pd.DataFrame)
    """
    if seed is not None:
        np.random.seed(seed)
    periods = len(macro_hist)

    loss_rates_df = pd.DataFrame(index=macro_hist.index)

    loss_rates_df[cfg.MORTGAGES_OO] = (0.003 + 0.20 * macro_hist[cfg.UNEMPLOYMENT_RATE] - 0.10 * macro_hist[cfg.HOUSE_PRICE_GROWTH] + 0.002 * np.random.randn(periods))
    loss_rates_df[cfg.CONSUMER_UNSECURED] = (0.006 + 0.35 * macro_hist[cfg.UNEMPLOYMENT_RATE] - 0.05 * macro_hist[cfg.GDP_GROWTH] + 0.003 * np.random.randn(periods))
    loss_rates_df[cfg.SME_LOANS] = (0.005 - 0.20 * macro_hist[cfg.GDP_GROWTH] + 0.25 * macro_hist[cfg.UNEMPLOYMENT_RATE] + 0.003 * np.random.randn(periods))
    loss_rates_df[cfg.LARGE_CORP_LOANS] = (0.002 - 0.25 * macro_hist[cfg.GDP_GROWTH] + 0.15 * macro_hist[cfg.UNEMPLOYMENT_RATE] + 0.002 * np.random.randn(periods))

    loss_rates_df = loss_rates_df.clip(lower=0.0, upper=1.0)
    return loss_rates_df


if __name__ == "__main__":

    print(f"macro_hist index: {macro_hist().index}")
    print(f"synthetic_loss_rates index: {synthetic_loss_rates().index}")