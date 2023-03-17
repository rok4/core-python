"""Provide classes to use a layer.

The module contains the following classe:

- `Layer` - Descriptor to broadcast pyramids' data
"""

from typing import Dict, List, Tuple, Union
import json
from json.decoder import JSONDecodeError
import os
import re

from rok4.Exceptions import *
from rok4.Pyramid import Pyramid, PyramidType
from rok4.TileMatrixSet import TileMatrixSet
from rok4.Storage import *
from rok4.Utils import *

class Layer:
    """A data layer, raster or vector

    Attributes:
        __name (str): layer's technical name
        __pyramids (Dict[str, Union[rok4.Pyramid.Pyramid,str,str]]): used pyramids
        __format (str): pyramid's list path
        __tms (rok4.TileMatrixSet.TileMatrixSet): Used grid
        __keywords (List[str]): Keywords
        __levels (Dict[str, rok4.Pyramid.Level]): Used pyramids' levels
        __best_level (rok4.Pyramid.Level): Used pyramids best level
        __resampling (str): Interpolation to use fot resampling
        __bbox (Tuple[float, float, float, float]): data bounding box, TMS coordinates system
        __geobbox (Tuple[float, float, float, float]): data bounding box, EPSG:4326
    """

    @classmethod
    def from_descriptor(cls, descriptor: str) -> 'Layer':
        """Create a layer from its descriptor

        Args:
            descriptor (str): layer's descriptor path

        Raises:
            FormatError: Provided path is not a well formed JSON
            MissingAttributeError: Attribute is missing in the content
            StorageError: Storage read issue (layer descriptor)
            MissingEnvironmentError: Missing object storage informations

        Returns:
            Layer: a Layer instance
        """        
        try:
            data = json.loads(get_data_str(descriptor))

        except JSONDecodeError as e:
            raise FormatError("JSON", descriptor, e)

        layer = cls()

        storage_type, path, root, base_name = get_infos_from_path(descriptor)
        layer.__name = base_name[:-5] # on supprime l'extension.json

        try:
            # Attributs communs
            layer.__title = data["title"]
            layer.__abstract = data["abstract"]
            layer.__load_pyramids(data["pyramids"])

            # Paramètres optionnels
            if "keywords" in data:
                for k in data["keywords"]:
                    layer.__keywords.append(k)


            if layer.type == PyramidType.RASTER: 
                if "resampling" in data:
                    layer.__resampling = data["resampling"]

                if "styles" in data:
                    layer.__styles = data["styles"]
                else:
                    layer.__styles = ["normal"]

            # Les bbox, native et géographique
            if "bbox" in data:
                layer.__geobbox = (data["bbox"]["south"], data["bbox"]["west"], data["bbox"]["north"], data["bbox"]["east"])
                layer.__bbox = reproject_bbox(layer.__geobbox, "EPSG:4326", layer.__tms.srs, 5)
                # On force l'emprise de la couche, on recalcule donc les tuiles limites correspondantes pour chaque niveau
                for l in layer.__levels.values():
                    l.set_limits_from_bbox(layer.__bbox)
            else:
                layer.__bbox = layer.__best_level.bbox
                layer.__geobbox = reproject_bbox(layer.__bbox, layer.__tms.srs, "EPSG:4326", 5)

        except KeyError as e:
            raise MissingAttributeError(descriptor, e)


        return layer

    @classmethod
    def from_parameters(cls, pyramids: List[Dict[str, str]], name: str, **kwargs) -> 'Layer':
        """Create a default layer from parameters

        Args:
            pyramids (List[Dict[str, str]]): pyramids to use and extrem levels, bottom and top
            name (str): layer's technical name
            **title (str): Layer's title (will be equal to name if not provided)
            **abstract (str): Layer's abstract (will be equal to name if not provided)
            **styles (List[str]): Styles identifier to authorized for the layer
            **resampling (str): Interpolation to use for resampling

        Raises:
            Exception: name contains forbidden characters or used pyramids do not shared same parameters (format, tms...)

        Returns:
            Layer: a Layer instance
        """

        layer = cls()

        # Informations obligatoires
        if not re.match("^[A-Za-z0-9_-]*$", name):
            raise Exception(f"Layer's name have to contain only letters, number, hyphen and underscore, to be URL and storage compliant ({name})")

        layer.__name = name
        layer.__load_pyramids(pyramids)

        # Les bbox, native et géographique
        layer.__bbox = layer.__best_level.bbox
        layer.__geobbox = reproject_bbox(layer.__bbox, layer.__tms.srs, "EPSG:4326", 5)

        # Informations calculées
        layer.__keywords.append(layer.type.name)
        layer.__keywords.append(layer.__name)

        # Informations optionnelles
        if "title" in kwargs and kwargs["title"] is not None:
            layer.__title = kwargs["title"]
        else:
            layer.__title = name

        if "abstract" in kwargs and kwargs["abstract"] is not None:
            layer.__abstract = kwargs["abstract"]
        else:
            layer.__abstract = name

        if layer.type == PyramidType.RASTER: 
            if "styles" in kwargs and kwargs["styles"] is not None and len(kwargs["styles"]) > 0:
                layer.__styles = kwargs["styles"]
            else:
                layer.__styles = ["normal"]

            if "resampling" in kwargs and kwargs["resampling"] is not None:
                layer.__resampling = kwargs["resampling"]

        return layer


    def __init__(self) -> None:
        self.__format = None
        self.__tms = None
        self.__best_level = None
        self.__levels = dict()
        self.__keywords = []
        self.__pyramids = []

    def __load_pyramids(self, pyramids: List[Dict[str, str]]) -> None:
        """Load and check pyramids

        Args:
            pyramids (List[Dict[str, str]]): List of descriptors' paths and optionnaly top and bottom levels

        Raises:
            Exception: Pyramids' do not all own the same format
            Exception: Pyramids' do not all own the same TMS
            Exception: Pyramids' do not all own the same channels number
            Exception: Overlapping in usage pyramids' levels
        """        

        ## Toutes les pyramides doivent avoir les même caractéristiques
        channels = None
        for p in pyramids:

            pyramid = Pyramid.from_descriptor(p["path"])
            bottom_level = p.get("bottom_level", None)
            top_level = p.get("top_level", None)

            if bottom_level is None:
                bottom_level = pyramid.bottom_level.id

            if top_level is None:
                top_level = pyramid.top_level.id

            if self.__format is not None and self.__format != pyramid.format:
                raise Exception(f"Used pyramids have to own the same format : {self.__format} != {pyramid.format}")
            else:
                self.__format = pyramid.format

            if self.__tms is not None and self.__tms.id != pyramid.tms.id:
                raise Exception(f"Used pyramids have to use the same TMS : {self.__tms.id} != {pyramid.tms.id}")
            else:
                self.__tms = pyramid.tms

            if self.type == PyramidType.RASTER:
                if channels is not None and channels != pyramid.raster_specifications["channels"]:
                    raise Exception(f"Used RASTER pyramids have to own the same number of channels : {channels} != {pyramid.raster_specifications['channels']}")
                else:
                    channels = pyramid.raster_specifications["channels"]
                self.__resampling = pyramid.raster_specifications["interpolation"]

            levels = pyramid.get_levels(bottom_level, top_level)
            for l in levels:
                if l.id in self.__levels:
                    raise Exception(f"Level {l.id} is present in two used pyramids")
                self.__levels[l.id] = l

            self.__pyramids.append({
                "pyramid": pyramid,
                "bottom_level": bottom_level,
                "top_level": top_level
            })

        self.__best_level = sorted(self.__levels.values(), key=lambda l: l.resolution)[0]

    def __str__(self) -> str:
        return f"{self.type.name} layer '{self.__name}'"

    @property
    def serializable(self) -> Dict: 
        """Get the dict version of the layer object, descriptor compliant

        Returns:
            Dict: descriptor structured object description
        """        
        serialization = {
            "title": self.__title,
            "abstract": self.__abstract,
            "keywords": self.__keywords,
            "wmts": {
                "authorized": True
            },
            "tms": {
                "authorized": True
            },
            "bbox": {
                "south": self.__geobbox[0],
                "west": self.__geobbox[1],
                "north": self.__geobbox[2],
                "east": self.__geobbox[3]
            },
            "pyramids": []
        }

        for p in self.__pyramids:
            serialization["pyramids"].append({
                "bottom_level" : p["bottom_level"],
                "top_level" : p["top_level"],
                "path" : p["pyramid"].descriptor
            })

        if self.type == PyramidType.RASTER:
            serialization["wms"] = {
                "authorized": True,
                "crs": [
                    "CRS:84",
                    "IGNF:WGS84G",
                    "EPSG:3857",
                    "EPSG:4258",
                    "EPSG:4326"
                ]
            }

            if self.__tms.srs.upper() not in serialization["wms"]["crs"]:
                serialization["wms"]["crs"].append(self.__tms.srs.upper())
            
            serialization["styles"] = self.__styles
            serialization["resampling"] = self.__resampling

        return serialization

    def write_descriptor(self, directory: str = None) -> None:
        """Print layer's descriptor as JSON

        Args:
            directory (str, optional): Directory (file or object) where to print the layer's descriptor, called <layer's name>.json. Defaults to None, JSON is printed to standard output.
        """        
        content = json.dumps(self.serializable)

        if directory is None:
            print(content)
        else:
            put_data_str(content, os.path.join(directory, f"{self.__name}.json"))

    @property
    def type(self) -> PyramidType:
        if self.__format == "TIFF_PBF_MVT":
            return PyramidType.VECTOR
        else:
            return PyramidType.RASTER

    @property
    def bbox(self) -> Tuple[float, float, float, float]:
        return self.__bbox

    @property
    def geobbox(self) -> Tuple[float, float, float, float]:
        return self.__geobbox

