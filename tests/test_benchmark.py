import pytest

from healthcare_des.benchmark import benchmark_scenarios
from healthcare_des.model import ScenarioConfig


def test_default_benchmark_compares_multiple_scenarios():
    base = ScenarioConfig(days=2, daily_demand=15)
    result = benchmark_scenarios(base, replications=1)

    assert len(result) == 8
    assert "baseline" in set(result["name"])
    assert "high-demand" in set(result["name"])
    assert "extra-mri" in set(result["name"])
    assert "mean_wait_minutes_vs_baseline_pct" in result
    assert "throughput_per_day_vs_baseline_pct" in result

    baseline = result.loc[result["name"] == "baseline"].iloc[0]
    assert baseline["mean_wait_minutes_vs_baseline_pct"] == pytest.approx(0.0)
    assert baseline["throughput_per_day_vs_baseline_pct"] == pytest.approx(0.0)


def test_custom_benchmark_is_reproducible():
    base = ScenarioConfig(days=2, daily_demand=15)
    scenarios = {
        "baseline": {},
        "stress": {"daily_demand_multiplier": 1.3, "no_show_rate": 0.12},
    }

    first = benchmark_scenarios(base, scenarios=scenarios, replications=1)
    second = benchmark_scenarios(base, scenarios=scenarios, replications=1)
    assert first.equals(second)


@pytest.mark.parametrize(
    "scenarios, message",
    [
        ({}, "at least one"),
        ({"stress": {"daily_demand_multiplier": 1.2}}, "baseline"),
        ({"baseline": {"unknown": 1}}, "Unsupported"),
        ({"baseline": {"daily_demand_multiplier": 0}}, "positive"),
    ],
)
def test_invalid_benchmark_definitions_are_rejected(scenarios, message):
    base = ScenarioConfig(days=2, daily_demand=15)
    with pytest.raises(ValueError, match=message):
        benchmark_scenarios(base, scenarios=scenarios, replications=1)


def test_invalid_replication_count_is_rejected():
    with pytest.raises(ValueError, match="replications"):
        benchmark_scenarios(ScenarioConfig(), replications=0)
