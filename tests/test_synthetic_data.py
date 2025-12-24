import pandas as pd

import stress_test.config as cfg
from stress_test.synthetic_data import make_synthetic_history


def test_make_synthetic_history_shapes_and_columns():
    macro, losses = make_synthetic_history(start="2005Q1", periods=80, seed=184)

    # Types
    assert isinstance(macro, pd.DataFrame)
    assert isinstance(losses, pd.DataFrame)

    # Index
    assert isinstance(macro.index, pd.PeriodIndex)
    assert macro.index.equals(losses.index)
    assert macro.index[0] == pd.Period("2005Q1", freq=cfg.FREQUENCY)
    assert len(macro.index) == 80

    # Macro columns
    assert cfg.GDP_GROWTH in macro.columns
    assert cfg.UNEMPLOYMENT_RATE in macro.columns
    assert cfg.HOUSE_PRICE_GROWTH in macro.columns

    # Bucket columns (as per your config constants)
    assert cfg.MORTGAGES_OO in losses.columns
    assert cfg.CONSUMER_UNSECURED in losses.columns
    assert cfg.SME_LOANS in losses.columns
    assert cfg.LARGE_CORP_LOANS in losses.columns

    # Loss rates bounds
    assert (losses.values >= 0.0).all()
    assert (losses.values <= 1.0).all()


def test_make_synthetic_history_is_reproducible_with_seed():
    m1, l1 = make_synthetic_history(periods=20, seed=184)
    m2, l2 = make_synthetic_history(periods=20, seed=184)

    pd.testing.assert_frame_equal(m1, m2)
    pd.testing.assert_frame_equal(l1, l2)