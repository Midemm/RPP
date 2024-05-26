import unittest
from triangle_func import get_triangle_type, IncorrectTriangleSides

class TestGetTriangleType(unittest.TestCase):

    def test_equilateral_triangle(self):
        self.assertEqual(get_triangle_type(5, 5, 5), "equilateral")

    def test_isosceles_triangle(self):
        self.assertEqual(get_triangle_type(5, 5, 3), "isosceles")

    def test_nonequilateral_triangle(self):
        self.assertEqual(get_triangle_type(3, 4, 5), "nonequilateral")

    def test_invalid_triangle_sides(self):
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(0, 0, 0)
            get_triangle_type(-1, 2, 3)
            get_triangle_type(1, 1, 2)

if __name__ == '__main__':
    unittest.main()
