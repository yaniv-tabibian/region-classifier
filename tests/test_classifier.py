"""The classifier tested in isolation on crafted distance streams with known
labels -- no simulator, no geometry."""

from region_classifier.classifier import RegionClassifier


def feed(clf, da, db):
    return [clf.update(a, b) for a, b in zip(da, db, strict=True)]


def test_enter_A_then_leave_to_outside():
    clf = RegionClassifier(inradius_a=5, inradius_b=5)
    #        outside -> approach A -> cross -> inside A -> leave (d_a > inradius)
    da = [10, 6, 2, 0.05, 1.0, 3.0, 8.0]
    db = [12] * 7
    labels = feed(clf, da, db)
    assert labels[4] == "In A"  # just after the crossing
    assert labels[-1] == "Outside"  # anchor: d_a > inradius


def test_adjacent_A_to_B_via_shared_edge():
    clf = RegionClassifier(inradius_a=5, inradius_b=5)
    # into A, then cross the shared edge (both distances dip to ~0) into B
    da = [10, 6, 2, 0.05, 2.0, 0.05, 3.0, 4.5, 4.5]
    db = [12, 12, 12, 12, 12, 4.0, 0.05, 3.0, 4.5]
    labels = feed(clf, da, db)
    assert labels[4] == "In A"
    assert labels[-1] == "In B"


def test_graze_does_not_toggle():
    clf = RegionClassifier(inradius_a=5, inradius_b=5)
    # fine steps, approach the boundary but turn around well before it
    da = [10, 9, 8.5, 8.4, 8.5, 9, 10]
    db = [12] * 7
    assert all(lbl == "Outside" for lbl in feed(clf, da, db))


def test_anchor_forces_outside_regardless_of_history():
    clf = RegionClassifier(inradius_a=5, inradius_b=5)
    da = [10, 5, 1, 0.05, 1.0, 20.0]  # enter A, then jump far outside
    db = [12] * 6
    labels = feed(clf, da, db)
    assert labels[4] == "In A"
    assert labels[5] == "Outside"


def test_starts_outside():
    clf = RegionClassifier(inradius_a=5, inradius_b=5)
    assert clf.update(9, 9) == "Outside"
