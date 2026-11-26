# Even numbers

`get_even_numbers(items)` returns a new list of the even numbers in any
array-like input, in input order, and skips every value that is not a real
number. Standard library only; Python 3.9+.

```python
>>> from even_numbers import get_even_numbers
>>> get_even_numbers([1, 2, 3, 4, -6, 0, 8.0, 9.5, "10", None, True])
[2, 4, -6, 0, 8.0]
```

## Run it

Set up once (only needed for the 7 NumPy tests):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install numpy
```

Validate:

```bash
python --version                     # 3.9 or later
python even_numbers.py               # demo
python -m unittest -v                # 55 tests: unit, doctests, stress, fuzz (~3 s)
python -m unittest -v test_even_numbers          # core rules + doctests only
python -m unittest -v test_even_numbers_stress   # stress, NumPy and fuzz only
python -m doctest -v even_numbers.py # docstring examples only
python benchmark.py                  # timing and memory by input size
```

Code-quality checks (`python -m pip install ruff mypy`):

```bash
ruff check .
ruff format --check .
mypy
```

`python -m unittest -v` should end with `Ran 55 tests` and `OK`. Without NumPy
it ends with `OK (skipped=7)`, which is also a pass.

## Behavior

| Input | Result |
| --- | --- |
| `int` of any size, incl. negatives and 0 | kept if even |
| NumPy integers (`np.int64`, ...) | treated as integers |
| `float` / NumPy floats | kept only if finite, whole and even (`4.0` yes, `4.5`, `nan`, `inf` no) |
| `bool` | skipped (`True` is the integer 1 in Python) |
| `Fraction`, `Decimal`, `complex` | skipped (scope decision) |
| `str`, `None`, nested lists, dicts as elements | skipped, never converted |
| Container is `None`, a number, `str`, `bytes`, `bytearray`, `memoryview` or a `dict` | `TypeError` |

Two kinds of bad input are handled differently on purpose. A wrong
**container** is a caller bug and fails loudly. A bad **element** is treated
as messy data and is skipped.

## Design decisions

- **Python** because its integers are arbitrary precision: a 100,000-digit
  number is exact. In JavaScript, numbers above 2^53 lose precision without
  BigInt, and `-3 % 2` is `-1`.
- **Skip, don't coerce.** Converting `"4"` to `4` would hide bad data.
- **Reject bytes-like containers and mappings.** Found by adversarial testing:
  `bytearray(b"24")` used to return `[50, 52]` (byte values) and a `dict`
  returned its keys.
- **Support NumPy without importing it.** Found by testing: `np.int64` is not
  a Python `int`, so a plain `isinstance(v, int)` silently returned `[]` for
  `np.array([1, 2, 3, 4])`. The check now uses the `numbers.Integral` ABC.
- **Return the input's own objects.** `4.0` stays a float and `np.int64(2)`
  stays a NumPy integer, so the return type is `List[Any]` rather than a
  narrower type that would be wrong for NumPy input.
- **Keep the code short; put the reasoning here.** `even_numbers.py` is about
  40 lines of code with one-line comments on the non-obvious checks. This
  README carries the full rationale.
- **Fast path for `int` and `float`.** The ABC checks made 10M ints about
  3.5x slower (0.9 s to 3.3 s); an exact-type fast path brought it to 0.64 s.

## Order of the checks

1. Exact `int` / `float`: fast path (`type(v) is int` is False for `bool`).
2. `bool`: rejected, because `isinstance(True, int)` is True.
3. `numbers.Integral`: other integers, including NumPy and `IntEnum`.
4. `numbers.Real` but not `Rational`: other floats, including NumPy floats.
5. Anything else: skipped.

## Complexity

O(n) time, one pass. O(k) extra space for the k evens returned. For integers
with d digits the modulo check is O(d).

## Benchmark (Linux, Python 3.13)

| Workload | Time (s) | Evens | Peak MiB |
| --- | ---: | ---: | ---: |
| 1,000,000 ints | 0.06 | 500,000 | 4.0 |
| 10,000,000 ints (list) | 0.64 | 5,000,000 | 41.9 |
| 10,000,000 ints (generator) | 0.88 | 5,000,000 | 194.5 |
| 1,000,000 mixed types | 0.16 | 375,000 | 3.1 |
| 100,000 x 1,000-digit ints | 0.07 | 50,000 | 0.4 |

The generator row allocates more because the integers are created during the
call rather than already existing in an input list.

## Tests

- `test_even_numbers.py`: one test per documented rule, plus the docstring
  examples (doctests).
- `test_even_numbers_stress.py`: 1M and 10M element inputs, 100,000-digit
  integers, float extremes (`-0.0`, `2**53 + 1`, subnormals), deep and
  self-referential nesting, generator failures, rejected containers, NumPy,
  and a seeded fuzz test against an independent reference implementation.

Verified on Python 3.9, 3.10, 3.11, 3.12 and 3.13 (Linux) and 3.15.2 (macOS, Apple Silicon, with NumPy 2.5.5).

## Known limits

- Nested lists are not flattened.
- Memory is O(k) for the k evens returned, because the result is a fully
  built `list`. Nothing is indexed, so nothing can go out of bounds. The one
  way to exhaust memory is an unbounded generator of evens: with a 1 GiB cap
  it raised `MemoryError` after about 2 seconds. An unbounded generator of odd
  numbers uses flat memory but never returns. If that mattered, a streaming
  version that yields evens one at a time would use constant memory.

## How this was built

Built with Claude (Anthropic) as a coding assistant.
