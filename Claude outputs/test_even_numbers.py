import unittest
from even_numbers import get_even_numbers


class TestGetEvenNumbers(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(get_even_numbers([1, 2, 3, 4, 5, 6]), [2, 4, 6])

    def test_empty_and_no_evens(self):
        self.assertEqual(get_even_numbers([]), [])
        self.assertEqual(get_even_numbers([1, 3, 5]), [])

    def test_zero_is_even(self):
        self.assertEqual(get_even_numbers([0]), [0])

    def test_negatives(self):
        self.assertEqual(get_even_numbers([-4, -3, -2, -1]), [-4, -2])

    def test_very_large_integers(self):
        big_even, big_odd = 10**500, 10**500 + 1
        self.assertEqual(get_even_numbers([big_even, big_odd]), [big_even])

    def test_whole_floats_count_fractions_do_not(self):
        self.assertEqual(get_even_numbers([4.0, 4.5, -2.0, 1e300]),
                         [4.0, -2.0, 1e300])

    def test_nan_and_infinity_skipped(self):
        self.assertEqual(get_even_numbers([float("nan"), float("inf"),
                                           float("-inf"), 2]), [2])

    def test_non_numbers_skipped_not_coerced(self):
        self.assertEqual(get_even_numbers(["2", None, [2], {2: 2}, 2]), [2])

    def test_booleans_are_not_numbers(self):
        self.assertEqual(get_even_numbers([True, False, 2]), [2])

    def test_duplicates_and_order_preserved(self):
        self.assertEqual(get_even_numbers([4, 2, 4, 2]), [4, 2, 4, 2])

    def test_input_not_mutated(self):
        data = [1, 2, 3, 4]
        get_even_numbers(data)
        self.assertEqual(data, [1, 2, 3, 4])

    def test_other_iterables(self):
        self.assertEqual(get_even_numbers((1, 2, 3, 4)), [2, 4])
        self.assertEqual(get_even_numbers(range(7)), [0, 2, 4, 6])
        self.assertEqual(get_even_numbers(x for x in [1, 2, 3, 4]), [2, 4])

    def test_invalid_input_raises(self):
        for bad in (None, 42, "2468", b"24"):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    get_even_numbers(bad)


if __name__ == "__main__":
    unittest.main()
