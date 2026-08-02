"""Analytical queueing references used to verify simplified simulation cases.

These functions are deliberately small and dependency-free. They are not a
replacement for the discrete-event model; they provide transparent reference
values for controlled M/M/1 experiments and Little's Law checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class MM1Metrics:
    """Steady-state M/M/1 metrics expressed in a common time unit."""

    arrival_rate: float
    service_rate: float
    utilisation: float
    mean_number_in_system: float
    mean_number_in_queue: float
    mean_system_time: float
    mean_waiting_time: float


def mm1_metrics(arrival_rate: float, service_rate: float) -> MM1Metrics:
    """Return standard stable M/M/1 steady-state metrics.

    Parameters
    ----------
    arrival_rate:
        Mean arrivals per chosen time unit.
    service_rate:
        Mean services per the same time unit.

    Raises
    ------
    ValueError
        If rates are non-positive or the queue is unstable (`arrival_rate >= service_rate`).
    """

    if not isfinite(arrival_rate) or arrival_rate <= 0:
        raise ValueError("arrival_rate must be a finite positive number")
    if not isfinite(service_rate) or service_rate <= 0:
        raise ValueError("service_rate must be a finite positive number")
    if arrival_rate >= service_rate:
        raise ValueError("M/M/1 steady state requires arrival_rate < service_rate")

    utilisation = arrival_rate / service_rate
    mean_system_time = 1.0 / (service_rate - arrival_rate)
    mean_waiting_time = arrival_rate / (service_rate * (service_rate - arrival_rate))
    mean_number_in_system = arrival_rate * mean_system_time
    mean_number_in_queue = arrival_rate * mean_waiting_time

    return MM1Metrics(
        arrival_rate=arrival_rate,
        service_rate=service_rate,
        utilisation=utilisation,
        mean_number_in_system=mean_number_in_system,
        mean_number_in_queue=mean_number_in_queue,
        mean_system_time=mean_system_time,
        mean_waiting_time=mean_waiting_time,
    )


def littles_law_residual(mean_number: float, throughput: float, mean_time: float) -> float:
    """Return the signed residual `L - lambda * W` for Little's Law.

    All values must use compatible units. A result close to zero supports
    internal flow consistency; it does not by itself establish external validity.
    """

    values = (mean_number, throughput, mean_time)
    if any(not isfinite(value) or value < 0 for value in values):
        raise ValueError("Little's Law inputs must be finite and non-negative")
    return mean_number - throughput * mean_time
