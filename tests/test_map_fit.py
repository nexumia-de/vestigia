"""Zoom and centre for a day's positions."""
from vestigia.map import fit


def test_bounds():
    assert fit.bounds([]) is None
    assert fit.bounds([(1, 2), (3, -4)]) == (1, -4, 3, 2)


def test_fit_recorded_walk():
    # The bounds of the recorded day (tests/data/dawarich/timeline.json).
    box = (37.168572, -3.596221, 37.17575, -3.54178)
    lat, lon, zoom = fit.fit(box, 360, 600)
    assert abs(lat - 37.172) < 0.01 and abs(lon + 3.569) < 0.01
    # 0.0544° of longitude is 317 px at zoom 13, more than the 296 px
    # inside the padding; 159 px at zoom 12.
    assert zoom == 12.0


def test_single_point_is_not_zoomed_in_endlessly():
    assert fit.fit((52.5, 13.4, 52.5, 13.4), 360, 600)[2] == fit.MAX_FIT_ZOOM
