"""Return the even numbers in an array, with edge cases handled.

Design decisions, complexity and benchmarks are in README.md.
Run the demo with ``python3 even_numbers.py`` and the tests with
``python3 -m unittest -v``.
"""

from collections.abc import Mapping
from math import isfinite
from numbers import Integral, Rational, Real
from typing import Any, Iterable, List

__all__ = ["get_even_numbers"]

# Iterable, but not arrays of numbers: iterating yields characters, byte
# values or dict keys, which would give silently wrong answers.
_REJECTED_CONTAINERS = (str, bytes, bytearray, memoryview, Mapping)


def _is_even_number(value: Any) -> bool:
    """Return True for an even integer or a finite, whole, even float."""
    # Fast path for plain int/float (~5x faster). Exact type check, so bool
    # never takes this branch.
    if type(value) is int:
        return bool(value % 2 == 0)
    if type(value) is float:
        return isfinite(value) and value.is_integer() and value % 2 == 0
    # bool is an int subclass (True == 1), so exclude it explicitly.
    if isinstance(value, bool):
        return False
    # Integral, not int: NumPy integers are not int subclasses.
    if isinstance(value, Integral):
        return bool(value % 2 == 0)
    # NumPy floats. Rational is excluded so Fraction is skipped.
    if isinstance(value, Real) and not isinstance(value, Rational):
        f = float(value)
        return isfinite(f) and f.is_integer() and f % 2 == 0
    # str, None, lists, Fraction, Decimal, complex: skipped, never converted.
    return False


def get_even_numbers(items: Iterable[Any]) -> List[Any]:
    """Return a new list of the even numbers in ``items``, in input order.

    Non-numbers are skipped. The input is not modified.

    Args:
        items: Any iterable, such as a list, tuple, range, generator or
            NumPy array.

    Returns:
        The even numbers, as the same objects that were in the input.

    Raises:
        TypeError: If ``items`` is not iterable, or is a str, bytes-like
            object or mapping.

    Examples:
        >>> get_even_numbers([1, 2, 3, 4, -6, 0, 8.0, 9.5, "10", None, True])
        [2, 4, -6, 0, 8.0]
        >>> get_even_numbers(None)
        Traceback (most recent call last):
            ...
        TypeError: expected an array of values, got NoneType

    """
    error = f"expected an array of values, got {type(items).__name__}"
    if isinstance(items, _REJECTED_CONTAINERS):
        raise TypeError(error)
    try:
        iterator = iter(items)
    except TypeError:
        raise TypeError(error) from None
    return [value for value in iterator if _is_even_number(value)]


if __name__ == "__main__":
    sample = [1, 2, 3, 4, -6, -7, 0, 8.0, 9.5, "10", None, True, [12]]
    sample += [float("nan"), float("inf"), 10**40, 10**40 + 1]
    print("input :", sample)
    print("output:", get_even_numbers(sample))
