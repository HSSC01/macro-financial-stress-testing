import pandas as pd
import pytest
import stress_test.config as cfg
from stress_test.satellite import (
    prepare_regression_data,
    fit_satellite_model,
    project_loss_rates,
)

def _dummy_macro(index):
    return pd.DataFrame(
        index=index,
        data={
            cfg.GDP_GROWTH: 0.01,
            cfg.UNEMPLOYMENT_RATE: 0.05,
            cfg.HOUSE_PRICE_GROWTH: 0.00,
        },
    )

def _dummy_loss(index):
    return pd.Series(0.01, index=index, name="loss_rate")

def test_prepare_regression_data_returns_aligned_X_y():
    idx = pd.period_range("2010Q1", periods=8, freq=cfg.FREQUENCY)
    macro = _dummy_macro(idx)
    loss = _dummy_loss(idx)
    X, y = prepare_regression_data(macro, loss)
    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.Series)
    assert X.index.equals(y.index)
    assert "const" in X.columns
    assert cfg.GDP_GROWTH in X.columns
    assert cfg.UNEMPLOYMENT_RATE in X.columns
    assert cfg.HOUSE_PRICE_GROWTH in X.columns
    

def test_fit_satellite_model_returns_results():
    idx = pd.period_range("2010Q1", periods=8, freq=cfg.FREQUENCY)
    macro = _dummy_macro(idx)
    loss = _dummy_loss(idx)
    X, y = prepare_regression_data(macro, loss)
    results = fit_satellite_model(X, y)

    assert hasattr(results, "params")
    assert "const" in results.params.index


def test_project_loss_rates_returns_series():
    hist_idx = pd.period_range("2020Q1", periods=8, freq=cfg.FREQUENCY)
    macro_hist = _dummy_macro(hist_idx)
    loss = _dummy_loss(hist_idx)
    
    X, y = prepare_regression_data(macro_hist, loss)
    model = fit_satellite_model(X, y)
    scen_idx = pd.period_range("2025Q1", periods=4, freq=cfg.FREQUENCY)
    scenario = _dummy_macro(scen_idx)
    projection = project_loss_rates(model, scenario)

    assert isinstance(projection, pd.Series)
    assert projection.index.equals(scen_idx)
    