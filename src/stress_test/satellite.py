"""Satellite (credit loss) models.

Satellite models map macro conditions -> credit risk outcomes.

In this project, satellites produce *loss rates* (decimal in [0,1]) at the
portfolio-bucket level. These loss rates will later be applied to EAD to
produce credit losses that flow into capital / CET1.

This module intentionally starts with a simple, auditable approach:
- direct loss-rate regressions (OLS)

Core API
--------
- prepare_regression_data(...): align macro history and loss-rate history into X, y
- fit_satellite_model(X, y): fit an OLS model (statsmodels)
- project_loss_rates(model, scenario_df): apply model to scenario macros
- fit_bucket_models(macro_hist, loss_rates_hist): fit one model per bucket
"""

from __future__ import annotations
from typing import Sequence, Tuple
import pandas as pd
import statsmodels.api as sm

import stress_test.config as cfg


DEFAULT_REGRESSORS: Tuple[str, ...] = (
    cfg.GDP_GROWTH,
    cfg.UNEMPLOYMENT_RATE,
    cfg.HOUSE_PRICE_GROWTH,
)


def prepare_regression_data(
    macro_history: pd.DataFrame,
    loss_rate_history: pd.Series,
    regressor_cols: Sequence[str] = DEFAULT_REGRESSORS,
    *,
    add_constant: bool = True,
    dropna: bool = True,
) -> Tuple[pd.DataFrame, pd.Series]:
    """Prepare aligned regression inputs X and y.

    Parameters
    ----------
    macro_history:
        Historical macro data indexed by quarter (PeriodIndex) with regressor columns.
    loss_rate_history:
        Historical loss-rate series indexed by quarter (PeriodIndex), values in [0, 1].
    regressor_cols:
        Macro columns to include as regressors.
    add_constant:
        If True, add an intercept column using statsmodels.add_constant.
    dropna:
        If True, inner-join on index and drop rows with any missing values.

    Returns
    -------
    X:
        DataFrame of regressors aligned to y.
    y:
        Series of loss rates aligned to X.
    """
    missing = [c for c in regressor_cols if c not in macro_history.columns]
    if missing:
        raise KeyError(f"Missing macro columns: {missing}")
    if loss_rate_history.name is None:
        loss_rate_history = loss_rate_history.rename("loss_rate")

    X_raw = macro_history.loc[:, list(regressor_cols)]
    df = X_raw.join(loss_rate_history, how="inner")

    if dropna:
        df = df.dropna()
    X = df.loc[:, list(regressor_cols)].copy()
    y = df[loss_rate_history.name].copy()

    if add_constant:
        X = sm.add_constant(X, has_constant="add")

    return X, y


def fit_satellite_model(
    X: pd.DataFrame,
    y: pd.Series,
) -> "sm.regression.linear_model.RegressionResultsWrapper":
    """Fit an OLS satellite model."""
    if not isinstance(X, pd.DataFrame):
        raise TypeError("X must be a pandas DataFrame")
    if not isinstance(y, pd.Series):
        raise TypeError("y must be a pandas Series")
    
    X_aligned, y_aligned = X.align(y, join="inner", axis=0)

    if X_aligned.empty or y_aligned.empty:
        raise ValueError("X and y have no overlapping index after alignment")

    model = sm.OLS(y_aligned.astype(float), X_aligned.astype(float))
    results = model.fit()
    return results


def project_loss_rates(
    model: "sm.regression.linear_model.RegressionResultsWrapper",
    scenario_df: pd.DataFrame,
    regressor_cols: Sequence[str] = DEFAULT_REGRESSORS,
    *,
    add_constant: bool = True,
    clip: bool = True,
) -> pd.Series:
    """Project loss rates for a given scenario."""
    missing = [c for c in regressor_cols if c not in scenario_df.columns]
    if missing:
        raise KeyError(f"Missing scenario macro columns: {missing}")
    
    X = scenario_df.loc[:, list(regressor_cols)].copy()
    if add_constant:
        X = sm.add_constant(X, has_constant="add")
    
    loss_rates = pd.Series(
        model.predict(X),
        index=X.index,
        name="loss_rate"
    )

    if clip:
        loss_rates = loss_rates.clip(lower=0.0, upper=1.0)

    return loss_rates


def fit_bucket_models(
        macro_hist: pd.DataFrame,
        loss_rates_hist: pd.DataFrame,
        buckets: Sequence[str] | None = None,
        regressor_cols: Sequence[str] = DEFAULT_REGRESSORS,
        *,
        add_constant: bool = True,
        dropna: bool = True
) -> dict[str, "sm.regression.linear_model.RegressionResultsWrapper"]:
    """Fit one satellite (loss-rate) model per bucket."""

    if buckets is None:
        buckets = list(loss_rates_hist.columns)
    models: dict[str, "sm.regression.linear_model.RegressionResultsWrapper"] = {}

    for bucket in buckets:
        if bucket not in loss_rates_hist.columns:
            raise KeyError(f"Bucket '{bucket}' not found in loss_rates_hist columns")
        X, y = prepare_regression_data(
            macro_history=macro_hist,
            loss_rate_history=loss_rates_hist[bucket],
            regressor_cols=regressor_cols,
            add_constant=add_constant,
            dropna=dropna
        )
        models[bucket] = fit_satellite_model(X, y)
    return models

