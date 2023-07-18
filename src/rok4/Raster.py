"""Provide functions to read information on raster data

The module contains the following class :

    - Raster - Structure describing raster data.
    - RasterSet - Structure describing a set of raster data.
"""

import copy
import json
import re
from enum import Enum
from typing import Dict, Tuple

from osgeo import gdal, ogr

from rok4.Storage import exists, get_osgeo_path, put_data_str
from rok4.Utils import ColorFormat, compute_bbox, compute_format

# Enable GDAL/OGR exceptions
ogr.UseExceptions()
gdal.UseExceptions()


class Raster:
    """A structure describing raster data

    Attributes :
        path (str): path to the file/object (ex:
          file:///path/to/image.tif or s3://bucket/path/to/image.tif)
        bbox (Tuple[float, float, float, float]): bounding rectange
          in the data projection
        bands (int): number of color bands (or channels)
        format (ColorFormat): numeric variable format for color values.
          Bit depth, as bits per channel, can be derived from it.
        mask (str): path to the associated mask file or object, if any,
          or None (same path as the image, but with a ".msk" extension
          and TIFF format. ex:
          file:///path/to/image.msk or s3://bucket/path/to/image.msk)
        dimensions (Tuple[int, int]): image width and height, in pixels
    """

    def __init__(self) -> None:
        self.bands = None
        self.bbox = (None, None, None, None)
        self.dimensions = (None, None)
        self.format = None
        self.mask = None
        self.path = None

    @classmethod
    def from_file(cls, path: str) -> "Raster":
        """Creates a Raster object from an image

        Args:
            path (str): path to the image file/object

        Examples:

            Loading informations from a file stored raster TIFF image

                from rok4.Raster import Raster

                try:
                    raster = Raster.from_file(
                        "file:///data/SC1000/0040_6150_L93.tif"
                    )

                except Exception as e:
                    print(f"Cannot load information from image : {e}")

        Raises:
            RuntimeError: raised by OGR/GDAL if anything goes wrong
            NotImplementedError: Storage type not handled

        Returns:
            Raster: a Raster instance
        """
        if not exists(path):
            raise Exception(f"No file or object found at path '{path}'.")

        self = cls()

        work_image_path = get_osgeo_path(path)

        image_datasource = gdal.Open(work_image_path)
        self.path = path

        path_pattern = re.compile("(/[^/]+?)[.][a-zA-Z0-9_-]+$")
        mask_path = path_pattern.sub("\\1.msk", path)

        if exists(mask_path):
            work_mask_path = get_osgeo_path(mask_path)
            mask_driver = gdal.IdentifyDriver(work_mask_path).ShortName
            if "GTiff" != mask_driver:
                message = (
                    f"Mask file '{mask_path}' is not a TIFF image."
                    + f" (GDAL driver : '{mask_driver}'"
                )
                raise Exception(message)
            self.mask = mask_path
        else:
            self.mask = None

        self.bbox = compute_bbox(image_datasource)
        self.bands = image_datasource.RasterCount
        self.format = compute_format(image_datasource, path)
        self.dimensions = (image_datasource.RasterXSize, image_datasource.RasterYSize)

        return self

    @classmethod
    def from_parameters(
        cls,
        path: str,
        bands: int,
        bbox: Tuple[float, float, float, float],
        dimensions: Tuple[int, int],
        format: ColorFormat,
        mask: str = None,
    ) -> "Raster":
        """Creates a Raster object from parameters

        Args:
            path (str): path to the file/object (ex:
              file:///path/to/image.tif or s3://bucket/image.tif)
            bands (int): number of color bands (or channels)
            bbox (Tuple[float, float, float, float]): bounding rectange
              in the data projection
            dimensions (Tuple[int, int]): image width and height
              expressed in pixels
            format (ColorFormat): numeric format for color values.
              Bit depth, as bits per channel, can be derived from it.
            mask (str, optionnal): path to the associated mask, if any,
              or None (same path as the image, but with a
              ".msk" extension and TIFF format. ex:
              file:///path/to/image.msk or s3://bucket/image.msk)

        Examples:

            Loading informations from parameters, related to
              a TIFF main image coupled to a TIFF mask image

                from rok4.Raster import Raster

                try:
                    raster = Raster.from_parameters(
                      path="file:///data/SC1000/_0040_6150_L93.tif",
                      mask="file:///data/SC1000/0040_6150_L93.msk",
                      bands=3,
                      format=ColorFormat.UINT8,
                      dimensions=(2000, 2000),
                      bbox=(40000.000, 5950000.000,
                            240000.000, 6150000.000)
                    )

                except Exception as e:
                    print(
                      f"Cannot load information from parameters : {e}"
                    )

        Raises:
            KeyError: a mandatory argument is missing

        Returns:
            Raster: a Raster instance
        """
        self = cls()

        self.path = path
        self.bands = bands
        self.bbox = bbox
        self.dimensions = dimensions
        self.format = format
        self.mask = mask
        return self


class RasterSet:
    """A structure describing a set of raster data

    Attributes :
        raster_list (List[Raster]): List of Raster instances in the set
        colors (List[Dict]): List of color properties for each raster
              instance. Contains only one element if
              the set is homogenous.
            Element properties:
                bands (int): number of color bands (or channels)
                format (ColorFormat): numeric variable format for
                  color values. Bit depth, as bits per channel,
                  can be derived from it.
        srs (str): Name of the set's spatial reference system
        bbox (Tuple[float, float, float, float]): bounding rectange
          in the data projection, enclosing the whole set
    """

    def __init__(self) -> None:
        self.bbox = (None, None, None, None)
        self.colors = []
        self.raster_list = []
        self.srs = None

    @classmethod
    def from_list(cls, path: str, srs: str) -> "RasterSet":
        """Instanciate a RasterSet from an images list path and a srs

        Args:
            path (str): path to the images list file or object
              (each line in this list contains the path to
              an image file or object in the set)

        Examples:

            Loading informations from a file stored list

                from rok4.Raster import RasterSet

                try:
                    raster_set = RasterSet.from_list(
                      path="file:///data/SC1000.list",
                      srs="EPSG:3857"
                    )

                except Exception as e:
                    print(
                      f"Cannot load information from list file : {e}"
                    )

        Raises:
            RuntimeError: raised by OGR/GDAL if anything goes wrong
            NotImplementedError: Storage type not handled

        Returns:
            RasterSet: a RasterSet instance
        """
        self = cls()
        self.srs = srs

        local_list_path = get_osgeo_path(path)
        image_list = []
        with open(file=local_list_path, mode="r") as list_file:
            for line in list_file:
                image_path = line.strip(" \t\n\r")
                image_list.append(image_path)

        temp_bbox = [None, None, None, None]
        for image_path in image_list:
            raster = Raster.from_file(image_path)
            self.raster_list.append(raster)
            if temp_bbox == [None, None, None, None]:
                for i in range(0, 4, 1):
                    temp_bbox[i] = raster.bbox[i]
            else:
                if temp_bbox[0] > raster.bbox[0]:
                    temp_bbox[0] = raster.bbox[0]
                if temp_bbox[1] > raster.bbox[1]:
                    temp_bbox[1] = raster.bbox[1]
                if temp_bbox[2] < raster.bbox[2]:
                    temp_bbox[2] = raster.bbox[2]
                if temp_bbox[3] < raster.bbox[3]:
                    temp_bbox[3] = raster.bbox[3]
            color_dict = {"bands": raster.bands, "format": raster.format}
            if color_dict not in self.colors:
                self.colors.append(color_dict)
        self.bbox = tuple(temp_bbox)
        return self

    @classmethod
    def from_descriptor(cls, path: str) -> "RasterSet":
        """Creates a RasterSet object from a descriptor file or object

        Args:
            path (str): path to the descriptor file or object

        Examples:

            Loading informations from a file stored descriptor

                from rok4.Raster import RasterSet

                try:
                    raster_set = RasterSet.from_descriptor(
                      "file:///data/images/descriptor.json"
                    )

                except Exception as e:
                    message = ("Cannot load information from "
                              + f"descriptor file : {e}")
                    print(message)

        Raises:
            RuntimeError: raised by OGR/GDAL if anything goes wrong
            NotImplementedError: Storage type not handled

        Returns:
            RasterSet: a RasterSet instance
        """
        self = cls()
        descriptor_path = get_osgeo_path(path)
        with open(file=descriptor_path, mode="r") as file_handle:
            raw_content = file_handle.read()
        serialization = json.loads(raw_content)
        self.srs = serialization["srs"]
        self.raster_list = []
        for raster_dict in serialization["raster_list"]:
            parameters = copy.deepcopy(raster_dict)
            parameters["bbox"] = tuple(raster_dict["bbox"])
            parameters["dimensions"] = tuple(raster_dict["dimensions"])
            parameters["format"] = ColorFormat[raster_dict["format"]]
            self.raster_list.append(Raster.from_parameters(**parameters))
        self.bbox = tuple(serialization["bbox"])
        self.colors = []
        for color_dict in serialization["colors"]:
            color_item = copy.deepcopy(color_dict)
            color_item["format"] = ColorFormat[color_dict["format"]]
            self.colors.append(color_item)
        return self

    @property
    def serializable(self) -> Dict:
        """Get the dict version of the raster set, descriptor compliant

        Returns:
            Dict: descriptor structured object description
        """
        serialization = {"bbox": list(self.bbox), "srs": self.srs, "colors": [], "raster_list": []}
        for color in self.colors:
            color_serial = {"bands": color["bands"], "format": color["format"].name}
            serialization["colors"].append(color_serial)
        for raster in self.raster_list:
            raster_dict = {
                "path": raster.path,
                "dimensions": list(raster.dimensions),
                "bbox": list(raster.bbox),
                "bands": raster.bands,
                "format": raster.format.name,
            }
            if raster.mask is not None:
                raster_dict["mask"] = raster.mask
            serialization["raster_list"].append(raster_dict)
        return serialization

    def write_descriptor(self, path: str = None) -> None:
        """Print raster set's descriptor as JSON

        Args:
            path (str, optional): Complete path (file or object)
              where to print the raster set's JSON. Defaults to None,
              JSON is printed to standard output.
        """
        content = json.dumps(self.serializable, sort_keys=True)
        if path is None:
            print(content)
        else:
            put_data_str(content, path)
