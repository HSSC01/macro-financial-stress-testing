from stress_test.balance_sheet import make_stylised_banks
from stress_test import config as cfg

TOL = 1e-9

def _approx_equal(a: float, b: float, tol: float = TOL) -> bool:
    return abs(a - b) <= tol

def test_make_stylised_banks_returns_three_named__banks() -> None:
    banks = make_stylised_banks()
    assert isinstance(banks, list)
    assert len(banks) == 3

    names = [b.name for b in banks]
    assert names == ["HSBC", "Lloyds Banking Group", "Standard Chartered"]

def test_bank_buckets_exist_and_have_expected_fields() -> None:
    banks = make_stylised_banks()
    for b in banks:
        assert isinstance(b.buckets, dict)
        assert len(b.buckets) > 0
        for k, bucket in b.buckets.items():
            assert isinstance(k, str)
            assert hasattr(bucket, "ead")
            assert hasattr(bucket, "rw")
            assert hasattr(bucket, "lgd")

            # sanity constraints
            assert bucket.ead >= 0
            assert 0 <= bucket.rw <= 2
            assert 0 <= bucket.lgd <= 1
            assert hasattr(bucket, "rwa")
            assert _approx_equal(float(bucket.rwa), float(bucket.ead) * float(bucket.rw))

def test_total_ead_equals_sum_of_bucket_ead() -> None:
    banks = make_stylised_banks()
    for b in banks:
        ead_sum = sum(float(bucket.ead) for bucket in b.buckets.values())
        assert _approx_equal(float(b.total_ead), float(ead_sum))

def test_total_rwa_equals_sum_of_bucket_rwa() -> None:
    banks = make_stylised_banks()
    for b in banks:
        rwa_sum = sum(float(bucket.rwa) for bucket in b.buckets.values())
        assert _approx_equal(float(b.total_rwa), float(rwa_sum))

def test_cet1_ratio_definition_is_consistent() -> None:
    banks = make_stylised_banks()
    for b in banks:
        # CET1 ratio = CET1 / total RWA
        assert b.total_rwa > 0
        implied_ratio = float(b.cet1) / float(b.total_rwa)
        assert _approx_equal(float(b.cet1_ratio), float(implied_ratio))

def test_overlays_present_and_are_shares() -> None:
    banks = make_stylised_banks()
    expected_overlay_keys = {
        "high_ltv_share_of_mortgages",
        "export_share_of_large_corp",
        "energy_intensive_share_of_corp"
    }
    for b in banks:
        assert hasattr(b, "overlays")
        assert isinstance(b.overlays, dict)
        assert expected_overlay_keys.issubset(set(b.overlays.keys()))

        for k in expected_overlay_keys:
            v = float(b.overlays[k])
            assert 0 <= v <= 1

def test_bucket_names_are_stable_and_match_printed_output() -> None:
    banks = make_stylised_banks()
    expected_bucket_keys = {
        cfg.MORTGAGES_OO,
        cfg.CONSUMER_UNSECURED,
        cfg.SME_LOANS,
        cfg.LARGE_CORP_LOANS
    }
    for b in banks:
        assert set(b.buckets.keys()) == expected_bucket_keys

def test_starting_positions_match_known_totals() -> None:
    """Regression test: if config changes, this will force us to acknowledge it."""
    banks = {b.name: b for b in make_stylised_banks()}
    assert _approx_equal(banks["HSBC"].total_ead, 800.0)
    assert _approx_equal(banks["HSBC"].total_rwa, 570.0)
    assert _approx_equal(banks["HSBC"].cet1_ratio, 0.14)
    assert _approx_equal(banks["Lloyds Banking Group"].total_ead, 600.0)
    assert _approx_equal(banks["Lloyds Banking Group"].total_rwa, 255.0)
    assert _approx_equal(banks["Lloyds Banking Group"].cet1_ratio, 0.15)
    assert _approx_equal(banks["Standard Chartered"].total_ead, 400.0)
    assert _approx_equal(banks["Standard Chartered"].total_rwa, 345.0)
    assert _approx_equal(banks["Standard Chartered"].cet1_ratio, 0.13)


