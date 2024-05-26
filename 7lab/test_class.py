import pytest
from triangle_class import Triangle, IncorrectTriangleSides

def test_triangle_creation():
    triangle = Triangle(3, 4, 5)
    assert triangle.side1 == 3
    assert triangle.side2 == 4
    assert triangle.side3 == 5

def test_triangle_type():
    triangle = Triangle(5, 5, 5)
    assert triangle.triangle_type() == "equilateral"

def test_perimeter():
    triangle = Triangle(3, 4, 5)
    assert triangle.perimeter() == 12

def test_invalid_triangle_creation():
    with pytest.raises(IncorrectTriangleSides):
        Triangle(0, 0, 0)
        Triangle(-1, 2, 3)
        Triangle(1, 1, 2)

if __name__ == "__main__":
    pytest.main()
