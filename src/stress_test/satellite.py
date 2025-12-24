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
"""

from __future__ import annotations
from typing import Iterable, Sequence, Tuple
import numpy as np
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
        Historical macro data indexed by quarter (PeriodIndex) with scenario columns.
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
    X = macro_history[list(regressor_cols)]
    df = X.join(loss_rate_history, how="inner")
    if dropna:
        df = df.dropna()
    X = df[list(regressor_cols)]
    y = df[loss_rate_history.name]

    if add_constant:
        X = sm.add_constant(X, has_constant="add")

    return X, y


def fit_satellite_model(
    X: pd.DataFrame,
    y: pd.Series,
) -> "sm.regression.linear_model.RegressionResultsWrapper":
    """Fit an OLS satellite model.

    Parameters
    ----------
    X:
        Regressor matrix, typically output of prepare_regression_data.
    y:
        Dependent variable (loss rate).

    Returns
    -------
    statsmodels RegressionResultsWrapper
        Fitted OLS model with coefficients, standard errors, fitted values, etc.
    """
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
    """Project loss rates for a given scenario.

    Parameters
    ----------
    model:
        A fitted statsmodels OLS model.
    scenario_df:
        Scenario macro path indexed by quarter (PeriodIndex).
    regressor_cols:
        Macro columns used for prediction (must match those used in fitting).
    add_constant:
        If True, add an intercept column when preparing prediction matrix.
    clip:
        If True, clip projected loss rates into [0, 1].

    Returns
    -------
    pd.Series
        Projected loss rates indexed by quarter.
    """
    raise NotImplementedError