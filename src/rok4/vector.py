"""Provide class to read informations on vector data set from list or descriptor

The module contains the following class :

- `VectorSets` - Data Vector Sets
- `Vector` - Data Vector
- `Layer` - Layer(name, attributes(columns, types of attributes), count, srs, bbox)
"""

# -- IMPORTS --

# standard library
import os
import tempfile

# 3rd party
from osgeo import ogr

# package
from rok4.storage import copy, get_osgeo_path
from rok4.raster import 

# -- GLOBALS --

# Enable GDAL/OGR exceptions
ogr.UseExceptions()


class VectorSet:

    @classmethod
    def from_list(cls, path: str) -> "VectorSet":
        """Constructor method of a VectorSet from lists"""

    @classmethod
    def from_descriptor(cls, path: str) -> "VectorSet":
        """Constructor method of a VectorSet from the descriptor"""

class Vector:

    @classmethod
    def from_file(cls, path: str) -> "Vector":
        """Constructor method of a Vector from file"""

    @classmethod
    def from_parameters(cls, path: str) -> "Vector":
        """Constructor method of a Vector from the descriptor"""

class Layer:

    def __init__(self, name, attributes, count, srs, bbox) -> "Layer":
        """Constructor method of a Layer"""
        self.__name = name
        self.__attributes = attributes
        self.__count = count
        self.__srs = srs
        self.__bbox = bbox