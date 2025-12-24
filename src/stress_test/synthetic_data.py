import pandas as pd
import numpy as np
import stress_test.config as cfg

def make_synthetic_history(
        start: str = "2005Q1",
        periods: int = 80,
        seed: int | None = 184
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate synthetic macro history and bucket-level loss rates.
    Parameters:
    - start: start quarter (string)
    - periods: number of quarterly observations (integer)
    - seed: random seed for reproducibility (integer or None)

    Returns:
    - macro_df: quarterly macro data with columns defined in config.py (pd.DataFrame)
    - loss_rates_df: quarterly loss-rate data with one column per portfolio bucket (pd.DataFrame)
    """
    if seed is not None:
        np.random.seed(seed)
    
    idx = pd.period_range(start, periods=periods, freq=cfg.FREQUENCY)

    macro_df = pd.DataFrame(index=idx)
    macro_df[cfg.GDP_GROWTH] = 0.02 + 0.01 * np.random.randn(periods)
    macro_df[cfg.UNEMPLOYMENT_RATE] = 0.05 + 0.01 * np.random.randn(periods)
    macro_df[cfg.HOUSE_PRICE_GROWTH] = 0.03 + 0.015 * np.random.randn(periods)

    loss_rates_df = pd.DataFrame(index=idx)
    loss_rates_df[cfg.MORTGAGES_OO] = (0.003 + 0.20 * macro_df[cfg.UNEMPLOYMENT_RATE] - 0.10 * macro_df[cfg.HOUSE_PRICE_GROWTH] + 0.002 * np.random.randn(periods))
    loss_rates_df[cfg.CONSUMER_UNSECURED] = (0.006 + 0.35 * macro_df[cfg.UNEMPLOYMENT_RATE] - 0.05 * macro_df[cfg.GDP_GROWTH] + 0.003 * np.random.randn(periods))
    loss_rates_df[cfg.SME_LOANS] = (0.005 - 0.20 * macro_df[cfg.GDP_GROWTH] + 0.25 * macro_df[cfg.UNEMPLOYMENT_RATE] + 0.003 * np.random.randn(periods))
    loss_rates_df[cfg.LARGE_CORP_LOANS] = (0.002 - 0.25 * macro_df[cfg.GDP_GROWTH] + 0.15 * macro_df[cfg.UNEMPLOYMENT_RATE] + 0.002 * np.random.randn(periods))

    loss_rates_df = loss_rates_df.clip(lower=0.0, upper=1.0)
    return macro_df, loss_rates_df