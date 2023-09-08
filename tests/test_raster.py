"""Describes unit tests for the rok4.raster module.

There is one test class for each tested functionnality.
See internal docstrings for more information.
Each variable prefixed by "m_" is a mock, or part of it.
"""

import copy
import json
import math
import random
from unittest import TestCase, mock
from unittest.mock import MagicMock, call, mock_open

import pytest

from rok4.enums import ColorFormat
from rok4.raster import Raster, RasterSet

# rok4.raster.Raster class tests


class TestRasterInit(TestCase):
    """rok4.raster.Raster default constructor."""

    def test_default(self):
        """Default property values."""
        raster = Raster()

        assert raster.bands is None
        assert (
            isinstance(raster.bbox, tuple)
            and len(raster.bbox) == 4
            and all(coordinate is None for coordinate in raster.bbox)
        )
        assert (
            isinstance(raster.dimensions, tuple)
            and len(raster.dimensions) == 2
            and all(dimension is None for dimension in raster.dimensions)
        )
        assert raster.format is None
        assert raster.mask is None
        assert raster.path is None


class TestRasterFromFile(TestCase):
    """rok4.raster.Raster.from_file(path) class constructor."""

    def setUp(self):
        self.source_image_path = "file:///home/user/image.tif"
        self.source_mask_path = "file:///home/user/image.msk"
        self.osgeo_image_path = "file:///home/user/image.tif"
        self.osgeo_mask_path = "file:///home/user/image.msk"
        self.bbox = (-5.4, 41.3, 9.8, 51.3)
        self.image_size = (1920, 1080)
        return super().setUp()

    def test_empty(self):
        """Constructor called without the expected path argument."""
        with pytest.raises(TypeError):
            Raster.from_file()

    @mock.patch("rok4.raster.exists", return_value=False)
    def test_image_not_found(self, m_exists):
        """Constructor called on a path matching no file or object."""
        with pytest.raises(Exception):
            Raster.from_file(self.source_image_path)
        m_exists.assert_called_once_with(self.source_image_path)

    @mock.patch("rok4.raster.get_osgeo_path")
    @mock.patch("rok4.raster.compute_format", return_value=ColorFormat.UINT8)
    @mock.patch("rok4.raster.gdal.Open")
    @mock.patch("rok4.raster.compute_bbox")
    @mock.patch("rok4.raster.exists", side_effect=[True, False])
    def test_image(self, m_exists, m_compute_bbox, m_gdal_open, m_compute_format, m_get_osgeo_path):
        """Constructor called nominally on an image without mask."""
        m_compute_bbox.return_value = self.bbox
        m_dataset_properties = {
            "RasterCount": 3,
            "RasterXSize": self.image_size[0],
            "RasterYSize": self.image_size[1],
        }
        m_gdal_open.return_value = type("", (object,), m_dataset_properties)
        m_get_osgeo_path.return_value = self.osgeo_image_path

        raster = Raster.from_file(self.source_image_path)

        m_exists.assert_has_calls([call(self.source_image_path), call(self.source_mask_path)])
        m_get_osgeo_path.assert_called_once_with(self.source_image_path)
        m_gdal_open.assert_called_once_with(self.osgeo_image_path)
        assert raster.path == self.source_image_path
        assert raster.mask is None
        m_compute_bbox.assert_called_once()
        assert (
            isinstance(raster.bbox, tuple)
            and len(raster.bbox) == 4
            and math.isclose(raster.bbox[0], self.bbox[0], rel_tol=1e-5)
            and math.isclose(raster.bbox[1], self.bbox[1], rel_tol=1e-5)
            and math.isclose(raster.bbox[2], self.bbox[2], rel_tol=1e-5)
            and math.isclose(raster.bbox[3], self.bbox[3], rel_tol=1e-5)
        )
        assert raster.bands == 3
        m_compute_format.assert_called_once()
        assert raster.format == ColorFormat.UINT8
        assert raster.dimensions == self.image_size

    @mock.patch("rok4.raster.get_osgeo_path")
    @mock.patch("rok4.raster.compute_format", return_value=ColorFormat.UINT8)
    @mock.patch("rok4.raster.gdal.IdentifyDriver")
    @mock.patch("rok4.raster.gdal.Open")
    @mock.patch("rok4.raster.compute_bbox")
    @mock.patch("rok4.raster.exists", side_effect=[True, True])
    def test_image_and_mask(
        self,
        m_exists,
        m_compute_bbox,
        m_gdal_open,
        m_identifydriver,
        m_compute_format,
        m_get_osgeo_path,
    ):
        """Constructor called nominally on an image with mask."""
        m_compute_bbox.return_value = self.bbox
        m_dataset_properties = {
            "RasterCount": 3,
            "RasterXSize": self.image_size[0],
            "RasterYSize": self.image_size[1],
        }
        m_gdal_open.return_value = type("", (object,), m_dataset_properties)
        m_get_osgeo_path.side_effect = [self.osgeo_image_path, self.osgeo_mask_path]
        m_identifydriver.return_value = type("", (object,), {"ShortName": "GTiff"})

        raster = Raster.from_file(self.source_image_path)

        m_exists.assert_has_calls([call(self.source_image_path), call(self.source_mask_path)])
        m_get_osgeo_path.assert_has_calls(
            [call(self.source_image_path), call(self.source_mask_path)]
        )
        m_identifydriver.assert_called_once_with(self.osgeo_mask_path)
        m_gdal_open.assert_called_once_with(self.osgeo_image_path)
        assert raster.path == self.source_image_path
        assert raster.mask == self.source_mask_path
        m_compute_bbox.assert_called_once()
        assert (
            isinstance(raster.bbox, tuple)
            and len(raster.bbox) == 4
            and math.isclose(raster.bbox[0], self.bbox[0], rel_tol=1e-5)
            and math.isclose(raster.bbox[1], self.bbox[1], rel_tol=1e-5)
            and math.isclose(raster.bbox[2], self.bbox[2], rel_tol=1e-5)
            and math.isclose(raster.bbox[3], self.bbox[3], rel_tol=1e-5)
        )
        assert raster.bands == 3
        m_compute_format.assert_called_once()
        assert raster.format == ColorFormat.UINT8
        assert raster.dimensions == self.image_size

    @mock.patch("rok4.raster.get_osgeo_path")
    @mock.patch("rok4.raster.gdal.Open", side_effect=RuntimeError)
    @mock.patch("rok4.raster.exists", side_effect=[True, False])
    def test_unsupported_image_format(self, m_exists, m_gdal_open, m_get_osgeo_path):
        """Test case : Constructor called on an unsupported image file or object."""
        m_get_osgeo_path.return_value = self.osgeo_image_path

        with pytest.raises(RuntimeError):
            Raster.from_file(self.source_image_path)

        m_exists.assert_called_once_with(self.source_image_path)
        m_get_osgeo_path.assert_called_once_with(self.source_image_path)
        m_gdal_open.assert_called_once_with(self.osgeo_image_path)

    @mock.patch("rok4.raster.get_osgeo_path")
    @mock.patch("rok4.raster.gdal.IdentifyDriver")
    @mock.patch("rok4.raster.gdal.Open", side_effect=None)
    @mock.patch("rok4.raster.exists", side_effect=[True, True])
    def test_unsupported_mask_format(
        self, m_exists, m_gdal_open, m_identifydriver, m_get_osgeo_path
    ):
        """Test case : Constructor called on an unsupported mask file or object."""
        m_get_osgeo_path.side_effect = [self.osgeo_image_path, self.osgeo_mask_path]
        m_identifydriver.return_value = type("", (object,), {"ShortName": "JPG"})

        with pytest.raises(Exception):
            Raster.from_file(self.source_image_path)

        m_exists.assert_has_calls([call(self.source_image_path), call(self.source_mask_path)])
        m_get_osgeo_path.assert_has_calls(
            [call(self.source_image_path), call(self.source_mask_path)]
        )
        m_identifydriver.assert_called_once_with(self.osgeo_mask_path)
        m_gdal_open.assert_called_once_with(self.osgeo_image_path)


class TestRasterFromParameters(TestCase):
    """rok4.raster.Raster.from_parameters(**kwargs) class constructor."""

    def test_image(self):
        """Parameters describing an image without mask"""
        parameters = {
            "bands": 4,
            "bbox": (-5.4, 41.3, 9.8, 51.3),
            "dimensions": (1920, 1080),
            "format": ColorFormat.UINT8,
            "path": "file:///path/to/image.tif",
        }

        raster = Raster.from_parameters(**parameters)

        assert raster.path == parameters["path"]
        assert (
            isinstance(raster.bbox, tuple)
            and len(raster.bbox) == 4
            and math.isclose(raster.bbox[0], parameters["bbox"][0], rel_tol=1e-5)
            and math.isclose(raster.bbox[1], parameters["bbox"][1], rel_tol=1e-5)
            and math.isclose(raster.bbox[2], parameters["bbox"][2], rel_tol=1e-5)
            and math.isclose(raster.bbox[3], parameters["bbox"][3], rel_tol=1e-5)
        )
        assert raster.bands == parameters["bands"]
        assert raster.format == parameters["format"]
        assert raster.dimensions == parameters["dimensions"]
        assert raster.mask is None

    def test_image_and_mask(self):
        """Parameters describing an image with mask"""
        parameters = {
            "bands": 4,
            "bbox": (-5.4, 41.3, 9.8, 51.3),
            "dimensions": (1920, 1080),
            "format": ColorFormat.UINT8,
            "mask": "file:///path/to/image.msk",
            "path": "file:///path/to/image.tif",
        }

        raster = Raster.from_parameters(**parameters)

        assert raster.path == parameters["path"]
        assert (
            isinstance(raster.bbox, tuple)
            and len(raster.bbox) == 4
            and math.isclose(raster.bbox[0], parameters["bbox"][0], rel_tol=1e-5)
            and math.isclose(raster.bbox[1], parameters["bbox"][1], rel_tol=1e-5)
            and math.isclose(raster.bbox[2], parameters["bbox"][2], rel_tol=1e-5)
            and math.isclose(raster.bbox[3], parameters["bbox"][3], rel_tol=1e-5)
        )
        assert raster.bands == parameters["bands"]
        assert raster.format == parameters["format"]
        assert raster.dimensions == parameters["dimensions"]
        assert raster.mask == parameters["mask"]


# rok4.raster.RasterSet class tests


class TestRasterSetInit(TestCase):
    """rok4.raster.RasterSet default constructor."""

    def test_default(self):
        """Default property values."""
        rasterset = RasterSet()

        assert (
            isinstance(rasterset.bbox, tuple)
            and len(rasterset.bbox) == 4
            and all(coordinate is None for coordinate in rasterset.bbox)
        )
        assert isinstance(rasterset.colors, list) and not rasterset.colors
        assert isinstance(rasterset.raster_list, list) and not rasterset.raster_list
        assert rasterset.srs is None


class TestRasterSetFromList(TestCase):
    """rok4.raster.RasterSet.from_list(path, srs) class constructor."""

    @mock.patch("rok4.raster.get_osgeo_path")
    @mock.patch("rok4.raster.Raster.from_file")
    def test_ok_at_least_3_files(self, m_from_file, m_get_osgeo_path):
        """List of 3 or more valid image files"""
        file_number = random.randint(3, 100)
        file_list = []
        for n in range(0, file_number, 1):
            file_list.append(f"s3://test_bucket/image_{n+1}.tif")
        file_list_string = "\n".join(file_list)
        m_open = mock_open(read_data=file_list_string)
        list_path = "s3://test_bucket/raster_set.list"
        list_local_path = "/tmp/raster_set.list"
        m_get_osgeo_path.return_value = list_local_path
        raster_list = []
        colors = []
        serial_in = {"raster_list": [], "colors": []}
        for n in range(0, file_number, 1):
            raster = MagicMock(Raster)
            raster.path = file_list[n]
            raster.bbox = (
                -0.75 + math.floor(n / 3),
                -1.33 + n - 3 * math.floor(n / 3),
                0.25 + math.floor(n / 3),
                -0.33 + n - 3 * math.floor(n / 3),
            )
            raster.format = random.choice([ColorFormat.BIT, ColorFormat.UINT8, ColorFormat.FLOAT32])
            if raster.format == ColorFormat.BIT:
                raster.bands = 1
            else:
                raster.bands = random.randint(1, 4)
            if random.randint(0, 1) == 1:
                raster.mask = raster.path.replace(".tif", ".msk")
            else:
                raster.mask = None
            color_dict = {"bands": raster.bands, "format": raster.format}
            if color_dict not in colors:
                colors.append(color_dict)
                serial_in["colors"].append({"bands": raster.bands, "format": raster.format.name})
            raster.dimensions = (5000, 5000)
            raster_list.append(raster)
            raster_serial = {
                "path": raster.path,
                "bands": raster.bands,
                "format": raster.format.name,
                "bbox": list(raster.bbox),
                "dimensions": list(raster.dimensions),
            }
            if raster.mask:
                raster_serial["mask"] = raster.mask
            serial_in["raster_list"].append(raster_serial)
        m_from_file.side_effect = raster_list
        srs = "EPSG:4326"
        serial_in["srs"] = srs
        bbox = (-0.75, -1.33, 0.25 + math.floor((file_number - 1) / 3), 1.67)
        serial_in["bbox"] = list(bbox)

        with mock.patch("rok4.raster.open", m_open):
            rasterset = RasterSet.from_list(list_path, srs)

        serial_out = rasterset.serializable
        assert rasterset.srs == srs
        m_get_osgeo_path.assert_called_once_with(list_path)
        m_open.assert_called_once_with(file=list_local_path)
        assert rasterset.raster_list == raster_list
        assert isinstance(serial_out["bbox"], list)
        for i in range(0, 4, 1):
            assert math.isclose(rasterset.bbox[i], bbox[i], rel_tol=1e-5)
            assert math.isclose(serial_out["bbox"][i], serial_in["bbox"][i], rel_tol=1e-5)
        assert len(rasterset.colors) > 0
        assert rasterset.colors == colors
        for key in serial_in.keys():
            if key != "bbox":
                assert serial_out[key] == serial_in[key]
        assert isinstance(serial_out["bbox"], list)


class TestRasterSetFromDescriptor(TestCase):
    """rok4.raster.RasterSet.from_descriptor(path) class constructor."""

    @mock.patch("rok4.raster.get_osgeo_path")
    @mock.patch("rok4.raster.Raster.from_parameters")
    def test_simple_ok(self, m_from_parameters, m_get_osgeo_path):
        serial_in = {
            "bbox": [550000.000, 6210000.000, 570000.000, 6230000.000],
            "colors": [{"bands": 3, "format": "UINT8"}],
            "raster_list": [
                {
                    "bands": 3,
                    "bbox": [550000.000, 6210000.000, 560000.000, 6220000.000],
                    "dimensions": [5000, 5000],
                    "format": "UINT8",
                    "mask": "file:///path/to/images/550000_6220000.msk",
                    "path": "file:///path/to/images/550000_6220000.tif",
                },
                {
                    "bands": 3,
                    "bbox": [560000.000, 6210000.000, 570000.000, 6220000.000],
                    "dimensions": [5000, 5000],
                    "format": "UINT8",
                    "mask": "file:///path/to/images/560000_6220000.msk",
                    "path": "file:///path/to/images/560000_6220000.tif",
                },
                {
                    "bands": 3,
                    "bbox": [550000.000, 6220000.000, 560000.000, 6230000.000],
                    "dimensions": [5000, 5000],
                    "format": "UINT8",
                    "mask": "file:///path/to/images/550000_6230000.msk",
                    "path": "file:///path/to/images/550000_6230000.tif",
                },
            ],
            "srs": "IGNF:LAMB93",
        }
        desc_path = "file:///path/to/descriptor.json"
        local_path = "/path/to/descriptor.json"
        desc_content = json.dumps(serial_in)
        raster_list = []
        raster_args_list = []
        for raster_dict in serial_in["raster_list"]:
            raster_properties = copy.deepcopy(raster_dict)
            raster_properties["format"] = ColorFormat[raster_dict["format"]]
            raster_properties["bbox"] = tuple(raster_dict["bbox"])
            raster_properties["dimensions"] = tuple(raster_dict["dimensions"])

            raster = MagicMock(Raster, **raster_properties)
            raster_list.append(raster)
            raster_args_list.append(raster_properties)
        m_from_parameters.side_effect = raster_list
        m_get_osgeo_path.return_value = local_path
        m_open = mock_open(read_data=desc_content)

        with mock.patch("rok4.raster.open", m_open):
            rasterset = RasterSet.from_descriptor(desc_path)

        m_get_osgeo_path.assert_called_once_with(desc_path)
        m_open.assert_called_once_with(file=local_path)
        assert rasterset.srs == serial_in["srs"]
        m_from_parameters.assert_called()
        assert m_from_parameters.call_count == 3
        for i in range(0, len(raster_args_list), 1):
            assert m_from_parameters.call_args_list[i] == call(**raster_args_list[i])
        assert rasterset.raster_list == raster_list
        assert isinstance(rasterset.bbox, tuple) and len(rasterset.bbox) == 4
        assert isinstance(rasterset.colors, list) and rasterset.colors
        for i in range(0, len(serial_in["colors"]), 1):
            expected_color = copy.deepcopy(serial_in["colors"][i])
            expected_color["format"] = ColorFormat[serial_in["colors"][i]["format"]]
            assert rasterset.colors[i] == expected_color
        serial_out = rasterset.serializable
        assert isinstance(serial_out["bbox"], list) and len(serial_out["bbox"]) == 4
        for i in range(0, 4, 1):
            assert math.isclose(rasterset.bbox[i], serial_in["bbox"][i], rel_tol=1e-5)
            assert math.isclose(serial_out["bbox"][i], serial_in["bbox"][i], rel_tol=1e-5)
        for key in serial_in.keys():
            if key != "bbox":
                assert serial_out[key] == serial_in[key]


class TestRasterSetWriteDescriptor(TestCase):
    """rok4.raster.RasterSet.write_descriptor(path) class method."""

    @mock.patch("rok4.raster.put_data_str")
    def test_ok_with_output_path(self, m_put_data_str):
        serial_in = {
            "bbox": [550000.000, 6210000.000, 570000.000, 6230000.000],
            "colors": [{"bands": 3, "format": "UINT8"}],
            "raster_list": [
                {
                    "bands": 3,
                    "bbox": [550000.000, 6210000.000, 560000.000, 6220000.000],
                    "dimensions": [5000, 5000],
                    "format": "UINT8",
                    "mask": "s3://rok4bucket/images/550000_6220000.msk",
                    "path": "s3://rok4bucket/images/550000_6220000.tif",
                },
                {
                    "bands": 3,
                    "bbox": [560000.000, 6210000.000, 570000.000, 6220000.000],
                    "dimensions": [5000, 5000],
                    "format": "UINT8",
                    "mask": "s3://rok4bucket/images/560000_6220000.msk",
                    "path": "s3://rok4bucket/images/560000_6220000.tif",
                },
                {
                    "bands": 3,
                    "bbox": [550000.000, 6220000.000, 560000.000, 6230000.000],
                    "dimensions": [5000, 5000],
                    "format": "UINT8",
                    "mask": "s3://rok4bucket/images/550000_6230000.msk",
                    "path": "s3://rok4bucket/images/550000_6230000.tif",
                },
            ],
            "srs": "IGNF:LAMB93",
        }
        content = json.dumps(serial_in, sort_keys=True)
        path = "s3://rok4bucket/dst_descriptor.json"
        rasterset = RasterSet()
        rasterset.bbox = tuple(serial_in["bbox"])
        rasterset.srs = serial_in["srs"]
        rasterset.colors = []
        for color_dict in serial_in["colors"]:
            rasterset.colors.append(
                {"bands": color_dict["bands"], "format": ColorFormat[color_dict["format"]]}
            )
        rasterset.raster_list = []
        for raster_dict in serial_in["raster_list"]:
            raster_args = copy.deepcopy(raster_dict)
            raster_args["format"] = ColorFormat[raster_dict["format"]]
            raster_args["bbox"] = tuple(raster_dict["bbox"])
            raster_args["dimensions"] = tuple(raster_dict["dimensions"])
            rasterset.raster_list.append(MagicMock(Raster, **raster_args))

        try:
            rasterset.write_descriptor(path)
        except Exception as exc:
            assert False, f"Writing RasterSet's descriptor raises an exception: {exc}"

        m_put_data_str.assert_called_once_with(content, path)

    @mock.patch("rok4.raster.print")
    def test_ok_no_output_path(self, m_print):
        serial_in = {
            "bbox": [550000.000, 6210000.000, 570000.000, 6230000.000],
            "colors": [{"bands": 3, "format": "UINT8"}],
            "raster_list": [
                {
                    "bands": 3,
                    "bbox": [550000.000, 6210000.000, 560000.000, 6220000.000],
                    "dimensions": [5000, 5000],
                    "format": "UINT8",
                    "mask": "s3://rok4bucket/images/550000_6220000.msk",
                    "path": "s3://rok4bucket/images/550000_6220000.tif",
                },
                {
                    "bands": 3,
                    "bbox": [560000.000, 6210000.000, 570000.000, 6220000.000],
                    "dimensions": [5000, 5000],
                    "format": "UINT8",
                    "mask": "s3://rok4bucket/images/560000_6220000.msk",
                    "path": "s3://rok4bucket/images/560000_6220000.tif",
                },
                {
                    "bands": 3,
                    "bbox": [550000.000, 6220000.000, 560000.000, 6230000.000],
                    "dimensions": [5000, 5000],
                    "format": "UINT8",
                    "mask": "s3://rok4bucket/images/550000_6230000.msk",
                    "path": "s3://rok4bucket/images/550000_6230000.tif",
                },
            ],
            "srs": "IGNF:LAMB93",
        }
        content = json.dumps(serial_in, sort_keys=True)
        rasterset = RasterSet()
        rasterset.bbox = tuple(serial_in["bbox"])
        rasterset.srs = serial_in["srs"]
        rasterset.colors = []
        for color_dict in serial_in["colors"]:
            rasterset.colors.append(
                {"bands": color_dict["bands"], "format": ColorFormat[color_dict["format"]]}
            )
        rasterset.raster_list = []
        for raster_dict in serial_in["raster_list"]:
            raster_args = copy.deepcopy(raster_dict)
            raster_args["format"] = ColorFormat[raster_dict["format"]]
            raster_args["bbox"] = tuple(raster_dict["bbox"])
            raster_args["dimensions"] = tuple(raster_dict["dimensions"])
            rasterset.raster_list.append(MagicMock(Raster, **raster_args))

        try:
            rasterset.write_descriptor()
        except Exception as exc:
            assert False, f"Writing RasterSet's descriptor raises an exception: {exc}"

        m_print.assert_called_once_with(content)
