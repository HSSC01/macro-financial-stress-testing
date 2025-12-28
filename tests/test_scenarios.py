import pandas as pd
from stress_test.scenarios import make_baseline, make_adverse
import stress_test.config as cfg


def test_make_baseline_returns_expected_shape_index_and_columns() -> None:
    horizon_q = 12
    df = make_baseline(horizon_q=horizon_q)

    assert len(df) == horizon_q
    assert isinstance(df.index, pd.PeriodIndex)

    # Required columns exist (extra columns are allowed, but these must be present)
    assert cfg.REQUIRED_SCENARIO_COLUMNS.issubset(set(df.columns))


def test_make_baseline_has_no_nans() -> None:
    df = make_baseline(horizon_q=12)
    assert not df.isna().any().any()


def test_make_adverse_matches_baseline_shape_index_and_columns() -> None:
    baseline = make_baseline(horizon_q=12)
    adverse = make_adverse(baseline, severity=1.0, persistence=0.85)

    assert adverse.shape == baseline.shape
    assert isinstance(adverse.index, pd.PeriodIndex)
    assert adverse.index.equals(baseline.index)
    assert list(adverse.columns) == list(baseline.columns)


def test_directionality_checks_at_t0() -> None:
    baseline = make_baseline(horizon_q=12)
    adverse = make_adverse(baseline, severity=1.0, persistence=0.85)

    t0 = baseline.index[0]

    assert float(adverse.loc[t0, cfg.GDP_GROWTH]) <= float(baseline.loc[t0, cfg.GDP_GROWTH])
    assert float(adverse.loc[t0, cfg.UNEMPLOYMENT_RATE]) >= float(baseline.loc[t0, cfg.UNEMPLOYMENT_RATE])
    assert float(adverse.loc[t0, cfg.HOUSE_PRICE_GROWTH]) <= float(baseline.loc[t0, cfg.HOUSE_PRICE_GROWTH])
