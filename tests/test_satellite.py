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
    

def test_fit_satellite_model_stub_raises():
    idx = pd.period_range("2010Q1", periods=8, freq=cfg.FREQUENCY)
    X = _dummy_macro(idx)
    y = _dummy_loss(idx)
    with pytest.raises(NotImplementedError):
        fit_satellite_model(X, y)

def test_project_loss_rates_stub_raises():
    idx = pd.period_range("2025Q1", periods=4, freq=cfg.FREQUENCY)
    scenario = _dummy_macro(idx)
    model = object()
    with pytest.raises(NotImplementedError):
        project_loss_rates(model, scenario)