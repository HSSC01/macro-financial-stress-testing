from stress_test.synthetic_data import make_synthetic_history
from stress_test.satellite import fit_bucket_models
from stress_test.scenarios import make_baseline, make_adverse
from stress_test.engine import project_loss_rates_all_buckets

def test_adverse_projection_differs_from_baseline():

    macro_hist, loss_hist = make_synthetic_history(periods=80, seed=184)
    models = fit_bucket_models(macro_hist, loss_hist)

    baseline = make_baseline(horizon_q=12)
    adverse = make_adverse(baseline, severity=1.0)

    projected_base = project_loss_rates_all_buckets(models, baseline)
    projected_adverse = project_loss_rates_all_buckets(models, adverse)

    assert projected_base.shape == projected_adverse.shape
    assert (projected_base != projected_adverse).to_numpy().any()