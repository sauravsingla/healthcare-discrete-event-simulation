import pytest

from healthcare_des.queueing import littles_law_residual, mm1_metrics


def test_mm1_reference_values() -> None:
    metrics = mm1_metrics(arrival_rate=2.0, service_rate=3.0)
    assert metrics.utilisation == pytest.approx(2 / 3)
    assert metrics.mean_system_time == pytest.approx(1.0)
    assert metrics.mean_waiting_time == pytest.approx(2 / 3)
    assert metrics.mean_number_in_system == pytest.approx(2.0)
    assert metrics.mean_number_in_queue == pytest.approx(4 / 3)


def test_mm1_metrics_obey_littles_law() -> None:
    metrics = mm1_metrics(arrival_rate=0.8, service_rate=1.0)
    assert littles_law_residual(
        metrics.mean_number_in_system,
        metrics.arrival_rate,
        metrics.mean_system_time,
    ) == pytest.approx(0.0)
    assert littles_law_residual(
        metrics.mean_number_in_queue,
        metrics.arrival_rate,
        metrics.mean_waiting_time,
    ) == pytest.approx(0.0)


@pytest.mark.parametrize(
    ("arrival_rate", "service_rate"),
    [
        (0.0, 1.0),
        (-1.0, 1.0),
        (1.0, 0.0),
        (1.0, -1.0),
        (1.0, 1.0),
        (2.0, 1.0),
    ],
)
def test_mm1_rejects_invalid_or_unstable_rates(
    arrival_rate: float, service_rate: float
) -> None:
    with pytest.raises(ValueError):
        mm1_metrics(arrival_rate, service_rate)


def test_littles_law_residual_reports_direction_and_magnitude() -> None:
    assert littles_law_residual(10.0, 2.0, 4.0) == pytest.approx(2.0)
    assert littles_law_residual(6.0, 2.0, 4.0) == pytest.approx(-2.0)


@pytest.mark.parametrize(
    ("mean_number", "throughput", "mean_time"),
    [(-1.0, 1.0, 1.0), (1.0, -1.0, 1.0), (1.0, 1.0, -1.0)],
)
def test_littles_law_rejects_negative_inputs(
    mean_number: float, throughput: float, mean_time: float
) -> None:
    with pytest.raises(ValueError):
        littles_law_residual(mean_number, throughput, mean_time)
