import os
from unittest import mock
from unittest.mock import *

import pytest

from rok4.enums import ColorFormat
from rok4.exceptions import FormatError, MissingAttributeError, MissingEnvironmentError
from rok4.style import Style


@mock.patch.dict(os.environ, {}, clear=True)
def test_missing_env():
    with pytest.raises(MissingEnvironmentError):
        Style("normal")


@mock.patch.dict(os.environ, {"ROK4_STYLES_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch(
    "rok4.style.exists",
    return_value=False,
)
def test_wrong_file(mocked_exists):
    with pytest.raises(FileNotFoundError):
        Style("toto")

    mocked_exists.assert_has_calls(
        [call("file:///path/to/toto"), call("file:///path/to/toto.json")]
    )


@mock.patch.dict(os.environ, {"ROK4_STYLES_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch(
    "rok4.style.exists",
    return_value=True,
)
@mock.patch(
    "rok4.style.get_data_str",
    return_value='"palette":"",}',
)
def test_bad_json(mocked_get_data_str, mocked_exists):
    with pytest.raises(FormatError):
        Style("normal")
    mocked_get_data_str.assert_called_once_with("file:///path/to/normal")


@mock.patch.dict(os.environ, {"ROK4_STYLES_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch(
    "rok4.style.exists",
    return_value=True,
)
@mock.patch(
    "rok4.style.get_data_str",
    return_value="""
    {
        "title": "Données Brutes",
        "abstract": "Données brutes sans changement de palette",
        "keywords": ["Défaut"],
        "legend": {
            "format": "image/png",
            "url": "http://serveur.fr/image.png",
            "height": 100,
            "width": 100,
            "min_scale_denominator": 0,
            "max_scale_denominator": 30
        }
    }""",
)
def test_missing_identifier(mocked_get_data_str, mocked_exists):
    with pytest.raises(MissingAttributeError) as exc:
        Style("normal")
    assert str(exc.value) == "Missing attribute 'identifier' in 'file:///path/to/normal'"
    mocked_get_data_str.assert_called_once_with("file:///path/to/normal")


@mock.patch.dict(os.environ, {"ROK4_STYLES_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch(
    "rok4.style.exists",
    return_value=True,
)
@mock.patch(
    "rok4.style.get_data_str",
    return_value="""
    {
	    "identifier": "normal",
        "title": "Données Brutes",
        "abstract": "Données brutes sans changement de palette",
        "keywords": ["Défaut"],
        "legend": {
            "format": "image/png",
            "url": "http://serveur.fr/image.png",
            "height": 100,
            "width": 100,
            "min_scale_denominator": 0,
            "max_scale_denominator": 30
        },
        "palette": {
            "no_alpha": false,
            "rgb_continuous": true,
            "alpha_continuous": true,
            "colours": []
        }
    }""",
)
def test_palette_without_colour(mocked_get_data_str, mocked_exists):
    with pytest.raises(Exception) as exc:
        Style("normal")
    assert str(exc.value) == "Style 'file:///path/to/normal' palette has no colour"
    mocked_get_data_str.assert_called_once_with("file:///path/to/normal")


@mock.patch.dict(os.environ, {"ROK4_STYLES_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch(
    "rok4.style.exists",
    return_value=True,
)
@mock.patch(
    "rok4.style.get_data_str",
    return_value="""
    {
	    "identifier": "normal",
        "title": "Données Brutes",
        "abstract": "Données brutes sans changement de palette",
        "keywords": ["Défaut"],
        "legend": {
            "format": "image/png",
            "url": "http://serveur.fr/image.png",
            "height": 100,
            "width": 100,
            "min_scale_denominator": 0,
            "max_scale_denominator": 30
        },
        "palette": {
            "no_alpha": false,
            "rgb_continuous": true,
            "alpha_continuous": true,
            "colours": [
                { "value": -99999, "red": 255, "green": 300, "blue": 255, "alpha": 0 }
            ]
        }
    }""",
)
def test_palette_wrong_colour(mocked_get_data_str, mocked_exists):
    with pytest.raises(Exception) as exc:
        Style("normal")
    assert (
        str(exc.value)
        == "In style 'file:///path/to/normal', a palette colour band has an invalid value (integer between 0 and 255 expected)"
    )
    mocked_get_data_str.assert_called_once_with("file:///path/to/normal")


@mock.patch.dict(os.environ, {"ROK4_STYLES_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch(
    "rok4.style.exists",
    return_value=True,
)
@mock.patch(
    "rok4.style.get_data_str",
    return_value="""
    {
	    "identifier": "normal",
        "title": "Données Brutes",
        "abstract": "Données brutes sans changement de palette",
        "keywords": ["Défaut"],
        "legend": {
            "format": "image/png",
            "url": "http://serveur.fr/image.png",
            "height": 100,
            "width": 100,
            "min_scale_denominator": 0,
            "max_scale_denominator": 30
        },
        "palette": {
            "no_alpha": false,
            "rgb_continuous": true,
            "alpha_continuous": true,
            "colours": [
                { "value": -80000, "red": 255, "green": 255, "blue": 255, "alpha": 0 },
                { "value": -99999, "red": 255, "green": 255, "blue": 255, "alpha": 0 }
            ]
        }
    }""",
)
def test_palette_wrong_colour_order(mocked_get_data_str, mocked_exists):
    with pytest.raises(Exception) as exc:
        Style("normal")
    assert (
        str(exc.value)
        == "Style 'file:///path/to/normal' palette colours hav eto be ordered input value ascending"
    )
    mocked_get_data_str.assert_called_once_with("file:///path/to/normal")


@mock.patch.dict(os.environ, {"ROK4_STYLES_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch(
    "rok4.style.exists",
    return_value=True,
)
@mock.patch(
    "rok4.style.get_data_str",
    return_value="""
    {
	    "identifier": "normal",
        "title": "Données Brutes",
        "abstract": "Données brutes sans changement de palette",
        "keywords": ["Défaut"],
        "legend": {
            "format": "image/png",
            "url": "http://serveur.fr/image.png",
            "height": 100,
            "width": 100,
            "min_scale_denominator": 0,
            "max_scale_denominator": 30
        },
        "palette": {
            "no_alpha": false,
            "rgb_continuous": true,
            "alpha_continuous": true,
            "colours": [
                { "value": 42, "red": 255, "green": 255, "blue": 255, "alpha": 0 }
            ]
        }
    }""",
)
def test_ok_only_palette(mocked_get_data_str, mocked_exists):

    try:
        style = Style("normal")
        mocked_get_data_str.assert_called_once_with("file:///path/to/normal")

        assert not style.is_identity
        assert style.bands == 4
        assert style.format == ColorFormat.UINT8
        assert style.input_nodata == 42.0

    except Exception as exc:
        assert False, f"Style read raises an exception: {exc}"


@mock.patch.dict(os.environ, {"ROK4_STYLES_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch(
    "rok4.style.exists",
    return_value=True,
)
@mock.patch(
    "rok4.style.get_data_str",
    return_value="""
    {
	    "identifier": "normal",
        "title": "Données Brutes",
        "abstract": "Données brutes sans changement de palette",
        "keywords": ["Défaut"],
        "legend": {
            "format": "image/png",
            "url": "http://serveur.fr/image.png",
            "height": 100,
            "width": 100,
            "min_scale_denominator": 0,
            "max_scale_denominator": 30
        },
        "pente": {
            "algo": "H",
            "unit": "degree",
            "interpolation": "linear",
            "image_nodata": -50000,
            "slope_nodata": 91,
            "slope_max": 90
        }
    }""",
)
def test_ok_only_pente(mocked_get_data_str, mocked_exists):

    try:
        style = Style("normal")
        mocked_get_data_str.assert_called_once_with("file:///path/to/normal")

        assert not style.is_identity
        assert style.bands == 1
        assert style.format == ColorFormat.FLOAT32
        assert style.input_nodata == -50000

    except Exception as exc:
        assert False, f"Style read raises an exception: {exc}"


@mock.patch.dict(os.environ, {"ROK4_STYLES_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch(
    "rok4.style.exists",
    return_value=True,
)
@mock.patch(
    "rok4.style.get_data_str",
    return_value="""
    {
	    "identifier": "normal",
        "title": "Données Brutes",
        "abstract": "Données brutes sans changement de palette",
        "keywords": ["Défaut"],
        "legend": {
            "format": "image/png",
            "url": "http://serveur.fr/image.png",
            "height": 100,
            "width": 100,
            "min_scale_denominator": 0,
            "max_scale_denominator": 30
        },
        "pente": {
            "algo": "H",
            "unit": "degree",
            "interpolation": "linear",
            "image_nodata": -50000,
            "slope_nodata": 91,
            "slope_max": 90
        },
        "estompage": {
            "zenith": 45,
            "azimuth": 315,
            "image_nodata": -50000,
            "z_factor": 1,
            "interpolation": "linear"
        },
        "exposition": {
            "algo": "H",
            "image_nodata": -50000,
            "min_slope": 1
        },
        "palette": {
            "no_alpha": true,
            "rgb_continuous": true,
            "alpha_continuous": true,
            "colours": [
                { "value": 42, "red": 255, "green": 255, "blue": 255, "alpha": 0 }
            ]
        }
    }""",
)
def test_ok_all(mocked_get_data_str, mocked_exists):

    try:
        style = Style("normal")
        mocked_get_data_str.assert_called_once_with("file:///path/to/normal")

        assert not style.is_identity
        assert style.bands == 3
        assert style.format == ColorFormat.UINT8
        assert style.input_nodata == -50000

    except Exception as exc:
        assert False, f"Style read raises an exception: {exc}"


@mock.patch.dict(os.environ, {"ROK4_STYLES_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch(
    "rok4.style.exists",
    return_value=True,
)
@mock.patch(
    "rok4.style.get_data_str",
    return_value="""
    {
	    "identifier": "normal",
        "title": "Données Brutes",
        "abstract": "Données brutes sans changement de palette",
        "keywords": ["Défaut"],
        "legend": {
            "format": "image/png",
            "url": "http://serveur.fr/image.png",
            "height": 100,
            "width": 100,
            "min_scale_denominator": 0,
            "max_scale_denominator": 30
        }
    }""",
)
def test_ok_identity(mocked_get_data_str, mocked_exists):

    try:
        style = Style("normal")
        mocked_get_data_str.assert_called_once_with("file:///path/to/normal")

        assert style.is_identity
        assert style.bands is None
        assert style.format is None
        assert style.input_nodata is None

    except Exception as exc:
        assert False, f"Style read raises an exception: {exc}"


@mock.patch.dict(os.environ, {"ROK4_STYLES_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch(
    "rok4.style.exists",
    return_value=True,
)
@mock.patch(
    "rok4.style.get_data_str",
    return_value="""
    {
	    "identifier": "normal",
        "title": "Données Brutes",
        "abstract": "Données brutes sans changement de palette",
        "keywords": ["Défaut"],
        "legend": {
            "format": "image/png",
            "url": "http://serveur.fr/image.png",
            "height": 100,
            "width": 100,
            "min_scale_denominator": 0,
            "max_scale_denominator": 30
        },
        "palette": {
            "no_alpha": false,
            "rgb_continuous": true,
            "alpha_continuous": false,
            "colours": [
                { "value": 0, "red": 10, "green": 20, "blue": 30, "alpha": 40 },
                { "value": 100, "red": 50, "green": 40, "blue": 10, "alpha": 100 }
            ]
        }
    }""",
)
def test_ok_palette_convert_rgba_continuous(mocked_get_data_str, mocked_exists):

    try:
        style = Style("normal")
        mocked_get_data_str.assert_called_once_with("file:///path/to/normal")

        assert style.palette.convert(-10) == (10, 20, 30, 40)
        assert style.palette.convert(150) == (50, 40, 10, 100)
        assert style.palette.convert(20) == (18, 24, 26, 40)

    except Exception as exc:
        assert False, f"Style read raises an exception: {exc}"


@mock.patch.dict(os.environ, {"ROK4_STYLES_DIRECTORY": "file:///path/to"}, clear=True)
@mock.patch(
    "rok4.style.exists",
    return_value=True,
)
@mock.patch(
    "rok4.style.get_data_str",
    return_value="""
    {
	    "identifier": "normal",
        "title": "Données Brutes",
        "abstract": "Données brutes sans changement de palette",
        "keywords": ["Défaut"],
        "legend": {
            "format": "image/png",
            "url": "http://serveur.fr/image.png",
            "height": 100,
            "width": 100,
            "min_scale_denominator": 0,
            "max_scale_denominator": 30
        },
        "palette": {
            "no_alpha": true,
            "rgb_continuous": false,
            "alpha_continuous": false,
            "colours": [
                { "value": 0, "red": 10, "green": 20, "blue": 30, "alpha": 40 },
                { "value": 100, "red": 50, "green": 40, "blue": 10, "alpha": 100 }
            ]
        }
    }""",
)
def test_ok_palette_convert_rgb_no_alpha(mocked_get_data_str, mocked_exists):

    try:
        style = Style("normal")
        mocked_get_data_str.assert_called_once_with("file:///path/to/normal")

        assert style.palette.convert(-10) == (10, 20, 30)
        assert style.palette.convert(150) == (50, 40, 10)
        assert style.palette.convert(20) == (10, 20, 30)

    except Exception as exc:
        assert False, f"Style read raises an exception: {exc}"
