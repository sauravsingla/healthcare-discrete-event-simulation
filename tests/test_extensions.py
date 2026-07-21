from healthcare_des.model import ScenarioConfig
from healthcare_des.optimisation import search_capacity
from healthcare_des.sensitivity import monte_carlo, one_at_a_time
from healthcare_des.synthetic import DemandPattern, generate_daily_demand


def test_synthetic_demand_is_reproducible():
    pattern = DemandPattern(days=14, seed=7)
    first = generate_daily_demand(pattern)
    second = generate_daily_demand(pattern)
    assert first.equals(second)
    assert len(first) == 14
    assert (first["observed_demand"] >= 0).all()


def test_capacity_search_returns_ranked_candidates():
    base = ScenarioConfig(days=2, daily_demand=15)
    result = search_capacity(
        base,
        mri_options=(1, 2),
        radiographer_options=(1, 2),
        radiologist_options=(1,),
        replications=1,
    )
    assert len(result) == 4
    assert result["objective_score"].is_monotonic_increasing


def test_sensitivity_outputs_expected_factors():
    base = ScenarioConfig(days=2, daily_demand=15)
    result = one_at_a_time(
        base,
        demand_multipliers=(1.0,),
        no_show_rates=(0.08,),
        replications=1,
    )
    assert set(result["factor"]) == {"daily_demand", "no_show_rate"}


def test_monte_carlo_is_seeded():
    base = ScenarioConfig(days=2, daily_demand=15)
    first = monte_carlo(base, samples=2, replications=1, seed=11)
    second = monte_carlo(base, samples=2, replications=1, seed=11)
    assert first.equals(second)
