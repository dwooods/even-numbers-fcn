"""Measure how get_even_numbers scales with input size and number size.

Run:  python3 benchmark.py

Prints wall-clock time and peak extra memory for a series of workloads.
Timing and memory are measured in separate runs, because memory tracing
(tracemalloc) slows Python down several times and would distort the timing.
Numbers vary by machine; what matters is the shape: time should grow
linearly with the number of elements.
"""

import time
import tracemalloc
from typing import Any, Callable, List, Tuple

from even_numbers import get_even_numbers

# Each workload is (label, factory). The factory builds the input, so input
# construction is excluded from the measurement.
Workload = Tuple[str, Callable[[], Any]]

WORKLOADS: List[Workload] = [
    ("100,000 ints (list)", lambda: list(range(100_000))),
    ("1,000,000 ints (list)", lambda: list(range(1_000_000))),
    ("10,000,000 ints (list)", lambda: list(range(10_000_000))),
    ("10,000,000 ints (generator)", lambda: (i for i in range(10_000_000))),
    (
        "1,000,000 mixed types",
        lambda: [1, 2, "x", None, 3.0, 4.0, True, 6] * 125_000,
    ),
    ("100,000 x 1,000-digit ints", lambda: [10**1000 + i for i in range(100_000)]),
    ("2,000 x 20,000-digit ints", lambda: [10**20_000 + i for i in range(2000)]),
]


def time_once(factory: Callable[[], Any]) -> Tuple[float, int]:
    """Return (seconds, number of evens) for one run, excluding input setup."""
    data = factory()
    start = time.perf_counter()
    result = get_even_numbers(data)
    return time.perf_counter() - start, len(result)


def peak_memory_mib(factory: Callable[[], Any]) -> float:
    """Return the peak memory allocated by the call itself, in MiB."""
    data = factory()
    tracemalloc.start()
    get_even_numbers(data)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / (1024 * 1024)


def main() -> None:
    """Run every workload and print a results table."""
    print(f"{'Workload':<30}{'Time (s)':>10}{'Evens':>12}{'Peak MiB':>10}")
    print("-" * 62)
    for label, factory in WORKLOADS:
        seconds, evens = time_once(factory)
        mib = peak_memory_mib(factory)
        print(f"{label:<30}{seconds:>10.3f}{evens:>12,}{mib:>10.1f}")


if __name__ == "__main__":
    main()
