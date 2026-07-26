from math import isclose

from region_classifier.geometry import Circle, Polygon, Rectangle, RegionField


def test_circle_distance_and_membership():
    c = Circle(0, 0, 5)
    assert isclose(c.distance_to_boundary(0, 0), 5.0)  # centre -> to boundary
    assert isclose(c.distance_to_boundary(3, 0), 2.0)  # inside
    assert isclose(c.distance_to_boundary(8, 0), 3.0)  # outside
    assert c.contains(1, 1) and not c.contains(6, 0)
    assert c.inradius == 5.0


def test_rectangle_distance_and_membership():
    r = Rectangle(0, 0, 10, 4)  # x in [-5,5], y in [-2,2]
    assert isclose(r.distance_to_boundary(0, 0), 2.0)  # nearest edge is top/bottom
    assert isclose(r.distance_to_boundary(7, 0), 2.0)  # outside to the right
    assert isclose(r.distance_to_boundary(8, 6), 5.0)  # outside corner (3,4)
    assert r.contains(4, 1) and not r.contains(6, 0)
    assert r.inradius == 2.0


def test_polygon_square_matches_rectangle():
    sq = Polygon(((-3, -3), (3, -3), (3, 3), (-3, 3)))
    assert isclose(sq.distance_to_boundary(0, 0), 3.0, abs_tol=1e-9)
    assert isclose(sq.distance_to_boundary(0, 5), 2.0, abs_tol=1e-9)
    assert sq.contains(1, 1) and not sq.contains(5, 5)
    assert isclose(sq.inradius, 3.0, abs_tol=0.1)  # numeric estimate


def test_region_field_true_label():
    f = RegionField(Circle(-10, 0, 4), Circle(10, 0, 4))
    assert f.true_label(-10, 0) == "In A"
    assert f.true_label(10, 0) == "In B"
    assert f.true_label(0, 0) == "Outside"
