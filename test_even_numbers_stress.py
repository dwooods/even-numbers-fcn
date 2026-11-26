"""Stress, adversarial and fuzz tests for get_even_numbers.

Run all:            python3 -m unittest -v
Run only these:     python3 -m unittest -v test_even_numbers_stress

Note on huge integers: Python 3.11+ refuses to convert integers with more
than 4,300 digits to text, so these tests never print or format them. A
failing assertion on a huge number would otherwise crash while building
its own error message. Assertions compare lengths and identity instead.
"""

import enum
import itertools
import math
import random
import unittest
from decimal import Decimal
from fractions import Fraction

from even_numbers import get_even_numbers

try:
    import numpy as np
except ImportError:  # NumPy is optional; those tests are skipped without it.
    np = None


def reference_even_numbers(items):
    """Independent, deliberately plain implementation to compare against.

    Uses exact type checks and a bitwise test instead of the production
    code's isinstance and modulo checks, so a shared mistake is unlikely.
    """
    out = []
    for v in items:
        t = type(v)
        if t is int:
            if v & 1 == 0:
                out.append(v)
        elif t is float and v - v == 0 and v == int(v) and int(v) & 1 == 0:
            # `v - v == 0` is False for nan and inf, so int(v) never fails.
            out.append(v)
    return out


class TestLongArrays(unittest.TestCase):
    N = 1_000_000

    def test_one_million_alternating_ints(self):
        data = list(range(self.N))
        result = get_even_numbers(data)
        self.assertEqual(len(result), self.N // 2)
        self.assertEqual(result[:3], [0, 2, 4])
        self.assertEqual(result[-1], self.N - 2)
        self.assertEqual(result, list(range(0, self.N, 2)))

    def test_one_million_all_odd_returns_empty(self):
        self.assertEqual(get_even_numbers(range(1, self.N * 2, 2)), [])

    def test_one_million_all_even_returns_everything(self):
        data = list(range(0, self.N * 2, 2))
        self.assertEqual(get_even_numbers(data), data)

    def test_one_million_same_value_repeated(self):
        self.assertEqual(len(get_even_numbers([4] * self.N)), self.N)
        self.assertEqual(get_even_numbers([3] * self.N), [])

    def test_one_million_negatives(self):
        data = list(range(-self.N, 0))
        result = get_even_numbers(data)
        self.assertEqual(len(result), self.N // 2)
        self.assertEqual(result[0], -self.N)
        self.assertEqual(result[-1], -2)

    def test_one_million_mixed_types(self):
        cycle = [1, 2, "x", None, 3.0, 4.0, True, 6]  # evens: 2, 4.0, 6
        data = cycle * 125_000
        result = get_even_numbers(data)
        self.assertEqual(len(result), 3 * 125_000)
        self.assertEqual(result[:3], [2, 4.0, 6])

    def test_ten_million_from_generator(self):
        # A generator is never held in memory as a whole list.
        result = get_even_numbers(i for i in range(10_000_000))
        self.assertEqual(len(result), 5_000_000)
        self.assertEqual(result[-1], 9_999_998)

    def test_long_input_is_not_mutated(self):
        data = list(range(self.N))
        snapshot = list(data)
        get_even_numbers(data)
        self.assertEqual(data, snapshot)

    def test_result_is_a_new_list_even_when_everything_is_even(self):
        data = [2, 4, 6]
        result = get_even_numbers(data)
        self.assertEqual(result, data)
        self.assertIsNot(result, data)


class TestHugeNumbers(unittest.TestCase):
    def test_single_hundred_thousand_digit_integers(self):
        even, odd = 10**100_000, 10**100_000 + 1
        result = get_even_numbers([odd, even, odd])
        self.assertEqual(len(result), 1)
        self.assertIs(result[0], even)  # identity: never stringified

    def test_many_five_thousand_digit_integers(self):
        base = 10**5000
        data = [base + i for i in range(1000)]
        self.assertEqual(len(get_even_numbers(data)), 500)

    def test_one_hundred_thousand_thousand_digit_integers(self):
        base = 10**1000
        data = [base + i for i in range(100_000)]
        result = get_even_numbers(data)
        self.assertEqual(len(result), 50_000)
        self.assertTrue(all(v % 2 == 0 for v in result))

    def test_huge_negative_integers(self):
        even, odd = -(10**5000), -(10**5000) - 1
        result = get_even_numbers([odd, even])
        self.assertEqual(len(result), 1)
        self.assertIs(result[0], even)

    def test_two_to_the_64(self):
        # Just past the 64-bit range where many languages overflow.
        data = [2**64, 2**64 + 1, -(2**64), 2**63 - 1]
        self.assertEqual(get_even_numbers(data), [2**64, -(2**64)])

    def test_float_extremes(self):
        self.assertEqual(get_even_numbers([1e308, -1e308]), [1e308, -1e308])
        self.assertEqual(get_even_numbers([5e-324]), [])  # subnormal, not whole
        self.assertEqual(
            get_even_numbers([1.7976931348623157e308]), [1.7976931348623157e308]
        )

    def test_float_past_two_to_the_53(self):
        # 2**53 + 1 is not representable; it rounds to 2**53, which is even.
        self.assertEqual(get_even_numbers([float(2**53 + 1)]), [float(2**53)])

    def test_negative_zero_is_even(self):
        result = get_even_numbers([-0.0])
        self.assertEqual(len(result), 1)
        self.assertEqual(math.copysign(1, result[0]), -1.0)  # sign preserved


class TestStructuralAttacks(unittest.TestCase):
    def test_deeply_nested_list_is_skipped_without_recursion(self):
        nested = []
        for _ in range(100_000):
            nested = [nested]
        self.assertEqual(get_even_numbers([nested, 2]), [2])

    def test_self_referential_list_is_skipped(self):
        loop = []
        loop.append(loop)
        self.assertEqual(get_even_numbers([loop, 2, loop]), [2])

    def test_generator_error_midway_propagates(self):
        def broken():
            yield 2
            yield 4
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            get_even_numbers(broken())

    def test_generator_is_fully_consumed_once(self):
        gen = (i for i in range(10))
        self.assertEqual(get_even_numbers(gen), [0, 2, 4, 6, 8])
        self.assertEqual(get_even_numbers(gen), [])  # already exhausted

    def test_itertools_chain_input(self):
        self.assertEqual(get_even_numbers(itertools.chain([1, 2], (3, 4))), [2, 4])

    def test_set_input_returns_evens_in_some_order(self):
        self.assertEqual(sorted(get_even_numbers({1, 2, 3, 4})), [2, 4])

    def test_nested_lists_are_not_flattened(self):
        self.assertEqual(get_even_numbers([[2, 4], 6]), [6])


class TestRejectedContainers(unittest.TestCase):
    """Found by probing: these used to return wrong answers silently."""

    def test_bytearray_is_rejected_not_read_as_byte_values(self):
        with self.assertRaises(TypeError):
            get_even_numbers(bytearray(b"24"))

    def test_memoryview_is_rejected(self):
        with self.assertRaises(TypeError):
            get_even_numbers(memoryview(b"24"))

    def test_dict_is_rejected_not_read_as_its_keys(self):
        with self.assertRaises(TypeError):
            get_even_numbers({2: "a", 3: "b"})

    def test_string_subclass_is_rejected(self):
        class MyStr(str):
            pass

        with self.assertRaises(TypeError):
            get_even_numbers(MyStr("2468"))

    def test_other_non_iterables_raise(self):
        for bad in (None, 42, 4.0, True, object()):
            with self.subTest(bad=type(bad).__name__), self.assertRaises(TypeError):
                get_even_numbers(bad)


class TestOtherNumberTypes(unittest.TestCase):
    def test_int_subclass_is_kept(self):
        class Color(enum.IntEnum):
            TWO = 2
            THREE = 3

        self.assertEqual(get_even_numbers([Color.TWO, Color.THREE]), [Color.TWO])

    def test_fraction_decimal_complex_are_skipped(self):
        # Documented decision: only int-like and float-like numbers count.
        data = [Fraction(4, 1), Decimal(4), complex(4, 0)]
        self.assertEqual(get_even_numbers(data), [])

    @unittest.skipIf(np is None, "NumPy not installed")
    def test_numpy_integer_array_is_not_silently_dropped(self):
        result = get_even_numbers(np.array([1, 2, 3, 4], dtype=np.int64))
        self.assertEqual([int(v) for v in result], [2, 4])

    @unittest.skipIf(np is None, "NumPy not installed")
    def test_numpy_scalars_in_a_list(self):
        data = [np.int64(2), np.int32(3), np.uint8(4), np.float32(6.0), np.float64(7.5)]
        self.assertEqual([float(v) for v in get_even_numbers(data)], [2.0, 4.0, 6.0])

    @unittest.skipIf(np is None, "NumPy not installed")
    def test_numpy_float_array_with_nan_and_inf(self):
        arr = np.array([2.0, np.nan, np.inf, -np.inf, 3.0, 4.0])
        self.assertEqual([float(v) for v in get_even_numbers(arr)], [2.0, 4.0])

    @unittest.skipIf(np is None, "NumPy not installed")
    def test_numpy_fractional_floats_are_skipped(self):
        arr = np.array([2.0, 4.5, -2.5, 6.0, -8.0])
        self.assertEqual([float(v) for v in get_even_numbers(arr)], [2.0, 6.0, -8.0])
        self.assertEqual(get_even_numbers([np.float32(4.5), np.float32(4.0)]), [4.0])

    @unittest.skipIf(np is None, "NumPy not installed")
    def test_numpy_bool_array_is_skipped_like_python_bool(self):
        self.assertEqual(get_even_numbers(np.array([True, False])), [])

    @unittest.skipIf(np is None, "NumPy not installed")
    def test_numpy_2d_array_rows_are_skipped_not_flattened(self):
        self.assertEqual(get_even_numbers(np.array([[2, 4], [6, 8]])), [])

    @unittest.skipIf(np is None, "NumPy not installed")
    def test_large_numpy_array(self):
        result = get_even_numbers(np.arange(1_000_000))
        self.assertEqual(len(result), 500_000)


class TestFuzz(unittest.TestCase):
    """Random mixed inputs compared against an independent implementation.

    Seeded, so a failure is reproducible: the seed is in the message.
    """

    @staticmethod
    def random_item(rng):
        kind = rng.randrange(13)
        if kind == 0:
            return rng.randint(-1000, 1000)
        if kind == 1:
            return rng.randint(-(10**30), 10**30)
        if kind == 2:
            return rng.choice([10**400, 10**400 + 1, -(10**400)])
        if kind == 3:
            return float(rng.randint(-1000, 1000))
        if kind == 4:
            return rng.uniform(-1000, 1000)
        if kind == 5:
            return rng.choice(
                [float("nan"), float("inf"), float("-inf"), 0.0, -0.0, 1e300, 5e-324]
            )
        if kind == 6:
            return rng.choice(["2", "", "abc", "٢"])
        if kind == 7:
            return None
        if kind == 8:
            return rng.choice([True, False])
        if kind == 9:
            return [rng.randint(0, 10)]
        if kind == 10:
            return (rng.randint(0, 10),)
        if kind == 11:
            return {rng.randint(0, 10): 1}
        return rng.randint(0, 1)

    def test_random_inputs_match_reference(self):
        for seed in range(300):
            rng = random.Random(seed)
            data = [self.random_item(rng) for _ in range(rng.randrange(0, 600))]
            expected = reference_even_numbers(data)
            actual = get_even_numbers(data)
            with self.subTest(seed=seed):
                self.assertEqual(len(actual), len(expected))
                # Same objects in the same order; identity avoids formatting
                # huge integers if something ever differs.
                for a, e in zip(actual, expected):
                    self.assertIs(a, e)

    def test_output_is_always_a_subsequence_of_the_input(self):
        rng = random.Random(12345)
        data = [self.random_item(rng) for _ in range(5000)]
        result = get_even_numbers(data)
        it = iter(data)
        for value in result:
            self.assertTrue(
                any(value is x for x in it), "result item is not in input order"
            )

    def test_every_returned_value_is_even_and_numeric(self):
        rng = random.Random(777)
        data = [self.random_item(rng) for _ in range(20_000)]
        for v in get_even_numbers(data):
            self.assertNotIsInstance(v, bool)
            self.assertIsInstance(v, (int, float))
            self.assertEqual(v % 2, 0)


if __name__ == "__main__":
    unittest.main()
