"""A quarterly macro path generator that returns a DataFrame with a PeriodIndex (quarters) and columns:
- GDP Growth (quarter-on-quarter, real, decimal)
- Unemployment Rate (level, decimal, not percentage points)
- House Price Growth (quarter-on-quarter, nominal, decimal)
- Policy Rate (level, decimal)
- Gilt 10Y (level, decimal)
"""

import pandas as pd
import numpy as np

def quarter_index(start: str, horizon_q: int) -> pd.PeriodIndex:
    """Create a PeriodIndex of quarters starting at `start` for `horizon_q` quarters."""
    start_period = pd.Period(start, freq="Q")
    return pd.period_range(start=start_period, periods=horizon_q, freq="Q")
    

def make_baseline(start: str = "2025Q4", horizon_q: int = 12) -> pd.DataFrame:
    index = quarter_index(start, horizon_q)
    df = pd.DataFrame(
        index=index,
        data={
            "gdp_growth": 0.004,
            "unemployment_rate": 0.045,
            "house_price_growth": 0.003,
            "policy_rate": 0.035,
            "gilt_10y": 0.040
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
        "gdp_growth": -0.020 * severity,
        "unemployment_rate": 0.010 * severity,
        "house_price_growth": -0.030 * severity,
        "policy_rate": -0.005 * severity,
        "gilt_10y": -0.003 * severity
    }
    adverse = baseline_df.copy()
    for col, s0 in impact.items():
        if col not in adverse.columns:
            raise ValueError(f"Baseline is missing required column: {col}")
        shock_path = apply_persistent_shock(horizon_q, s0, persistence)
        adverse[col] = adverse[col].to_numpy(dtype=float) + shock_path

    # Safety
    adverse["unemployment_rate"] = adverse["unemployment_rate"].clip(lower=0.0)
    validate_scenario(adverse)
    return adverse


def validate_scenario(df: pd.DataFrame) -> None:
    if df is None or df.empty:
        raise ValueError("Scenario DataFrame must be non-empty.")
    required_columns = {
        "gdp_growth",
        "unemployment_rate",
        "house_price_growth",
        "policy_rate",
        "gilt_10y"
    }
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if not isinstance(df.index, pd.PeriodIndex):
        raise ValueError("DataFrame index must be a pandas PeriodIndex.")

    freqstr = getattr(df.index, "freqstr", None)
    if not freqstr or not freqstr.startswith("Q"):
        raise ValueError("DataFrame index must have quarterly frequency (freqstr starting with 'Q').")
    if df.isnull().any().any():
        raise ValueError("DataFrame contains null values.")
