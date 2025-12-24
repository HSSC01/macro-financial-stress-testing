"""A quarterly macro path generator that returns a DataFrame with a PeriodIndex (quarters) and columns:
- GDP Growth (quarter-on-quarter, real, decimal)
- Unemployment Rate (level, decimal, not percentage points)
- House Price Growth (quarter-on-quarter, nominal, decimal)
- Policy Rate (level, decimal)
- Gilt 10Y (level, decimal)
"""

import pandas as pd
import numpy as np
import stress_test.config as cfg

def quarter_index(start: str, horizon_q: int) -> pd.PeriodIndex:
    """Create a PeriodIndex of quarters starting at `start` for `horizon_q` quarters."""
    start_period = pd.Period(start, freq=cfg.FREQUENCY)
    return pd.period_range(start=start_period, periods=horizon_q, freq=cfg.FREQUENCY)


def make_baseline(start: str = "2025Q4", horizon_q: int = 12) -> pd.DataFrame:
    index = quarter_index(start, horizon_q)
    df = pd.DataFrame(
        index=index,
        data={
            cfg.GDP_GROWTH: 0.004,
            cfg.UNEMPLOYMENT_RATE: 0.045,
            cfg.HOUSE_PRICE_GROWTH: 0.003,
            cfg.POLICY_RATE: 0.035,
            cfg.GILT_10Y: 0.040
        }
    )
    validate_scenario(df)
    return df


def apply_persistent_shock(horizon_q: int, shock: float, persistence: float) -> np.ndarray:
    """Return persistent shock path of length `horizon_q`.
    Deviation at time t is: shock * persistence**t
    """
    if horizon_q <= 0:
        return np.array([], dtype=float)
    if not (0.0 <= persistence <= 1):
        raise ValueError("Persistence must be in [0,1]")
    t = np.arange(horizon_q, dtype=float)
    return float(shock) * (float(persistence)**t)


def make_adverse(baseline_df: pd.DataFrame, severity: float=1.0, persistence: float=0.85) -> pd.DataFrame:
    """Adverse scenario by applying persistent deviations to the baseline:
    baseline + (severity * shock_path)
    """
    if baseline_df is None or baseline_df.empty:
        raise ValueError("baseline_df must be a non-empty DataFrame.")
    horizon_q = len(baseline_df.index)
    impact = {
        cfg.GDP_GROWTH: -0.020 * severity,
        cfg.UNEMPLOYMENT_RATE: 0.010 * severity,
        cfg.HOUSE_PRICE_GROWTH: -0.030 * severity,
        cfg.POLICY_RATE: -0.005 * severity,
        cfg.GILT_10Y: -0.003 * severity
    }
    adverse = baseline_df.copy()
    for col, s0 in impact.items():
        if col not in adverse.columns:
            raise ValueError(f"Baseline is missing required column: {col}")
        shock_path = apply_persistent_shock(horizon_q, s0, persistence)
        adverse[col] = adverse[col].to_numpy(dtype=float) + shock_path

    # Safety
    adverse[cfg.UNEMPLOYMENT_RATE] = adverse[cfg.UNEMPLOYMENT_RATE].clip(lower=0.0)
    validate_scenario(adverse)
    return adverse


def validate_scenario(df: pd.DataFrame) -> None:
    if df is None or df.empty:
        raise ValueError("Scenario DataFrame must be non-empty.")
    missing = cfg.REQUIRED_SCENARIO_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if not isinstance(df.index, pd.PeriodIndex):
        raise ValueError("DataFrame index must be a pandas PeriodIndex.")

    freqstr = getattr(df.index, "freqstr", None)
    if not freqstr or not freqstr.startswith(cfg.FREQUENCY):
        raise ValueError(f"DataFrame index must have quarterly frequency (freqstr starting with '{cfg.FREQUENCY}').")
    if df.isnull().any().any():
        raise ValueError("DataFrame contains null values.")
