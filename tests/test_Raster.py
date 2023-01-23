from rok4.Raster import Raster

import pytest

def test_empty_constructor():
    catched_error = False
    try:
        raster_object = Raster()
    except TypeError as exc:
        catched_error = True
    finally:
        assert catched_error

def test_nominal_constructor():
    path = "file:///tmp/image.jpg"
    raster_object = Raster(path)
    assert raster_object.path == path
    assert raster_object.bbox is not None
    assert raster_object.samples is not None
    assert raster_object.mask is not None


