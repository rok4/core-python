"""Describes unit tests for the rok4.Raster module."""

from rok4.Raster import Raster, RasterSet
from rok4.Utils import ColorFormat

import copy
import math
import json
import random

import pytest
from unittest import mock, TestCase
from unittest.mock import *


# rok4.Raster.Raster class tests

class TestRasterFromFile(TestCase):
    """rok4.Raster.Raster.from_file(path) class constructor."""

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

    @mock.patch("rok4.Raster.exists", return_value=False)
    def test_image_not_found(self, mocked_exists):
        """Constructor called on a path matching no file or object."""

        with pytest.raises(Exception):
            Raster.from_file(self.source_image_path)

        mocked_exists.assert_called_once_with(self.source_image_path)

    @mock.patch("rok4.Raster.get_osgeo_path")
    @mock.patch("rok4.Raster.compute_format", return_value=ColorFormat.UINT8)
    @mock.patch("rok4.Raster.gdal.Open")
    @mock.patch("rok4.Raster.compute_bbox")
    @mock.patch("rok4.Raster.exists", side_effect=[True, False])
    def test_image(self, mocked_exists, mocked_compute_bbox, mocked_gdal_open,
                   mocked_compute_format, mocked_get_osgeo_path):
        """Constructor called nominally on an image without mask."""

        mocked_compute_bbox.return_value = self.bbox
        mocked_gdal_open.return_value = type(
            "", (object,), 
            {
                "RasterCount": 3,
                "RasterXSize": self.image_size[0],
                "RasterYSize": self.image_size[1]
            }
        )
        mocked_get_osgeo_path.return_value = self.osgeo_image_path

        raster_object = Raster.from_file(self.source_image_path)

        mocked_exists.assert_has_calls([call(self.source_image_path), call(self.source_mask_path)])
        mocked_get_osgeo_path.assert_called_once_with(self.source_image_path)
        mocked_gdal_open.assert_called_once_with( self.osgeo_image_path )
        assert raster_object.path == self.source_image_path
        assert raster_object.mask is None

        mocked_compute_bbox.assert_called_once()
        assert math.isclose(raster_object.bbox[0], self.bbox[0], rel_tol=1e-5)
        assert math.isclose(raster_object.bbox[1], self.bbox[1], rel_tol=1e-5)
        assert math.isclose(raster_object.bbox[2], self.bbox[2], rel_tol=1e-5)
        assert math.isclose(raster_object.bbox[3], self.bbox[3], rel_tol=1e-5)
        assert raster_object.bands == 3
        mocked_compute_format.assert_called_once()
        assert raster_object.format == ColorFormat.UINT8
        assert raster_object.dimensions == self.image_size

    @mock.patch("rok4.Raster.get_osgeo_path")
    @mock.patch("rok4.Raster.compute_format", return_value=ColorFormat.UINT8)
    @mock.patch("rok4.Raster.gdal.IdentifyDriver")
    @mock.patch("rok4.Raster.gdal.Open")
    @mock.patch("rok4.Raster.compute_bbox")
    @mock.patch("rok4.Raster.exists", side_effect=[True, True])
    def test_image_and_mask(self, mocked_exists, mocked_compute_bbox, mocked_gdal_open,
                            mocked_identifydriver, mocked_compute_format, mocked_get_osgeo_path):
        """Constructor called nominally on an image with mask."""

        mocked_compute_bbox.return_value = self.bbox
        mocked_gdal_open.return_value = type(
            "",
            (object,),
            {
                "RasterCount": 3,
                "RasterXSize": self.image_size[0],
                "RasterYSize": self.image_size[1]
            }
        )
        mocked_get_osgeo_path.side_effect=[self.osgeo_image_path, self.osgeo_mask_path]
        # This next line emulates the return of gdal.IdentifyDriver()
        mocked_identifydriver.return_value = type("", (object,), {"ShortName": "GTiff"})

        raster_object = Raster.from_file(self.source_image_path)

        mocked_exists.assert_has_calls([call(self.source_image_path), call(self.source_mask_path)])
        mocked_get_osgeo_path.assert_has_calls([call(self.source_image_path),
                                                call(self.source_mask_path)])
        mocked_identifydriver.assert_called_once_with(self.osgeo_mask_path)
        mocked_gdal_open.assert_called_once_with(self.osgeo_image_path)
        assert raster_object.path == self.source_image_path
        assert raster_object.mask == self.source_mask_path

        mocked_compute_bbox.assert_called_once()
        assert math.isclose(raster_object.bbox[0], self.bbox[0], rel_tol=1e-5)
        assert math.isclose(raster_object.bbox[1], self.bbox[1], rel_tol=1e-5)
        assert math.isclose(raster_object.bbox[2], self.bbox[2], rel_tol=1e-5)
        assert math.isclose(raster_object.bbox[3], self.bbox[3], rel_tol=1e-5)
        assert raster_object.bands == 3
        mocked_compute_format.assert_called_once()
        assert raster_object.format == ColorFormat.UINT8
        assert raster_object.dimensions == self.image_size

    @mock.patch("rok4.Raster.get_osgeo_path")
    @mock.patch("rok4.Raster.gdal.Open", side_effect=RuntimeError)
    @mock.patch("rok4.Raster.exists", side_effect=[True, False])
    def test_unsupported_image_format(self, mocked_exists, mocked_gdal_open, 
                                      mocked_get_osgeo_path):
        """Test case : Constructor called on an unsupported image file or object."""

        mocked_get_osgeo_path.return_value = self.osgeo_image_path

        with pytest.raises(RuntimeError):
            Raster.from_file(self.source_image_path)

        mocked_exists.assert_called_once_with(self.source_image_path)
        mocked_get_osgeo_path.assert_called_once_with(self.source_image_path)
        mocked_gdal_open.assert_called_once_with(self.osgeo_image_path)

    @mock.patch("rok4.Raster.get_osgeo_path")
    @mock.patch("rok4.Raster.gdal.IdentifyDriver")
    @mock.patch("rok4.Raster.gdal.Open", side_effect=None)
    @mock.patch("rok4.Raster.exists", side_effect=[True, True])
    def test_unsupported_mask_format(self, mocked_exists, mocked_gdal_open, mocked_identifydriver,
                                     mocked_get_osgeo_path):
        """Test case : Constructor called on an unsupported mask file or object."""

        mocked_get_osgeo_path.side_effect=[self.osgeo_image_path, self.osgeo_mask_path]
        # This next line emulates the return of gdal.IdentifyDriver()
        mocked_identifydriver.return_value = type("", (object,), {"ShortName": "JPG"})

        with pytest.raises(Exception):
            Raster.from_file(self.source_image_path)      

        mocked_exists.assert_has_calls([call(self.source_image_path), call(self.source_mask_path)])
        mocked_get_osgeo_path.assert_has_calls([call(self.source_image_path),
                                                call(self.source_mask_path)])
        mocked_identifydriver.assert_called_once_with(self.osgeo_mask_path)
        mocked_gdal_open.assert_called_once_with(self.osgeo_image_path)


class TestRasterFromParameters(TestCase):
    """rok4.Raster.Raster.from_parameters(**kwargs) class constructor."""

    def test_image(self):
        """Parameters describing an image without mask"""

        i_path = "file:///path/to/image.tif"
        i_bbox = (-5.4, 41.3, 9.8, 51.3)
        i_bands = 4
        i_format = ColorFormat.UINT8
        i_dimensions = (1920, 1080)

        result = Raster.from_parameters(path=i_path, bbox=i_bbox, bands=i_bands, format=i_format,
                                        dimensions=i_dimensions)

        assert result.path == i_path
        assert math.isclose(result.bbox[0], i_bbox[0], rel_tol=1e-5)
        assert math.isclose(result.bbox[1], i_bbox[1], rel_tol=1e-5)
        assert math.isclose(result.bbox[2], i_bbox[2], rel_tol=1e-5)
        assert math.isclose(result.bbox[3], i_bbox[3], rel_tol=1e-5)
        assert result.bands == i_bands
        assert result.format == i_format
        assert result.dimensions == i_dimensions
        assert result.mask is None

    def test_image_and_mask(self):
        """Parameters describing an image with mask"""

        i_path = "file:///path/to/image.tif"
        i_mask = "file:///path/to/image.msk"
        i_bbox = (-5.4, 41.3, 9.8, 51.3)
        i_bands = 4
        i_format = ColorFormat.UINT8
        i_dimensions = (1920, 1080)

        result = Raster.from_parameters(path=i_path, bbox=i_bbox, bands=i_bands, format=i_format,
                                        dimensions=i_dimensions, mask=i_mask)

        assert result.path == i_path
        assert math.isclose(result.bbox[0], i_bbox[0], rel_tol=1e-5)
        assert math.isclose(result.bbox[1], i_bbox[1], rel_tol=1e-5)
        assert math.isclose(result.bbox[2], i_bbox[2], rel_tol=1e-5)
        assert math.isclose(result.bbox[3], i_bbox[3], rel_tol=1e-5)
        assert result.bands == i_bands
        assert result.format == i_format
        assert result.dimensions == i_dimensions
        assert result.mask == i_mask
    

# rok4.Raster.RasterSet class tests

class TestRasterSetFromList(TestCase):
    """rok4.Raster.RasterSet.from_list(path, srs) class constructor."""

    @mock.patch("rok4.Raster.get_osgeo_path")
    @mock.patch("rok4.Raster.Raster.from_file")
    def test_ok_at_least_3_files(self, mocked_from_file, mocked_get_osgeo_path):
        """List of 3 or more valid image files"""

        file_number = random.randint(3, 100)
        file_list = []
        for n in range(0, file_number, 1):
            file_list.append(f"s3://test_bucket/image_{n+1}.tif")
        file_list_string = "\n".join(file_list)
        mocked_open = mock_open(read_data = file_list_string)

        list_path = "s3://test_bucket/raster_set.list"
        list_local_path = "/tmp/raster_set.list"
        
        mocked_get_osgeo_path.return_value = list_local_path

        raster_list = []
        colors = []
        serializable = {
            "raster_list": [],
            "colors": []
        }
        for n in range(0, file_number, 1):
            raster = MagicMock(Raster)
            raster.path = file_list[n]
            raster.bbox = (
                -0.75 + math.floor(n/3),
                -1.33 + n - 3 * math.floor(n/3),
                0.25 + math.floor(n/3),
                -0.33 +  n - 3 * math.floor(n/3)
            )
            raster.format = random.choice([ColorFormat.BIT, ColorFormat.UINT8,
                                          ColorFormat.FLOAT32])

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
                serializable["colors"].append({"bands": raster.bands, 
                                               "format": raster.format.name})
            raster.dimensions = (5000, 5000)

            raster_list.append(raster)
            raster_serializable = {"path": raster.path, "bands": raster.bands,
                                   "format": raster.format.name, "bbox": list(raster.bbox),
                                   "dimensions": list(raster.dimensions)}
            if raster.mask: 
                raster_serializable["mask"] = raster.mask
            serializable["raster_list"].append(raster_serializable)

        mocked_from_file.side_effect = raster_list

        srs = "EPSG:4326"
        serializable["srs"] = srs
        bbox = (
            -0.75,
            -1.33,
            0.25 + math.floor((file_number-1)/3),
            1.67
        )
        serializable["bbox"] = list(bbox)

        with mock.patch("rok4.Raster.open", mocked_open):
            result = RasterSet.from_list(list_path, srs)

        result_serializable = result.serializable

        assert result.srs == srs
        mocked_get_osgeo_path.assert_called_once_with(list_path)
        mocked_open.assert_called_once_with(file=list_local_path, mode="r")
        assert result.raster_list == raster_list
        assert isinstance(result_serializable["bbox"], list)
        for i in range(0, 4, 1):
            assert math.isclose(result.bbox[i], bbox[i], rel_tol=1e-5)
            assert math.isclose(result_serializable["bbox"][i], serializable["bbox"][i],
                                rel_tol=1e-5)
        assert len(result.colors) > 0
        assert result.colors == colors
        for key in serializable.keys():
            if key != "bbox":
                assert result_serializable[key] == serializable[key]
        assert isinstance(result_serializable["bbox"], list)


class TestRasterSetFromDescriptor(TestCase):
    """rok4.Raster.RasterSet.from_descriptor(path) class constructor."""

    @mock.patch("rok4.Raster.get_osgeo_path")
    @mock.patch("rok4.Raster.Raster.from_parameters")
    def test_simple_ok(self, mocked_from_parameters, mocked_get_osgeo_path):
        serialization = {
            "bbox": [550000.000, 6210000.000, 570000.000, 6230000.000],
            "colors": [{"bands": 3, "format": "UINT8"}],
            "raster_list": [
                {
                    "bands": 3,
                    "bbox": [550000.000, 6210000.000, 560000.000, 6220000.000],
                    "dimensions": [5000,5000],
                    "format": "UINT8",
                    "mask": "file:///path/to/images/550000_6220000.msk",
                    "path": "file:///path/to/images/550000_6220000.tif"
                },
                {
                    "bands": 3,
                    "bbox": [560000.000, 6210000.000, 570000.000, 6220000.000],
                    "dimensions": [5000,5000],
                    "format": "UINT8",
                    "mask": "file:///path/to/images/560000_6220000.msk",
                    "path": "file:///path/to/images/560000_6220000.tif"
                },
                {
                    "bands": 3,
                    "bbox": [550000.000, 6220000.000, 560000.000, 6230000.000],
                    "dimensions": [5000,5000],
                    "format": "UINT8",
                    "mask": "file:///path/to/images/550000_6230000.msk",
                    "path": "file:///path/to/images/550000_6230000.tif"
                }
            ],
            "srs": "IGNF:LAMB93"
        }
        desc_path = "file:///path/to/descriptor.json"
        local_path = "/path/to/descriptor.json"
        desc_content = json.dumps(serialization)

        raster_list = []
        raster_args_list = []
        for raster_dict in serialization["raster_list"]:
            raster_properties = copy.deepcopy(raster_dict)
            raster_properties["format"] = ColorFormat[raster_dict["format"]]
            raster_properties["bbox"] = tuple(raster_dict["bbox"])
            raster_properties["dimensions"] = tuple(raster_dict["dimensions"])

            raster = MagicMock(Raster, **raster_properties)
            raster_list.append(raster)
            raster_args_list.append(raster_properties)

        mocked_from_parameters.side_effect = raster_list
        mocked_get_osgeo_path.return_value = local_path
        mocked_open = mock_open(read_data = desc_content)
        with mock.patch("rok4.Raster.open", mocked_open):
            result = RasterSet.from_descriptor(desc_path)

        mocked_get_osgeo_path.assert_called_once_with(desc_path)
        mocked_open.assert_called_once_with(file=local_path, mode="r")
        assert result.srs == serialization["srs"]
        mocked_from_parameters.assert_called()
        assert mocked_from_parameters.call_count == 3
        for i in range(0, len(raster_args_list), 1):
            assert mocked_from_parameters.call_args_list[i] == call(**raster_args_list[i])
        assert result.raster_list == raster_list
        assert isinstance(result.bbox, tuple)
        for i in range(0, 4, 1):
            assert math.isclose(result.bbox[i], serialization["bbox"][i], rel_tol=1e-5)
        assert len(result.colors) > 0
        for i in range(0, len(serialization["colors"]), 1):
            expected_color = copy.deepcopy(serialization["colors"][i])
            expected_color["format"] = ColorFormat[serialization["colors"][i]["format"]]
            assert result.colors[i] == expected_color

        result_serializable = result.serializable
        assert isinstance(result_serializable["bbox"], list)
        for i in range(0, 4, 1):
            assert math.isclose(result_serializable["bbox"][i], serialization["bbox"][i],
                                rel_tol=1e-5)
        for key in serialization.keys():
            if key != "bbox":
                assert result_serializable[key] == serialization[key]


class TestRasterSetWriteDescriptor(TestCase):
    """rok4.Raster.RasterSet.write_descriptor(path) class method."""

    @mock.patch("rok4.Raster.put_data_str")
    def test_ok_with_output_path(self, mocked_put_data_str):
        serialization = {
            "bbox": [550000.000, 6210000.000, 570000.000, 6230000.000],
            "colors": [{"bands": 3, "format": "UINT8"}],
            "raster_list": [
                {
                    "bands": 3,
                    "bbox": [550000.000, 6210000.000, 560000.000, 6220000.000],
                    "dimensions": [5000,5000],
                    "format": "UINT8",
                    "mask": "s3://rok4bucket/images/550000_6220000.msk",
                    "path": "s3://rok4bucket/images/550000_6220000.tif"
                },
                {
                    "bands": 3,
                    "bbox": [560000.000, 6210000.000, 570000.000, 6220000.000],
                    "dimensions": [5000,5000],
                    "format": "UINT8",
                    "mask": "s3://rok4bucket/images/560000_6220000.msk",
                    "path": "s3://rok4bucket/images/560000_6220000.tif"
                },
                {
                    "bands": 3,
                    "bbox": [550000.000, 6220000.000, 560000.000, 6230000.000],
                    "dimensions": [5000,5000],
                    "format": "UINT8",
                    "mask": "s3://rok4bucket/images/550000_6230000.msk",
                    "path": "s3://rok4bucket/images/550000_6230000.tif"
                }
            ],
            "srs": "IGNF:LAMB93"
        }
        content = json.dumps(serialization, sort_keys=True)
        path = "s3://rok4bucket/dst_descriptor.json"

        try:
            rasterset = RasterSet()
            rasterset.bbox = tuple(serialization["bbox"])
            rasterset.srs = serialization["srs"]
            rasterset.colors = []
            for color_dict in serialization["colors"]:
                rasterset.colors.append({"bands": color_dict["bands"],
                                         "format": ColorFormat[color_dict["format"]]})
            rasterset.raster_list = []
            for raster_dict in serialization["raster_list"]:
                raster_args = copy.deepcopy(raster_dict)
                raster_args["format"] = ColorFormat[raster_dict["format"]]
                raster_args["bbox"] = tuple(raster_dict["bbox"])
                raster_args["dimensions"] = tuple(raster_dict["dimensions"])
                rasterset.raster_list.append(MagicMock(Raster, **raster_args))

            rasterset.write_descriptor(path)

        except Exception as exc:
            assert False, f"Writing RasterSet's descriptor raises an exception: {exc}"

        mocked_put_data_str.assert_called_once_with(content, path)


    @mock.patch("rok4.Raster.print")
    def test_ok_no_output_path(self, mocked_print):
        serialization = {
            "bbox": [550000.000, 6210000.000, 570000.000, 6230000.000],
            "colors": [{"bands": 3, "format": "UINT8"}],
            "raster_list": [
                {
                    "bands": 3,
                    "bbox": [550000.000, 6210000.000, 560000.000, 6220000.000],
                    "dimensions": [5000,5000],
                    "format": "UINT8",
                    "mask": "s3://rok4bucket/images/550000_6220000.msk",
                    "path": "s3://rok4bucket/images/550000_6220000.tif"
                },
                {
                    "bands": 3,
                    "bbox": [560000.000, 6210000.000, 570000.000, 6220000.000],
                    "dimensions": [5000,5000],
                    "format": "UINT8",
                    "mask": "s3://rok4bucket/images/560000_6220000.msk",
                    "path": "s3://rok4bucket/images/560000_6220000.tif"
                },
                {
                    "bands": 3,
                    "bbox": [550000.000, 6220000.000, 560000.000, 6230000.000],
                    "dimensions": [5000,5000],
                    "format": "UINT8",
                    "mask": "s3://rok4bucket/images/550000_6230000.msk",
                    "path": "s3://rok4bucket/images/550000_6230000.tif"
                }
            ],
            "srs": "IGNF:LAMB93"
        }
        content = json.dumps(serialization, sort_keys=True)
        rasterset = RasterSet()
        rasterset.bbox = tuple(serialization["bbox"])
        rasterset.srs = serialization["srs"]
        rasterset.colors = []
        for color_dict in serialization["colors"]:
            rasterset.colors.append({"bands": color_dict["bands"],
                                     "format": ColorFormat[color_dict["format"]]})
        rasterset.raster_list = []
        for raster_dict in serialization["raster_list"]:
            raster_args = copy.deepcopy(raster_dict)
            raster_args["format"] = ColorFormat[raster_dict["format"]]
            raster_args["bbox"] = tuple(raster_dict["bbox"])
            raster_args["dimensions"] = tuple(raster_dict["dimensions"])
            rasterset.raster_list.append(MagicMock(Raster, **raster_args))

        try:
            rasterset.write_descriptor()
        except Exception as exc:
            assert False, f"Writing RasterSet's descriptor raises an exception: {exc}"

        mocked_print.assert_called_once_with(content)


