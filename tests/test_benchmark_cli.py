from pathlib import Path

import pytest

from healthcare_des.benchmark_cli import build_parser, positive_int


def test_positive_int_accepts_positive_values() -> None:
    assert positive_int("3") == 3


@pytest.mark.parametrize("value", ["0", "-1"])
def test_positive_int_rejects_non_positive_values(value: str) -> None:
    with pytest.raises(Exception, match="positive integer"):
        positive_int(value)


def test_parser_defaults() -> None:
    args = build_parser().parse_args(["--config", "scenario.yml"])
    assert args.config == "scenario.yml"
    assert args.replications == 20
    assert Path(args.output) == Path("outputs/benchmark.csv")
