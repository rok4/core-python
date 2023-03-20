"""Provide classes to use pyramid's data.

The module contains the following classes:

- `Pyramid` - Data container
- `Level` - Level of a pyramid
"""

from typing import Dict, List, Tuple, Union
import json
from json.decoder import JSONDecodeError
import os
import re
import numpy
import zlib
import io
import mapbox_vector_tile
from PIL import Image

from rok4.Exceptions import *
from rok4.TileMatrixSet import TileMatrixSet, TileMatrix
from rok4.Storage import *
from rok4.Utils import *

class PyramidType(Enum):
    RASTER = "RASTER"
    VECTOR = "VECTOR"

class SlabType(Enum):
    DATA = "DATA"
    MASK = "MASK"

def b36_number_encode(number: int) -> str:
    """Convert base-10 number to base-36

    Used alphabet is '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    Args:
        number (int): base-10 number

    Returns:
        str: base-36 number
    """

    alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    base36 = ''

    if 0 <= number < len(alphabet):
        return alphabet[number]

    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36

    return base36

def b36_number_decode(number: str) -> int:
    """Convert base-36 number to base-10

    Args:
        number (str): base-36 number

    Returns:
        int: base-10 number
    """
    return int(number, 36)

def b36_path_decode(path: str) -> Tuple[int, int]:
    """Get slab's column and row from a base-36 based path

    Args:
        path (str): slab's path

    Returns:
        Tuple[int, int]: slab's column and row
    """    

    path = path.replace('/', '')
    path = re.sub(r'(\.TIFF?)', "", path.upper())

    b36_column = ""
    b36_row = ""

    while len(path) > 0:
        b36_column += path[0]
        b36_row += path[1]
        path = path[2:]

    return b36_number_decode(b36_column), b36_number_decode(b36_row)


def b36_path_encode(column: int, row: int, slashs: int) -> str:
    """Convert slab indices to base-36 based path, with .tif extension

    Args:
        column (int): slab's column
        row (int): slab's row
        slashs (int): slashs' number (to split path)

    Returns:
        str: base-36 based path
    """    

    b36_column = b36_number_encode(column)
    b36_row = b36_number_encode(row)

    max_len = max(slashs + 1, len(b36_column), len(b36_row))

    b36_column = b36_column.rjust(max_len, "0")
    b36_row = b36_row.rjust(max_len, "0")

    b36_path = ""

    while len(b36_column) > 0:
        b36_path = b36_row[-1] + b36_path
        b36_path = b36_column[-1] + b36_path

        b36_column = b36_column[:-1]
        b36_row = b36_row[:-1]

        if slashs > 0:
            b36_path = "/" + b36_path
            slashs -= 1

    return f"{b36_path}.tif"

class Level:
    """A pyramid's level, raster or vector

    Attributes:
        __id (str): level's identifier. have to exist in the pyramid's used TMS
        __tile_limits (Dict[str, int]): minimum and maximum tiles' columns and rows of pyramid's content
        __slab_size (Tuple[int, int]): number of tile in a slab, widthwise and heightwise
        __tables (List[Dict]): for a VECTOR pyramid, description of vector content, tables and attributes
    """

    @classmethod
    def from_descriptor(cls, data: Dict, pyramid: 'Pyramid') -> 'Level':
        """Create a pyramid's level from the pyramid's descriptor levels element

        Args:
            data (Dict): level's information from the pyramid's descriptor
            pyramid (Pyramid): pyramid containing the level to create

        Raises:
            Exception: different storage or masks presence between the level and the pyramid
            MissingAttributeError: Attribute is missing in the content

        Returns:
            Pyramid: a Level instance
        """    
        level = cls()

        level.__pyramid = pyramid

        # Attributs communs
        try:
            level.__id = data["id"]
            level.__tile_limits = data["tile_limits"]
            level.__slab_size = (data["tiles_per_width"], data["tiles_per_height"],)

            # Informations sur le stockage : on les valide et stocke dans la pyramide
            if pyramid.storage_type.name != data["storage"]["type"]:
                raise Exception(f"Pyramid {pyramid.descriptor} owns levels using different storage types ({ data['storage']['type'] }) than its one ({pyramid.storage_type.name})")

            if pyramid.storage_type == StorageType.FILE:                    
                pyramid.storage_depth = data["storage"]["path_depth"]   
            
            if "mask_directory" in data["storage"] or "mask_prefix" in data["storage"]:
                if not pyramid.own_masks:
                    raise Exception(f"Pyramid {pyramid.__descriptor} does not define a mask format but level {level.__id} define mask storage informations")
            else:
                if pyramid.own_masks:
                    raise Exception(f"Pyramid {pyramid.__descriptor} define a mask format but level {level.__id} does not define mask storage informations")

        except KeyError as e:
            raise MissingAttributeError(pyramid.descriptor, f"levels[].{e}")

        # Attributs dans le cas d'un niveau vecteur
        if level.__pyramid.type == PyramidType.VECTOR :
            try:
                level.__tables = data["tables"]

            except KeyError as e:
                raise MissingAttributeError(pyramid.descriptor, f"levels[].{e}")

        return level

    @classmethod
    def from_other(cls, other: 'Level', pyramid: 'Pyramid') -> 'Level':
        """Create a pyramid's level from another one

        Args:
            other (Level): level to clone
            pyramid (Pyramid): new pyramid containing the new level

        Raises:
            Exception: different storage or masks presence between the level and the pyramid
            MissingAttributeError: Attribute is missing in the content

        Returns:
            Pyramid: a Level instance
        """

        level = cls()

        # Attributs communs
        level.__id = other.__id
        level.__pyramid = pyramid
        level.__tile_limits = other.__tile_limits
        level.__slab_size = other.__slab_size

        # Attributs dans le cas d'un niveau vecteur
        if level.__pyramid.type == PyramidType.VECTOR :
            level.__tables = other.__tables

        return level

    def __str__(self) -> str:
        return f"{self.__pyramid.type.name} pyramid's level '{self.__id}' ({self.__pyramid.storage_type.name} storage)"


    @property
    def serializable(self) -> Dict: 
        """Get the dict version of the pyramid object, pyramid's descriptor compliant

        Returns:
            Dict: pyramid's descriptor structured object description
        """   
        serialization = {
            "id": self.__id,
            "tiles_per_width": self.__slab_size[0],
            "tiles_per_height": self.__slab_size[1],
            "tile_limits": self.__tile_limits
        }

        if self.__pyramid.type == PyramidType.VECTOR:
            serialization["tables"] = self.__tables

        if self.__pyramid.storage_type == StorageType.FILE:
            serialization["storage"] = {
                "type": "FILE",
                "image_directory": f"{self.__pyramid.name}/DATA/{self.__id}",
                "path_depth": self.__pyramid.storage_depth
            }
            if self.__pyramid.own_masks:
                serialization["storage"]["mask_directory"] = f"{self.__pyramid.name}/MASK/{self.__id}"

        elif self.__pyramid.storage_type == StorageType.CEPH:
            serialization["storage"] = {
                "type": "CEPH",
                "image_prefix": f"{self.__pyramid.name}/DATA_{self.__id}",
                "pool_name": self.__pyramid.storage_root
            }
            if self.__pyramid.own_masks:
                serialization["storage"]["mask_prefix"] = f"{self.__pyramid.name}/MASK_{self.__id}"

        elif self.__pyramid.storage_type == StorageType.S3:
            serialization["storage"] = {
                "type": "S3",
                "image_prefix": f"{self.__pyramid.name}/DATA_{self.__id}",
                "bucket_name": self.__pyramid.storage_root
            }
            if self.__pyramid.own_masks:
                serialization["storage"]["mask_prefix"] = f"{self.__pyramid.name}/MASK_{self.__id}"

        return serialization

    @property
    def id(self) -> str: 
        return self.__id

    @property
    def bbox(self) -> Tuple[float, float, float, float]: 
        """Return level extent, based on tile limits

        Returns:
            Tuple[float, float, float, float]: level terrain extent (xmin, ymin, xmax, ymax)
        """        
        min_bbox = self.__pyramid.tms.get_level(self.__id).tile_to_bbox(self.__tile_limits["min_col"], self.__tile_limits["max_row"])
        print(min_bbox)
        max_bbox = self.__pyramid.tms.get_level(self.__id).tile_to_bbox(self.__tile_limits["max_col"], self.__tile_limits["min_row"])
        print(max_bbox)

        return (min_bbox[0], min_bbox[1], max_bbox[2], max_bbox[3])

    @property
    def resolution(self) -> str: 
        return self.__pyramid.tms.get_level(self.__id).resolution

    @property
    def tile_matrix(self) -> TileMatrix: 
        return self.__pyramid.tms.get_level(self.__id)

    @property
    def slab_width(self) -> int: 
        return self.__slab_size[0]

    @property
    def slab_height(self) -> int: 
        return self.__slab_size[1]

    def is_in_limits(self, column: int, row: int) -> bool:
        """Is the tile indices in limits ?

        Args:
            column (int): tile's column
            row (int): tile's row

        Returns:
            bool: True if tiles' limits contain the provided tile's indices
        """
        return self.__tile_limits["min_row"] <= row and self.__tile_limits["max_row"] >= row and self.__tile_limits["min_col"] <= column and self.__tile_limits["max_col"] >= column

    def set_limits_from_bbox(self, bbox: Tuple[float, float, float, float]) -> None:
        """Set tile limits, based on provided bounding box

        Args:
            bbox (Tuple[float, float, float, float]): terrain extent (xmin, ymin, xmax, ymax), in TMS coordinates system

        """
        
        col_min, row_min, col_max, row_max = self.__pyramid.tms.get_level(self.__id).bbox_to_tiles(bbox)
        self.__tile_limits = {
            "min_row": row_min,
            "max_col": col_max,
            "max_row": row_max,
            "min_col": col_min
        }


class Pyramid:

    """A data pyramid, raster or vector

    Attributes:
        __name (str): pyramid's name
        __descriptor (str): pyramid's descriptor path
        __list (str): pyramid's list path
        __tms (rok4.TileMatrixSet.TileMatrixSet): Used grid
        __levels (Dict[str, Level]): Pyramid's levels
        __format (str): Data format
        __storage (Dict[str, Union[rok4.Storage.StorageType,str,int]]): Pyramid's storage informations (type, root and depth if FILE storage)
        __raster_specifications (Dict): If raster pyramid, raster specifications
    """

    @classmethod
    def from_descriptor(cls, descriptor: str) -> 'Pyramid':
        """Create a pyramid from its descriptor

        Args:
            descriptor (str): pyramid's descriptor path

        Raises:
            FormatError: Provided path or the TMS is not a well formed JSON
            Exception: Level issue : no one in the pyramid or the used TMS, or level ID not defined in the TMS
            MissingAttributeError: Attribute is missing in the content
            StorageError: Storage read issue (pyramid descriptor or TMS)
            MissingEnvironmentError: Missing object storage informations or TMS root directory

        Returns:
            Pyramid: a Pyramid instance
        """        
        try:
            data = json.loads(get_data_str(descriptor))

        except JSONDecodeError as e:
            raise FormatError("JSON", descriptor, e)


        pyramid = cls()

        pyramid.__storage["type"], path, pyramid.__storage["root"], base_name = get_infos_from_path(descriptor)
        pyramid.__name = base_name[:-5] # on supprime l'extension.json
        pyramid.__descriptor = descriptor
        pyramid.__list = get_path_from_infos(pyramid.__storage["type"], pyramid.__storage["root"], f"{pyramid.__name}.list")

        try:
            # Attributs communs
            pyramid.__tms = TileMatrixSet(data["tile_matrix_set"])
            pyramid.__format = data["format"]

            # Attributs d'une pyramide raster
            if pyramid.type == PyramidType.RASTER :
                pyramid.__raster_specifications = data["raster_specifications"]

                if "mask_format" in data:
                    pyramid.__masks = True
                else:
                    pyramid.__masks = False

            # Niveaux
            for l in data["levels"]:
                lev = Level.from_descriptor(l, pyramid)
                pyramid.__levels[lev.id] = lev

                if pyramid.__tms.get_level(lev.id) is None:
                    raise Exception(f"Pyramid {descriptor} owns a level with the ID '{lev.id}', not defined in the TMS '{pyramid.tms.name}'")

        except KeyError as e:
            raise MissingAttributeError(descriptor, e)

        if len(pyramid.__levels.keys()) == 0:
            raise Exception(f"Pyramid '{descriptor}' has no level")

        return pyramid

    @classmethod
    def from_other(cls, other: 'Pyramid', name: str, storage: Dict) -> 'Pyramid':
        """Create a pyramid from another one

        Args:
            other (Pyramid): pyramid to clone
            name (str): new pyramid's name
            storage (Dict[str, Union[str, int]]): new pyramid's storage informations

        Raises:
            FormatError: Provided path or the TMS is not a well formed JSON
            Exception: Level issue : no one in the pyramid or the used TMS, or level ID not defined in the TMS
            MissingAttributeError: Attribute is missing in the content

        Returns:
            Pyramid: a Pyramid instance
        """
        try:
            # On convertit le type de stockage selon l'énumération
            storage["type"] = StorageType[storage["type"]]

            if storage["type"] == StorageType.FILE and name.find("/") != -1:
                raise Exception(f"A FILE stored pyramid's name cannot contain '/' : '{name}'")

            if storage["type"] == StorageType.FILE and "depth" not in storage:
                storage["depth"] = 2

            pyramid = cls()

            # Attributs communs
            pyramid.__name = name 
            pyramid.__storage = storage
            pyramid.__masks = other.__masks

            pyramid.__descriptor = get_path_from_infos(pyramid.__storage["type"], pyramid.__storage["root"], f"{pyramid.__name}.json")
            pyramid.__list = get_path_from_infos(pyramid.__storage["type"], pyramid.__storage["root"], f"{pyramid.__name}.list")
            pyramid.__tms = other.__tms
            pyramid.__format = other.__format

            # Attributs d'une pyramide raster
            if pyramid.type == PyramidType.RASTER :
                if other.own_masks:
                    pyramid.__masks = True
                else:
                    pyramid.__masks = False
                pyramid.__raster_specifications = other.__raster_specifications

            # Niveaux
            for l in other.__levels.values():
                lev = Level.from_other(l, pyramid)
                pyramid.__levels[lev.id] = lev


        except KeyError as e:
            raise MissingAttributeError(descriptor, e)

        return pyramid

    def __init__(self) -> None:
        self.__storage = dict()
        self.__levels = dict()
        self.__masks = None

    def __str__(self) -> str:
        return f"{self.type.name} pyramid '{self.__name}' ({self.__storage['type'].name} storage)"

    @property
    def serializable(self) -> Dict: 
        """Get the dict version of the pyramid object, descriptor compliant

        Returns:
            Dict: descriptor structured object description
        """        
        serialization = {
            "tile_matrix_set": self.__tms.name,
            "format": self.__format
        }

        serialization["levels"] = []
        sorted_levels = sorted(self.__levels.values(), key=lambda l: l.resolution, reverse=True)

        for l in sorted_levels:
            serialization["levels"].append(l.serializable)

        if self.type == PyramidType.RASTER:
            serialization["raster_specifications"] = self.__raster_specifications

        if self.__masks:
            serialization["mask_format"] = "TIFF_ZIP_UINT8"

        return serialization

    @property
    def list(self) -> str:
        return self.__list

    @property
    def descriptor(self) -> str:
        return self.__descriptor

    @property
    def name(self) -> str:
        return self.__name

    @property
    def tms(self) -> TileMatrixSet:
        return self.__tms
        
    @property
    def raster_specifications(self) -> Dict:
        """Get raster specifications for a RASTER pyramid

        Example:
            {
                "channels": 3,
                "nodata": "255,0,0",
                "photometric": "rgb",
                "interpolation": "bicubic"
            }
        
        Returns:
            Dict: Raster specifications, None if VECTOR pyramid
        """        
        return self.__raster_specifications

    @property
    def storage_type(self) -> StorageType: 
        """Get the storage type

        Returns:
            StorageType: FILE, S3 or CEPH
        """        
        return self.__storage["type"]

    @property
    def storage_root(self) -> str: 
        """Get the pyramid's storage root.

        If storage is S3, the used cluster is removed.

        Returns:
            str: Pyramid's storage root
        """        
        return self.__storage["root"].split("@", 1)[0] # Suppression de l'éventuel hôte de spécification du cluster S3

    @property
    def storage_depth(self) -> int: 
        return self.__storage.get("depth", None)


    @property
    def storage_s3_cluster(self) -> str:
        """Get the pyramid's storage S3 cluster (host name)

        Returns:
            str: the host if known, None if the default one have to be used or if storage is not S3
        """        
        if self.__storage["type"] == StorageType.S3:
            try:
                return self.__storage["root"].split("@")[1]
            except IndexError:
                return None
        else:
            return None


    @storage_depth.setter
    def storage_depth(self, d: int) -> None:
        """Set the tree depth for a FILE storage

        Args:
            d (int): file storage depth

        Raises:
            Exception: the depth is not equal to the already known depth
        """        
        if "depth" in self.__storage and self.__storage["depth"] != d:
            raise Exception(f"Pyramid {pyramid.__descriptor} owns levels with different path depths")
        self.__storage["depth"] = d

    @property
    def own_masks(self) -> bool:
        return self.__masks

    @property
    def format(self) -> str: 
        return self.__format

    @property
    def bottom_level(self) -> 'Level': 
        """Get the best resolution level in the pyramid

        Returns:
            Level: the bottom level
        """   
        return sorted(self.__levels.values(), key=lambda l: l.resolution)[0]

    @property
    def top_level(self) -> 'Level':
        """Get the low resolution level in the pyramid

        Returns:
            Level: the top level
        """        
        return sorted(self.__levels.values(), key=lambda l: l.resolution)[-1]

    @property
    def type(self) -> PyramidType:
        """Get the pyramid's type (RASTER or VECTOR) from its format

        Returns:
            PyramidType: RASTER or VECTOR
        """        
        if self.__format == "TIFF_PBF_MVT":
            return PyramidType.VECTOR
        else:
            return PyramidType.RASTER

    def get_level(self, level_id: str) -> 'Level':
        """Get one level according to its identifier

        Args:
            level_id: Level identifier

        Returns:
            The corresponding pyramid's level, None if not present
        """
      
        return self.__levels.get(level_id, None)


    def get_levels(self, bottom_id: str = None, top_id: str = None) -> List[Level]:
        """Get sorted levels from bottom and top provided

        Args:
            bottom_id (str): optionnal specific bottom level id. Defaults to None.
            top_id (str): optionnal specific top level id. Defaults to None.

        Raises:
            Exception: Provided levels are not consistent (bottom > top or not in the pyramid)

        Returns:
            List[Level]: asked sorted levels
        """

        sorted_levels = sorted(self.__levels.values(), key=lambda l: l.resolution)
        
        levels = []

        begin = False
        if bottom_id is None:
            # Pas de niveau du bas fourni, on commence tout en bas
            begin = True
        else:
            if self.get_level(bottom_id) is None:
                raise Exception(f"Pyramid {self.name} does not contain the provided bottom level {bottom_id}")

        if top_id is not None and self.get_level(top_id) is None:
            raise Exception(f"Pyramid {self.name} does not contain the provided top level {top_id}")

        end = False

        for l in sorted_levels:
            if not begin and l.id == bottom_id:
                begin = True

            if begin:
                levels.append(l)
                if top_id is not None and l.id == top_id:
                    end = True
                    break
                else:
                    continue
        
        if top_id is None:
            # Pas de niveau du haut fourni, on a été jusqu'en haut et c'est normal
            end = True

        if not begin or not end:
            raise Exception(f"Provided levels ids are not consistent to extract levels from the pyramid {self.name}")
      
        return levels

    def write_descriptor(self) -> None:
        """Write the pyramid's descriptor to the final location (in the pyramid's storage root)
        """        
        content = json.dumps(self.serializable)
        put_data_str(content, self.__descriptor)

    def get_infos_from_slab_path(self, path: str) -> Tuple[SlabType, str, int, int]:
        """Get the slab's indices from its storage path

        Args:
            path (str): Slab's storage path

        Returns:
            Tuple[SlabType, str, int, int]: Slab's type (DATA or MASK), level identifier, slab's column and slab's row
        """        
        if self.__storage["type"] == StorageType.FILE:
            parts = path.split("/")

            # Le partie du chemin qui contient la colonne et ligne de la dalle est à la fin, en fonction de la profondeur choisie
            # depth = 2 -> on doit utiliser les 3 dernières parties pour la conversion
            column, row = b36_path_decode('/'.join(parts[-(self.__storage["depth"]+1):]))
            level = parts[-(self.__storage["depth"]+2)]
            raw_slab_type = parts[-(self.__storage["depth"]+3)]

            # Pour être retro compatible avec l'ancien nommage
            if raw_slab_type == "IMAGE":
                raw_slab_type = "DATA"

            slab_type = SlabType[raw_slab_type]

            return slab_type, level, column, row
        else:
            parts = re.split(r'[/_]', path)
            column = parts[-2]
            row = parts[-1]
            level = parts[-3]
            raw_slab_type = parts[-4]

            # Pour être retro compatible avec l'ancien nommage
            if raw_slab_type == "IMG":
                raw_slab_type = "DATA"
            elif raw_slab_type == "MSK":
                raw_slab_type = "MASK"

            slab_type = SlabType[raw_slab_type]

            return slab_type, level, int(column), int(row)

    def get_slab_path_from_infos(self, slab_type: SlabType, level: str, column: int, row: int, full: bool = True) -> str:
        """Get slab's storage path from the indices

        Args:
            slab_type (SlabType): DATA or MASK
            level (str): Level identifier
            column (int): Slab's column
            row (int): Slab's row
            full (bool, optional): Full path or just relative path from pyramid storage root. Defaults to True.

        Returns:
            str: Absolute or relative slab's storage path
        """        
        if self.__storage["type"] == StorageType.FILE:
            slab_path = os.path.join(slab_type.value, level, b36_path_encode(column, row, self.__storage["depth"]))
        else:
            slab_path = f"{slab_type.value}_{level}_{column}_{row}"
        
        if full:
            return get_path_from_infos(self.__storage["type"], self.__storage["root"], self.__name, slab_path )
        else:
            return slab_path
        

    def get_tile_data_binary(self, level: str, column: int, row: int) -> str:
        """Get a pyramid's tile as binary string

        To get a tile, 3 steps :
            * calculate slab path from tile indice
            * read slab index to get offsets and sizes of slab's tiles
            * read the tile into the slab

        Args:
            level (str): Tile's level
            column (int): Tile's column
            row (int): Tile's row

        Limitations:
            Pyramids with one-tile slab are not handled

        Raises:
            Exception: Level not found in the pyramid
            NotImplementedError: Pyramid owns one-tile slabs
            MissingEnvironmentError: Missing object storage informations
            StorageError: Storage read issue

        Returns:
            str: data, as binary string, None if no data
        """

        level_object = self.get_level(level)
        
        if level_object is None:
            raise Exception(f"No level {level} in the pyramid")

        if level_object.slab_width == 1 and level_object.slab_height == 1:
            raise NotImplementedError(f"One-tile slab pyramid is not handled")

        if not level_object.is_in_limits(column, row):
            return None

        # Indices de la dalle
        slab_column = column // level_object.slab_width
        slab_row = row // level_object.slab_height

        # Indices de la tuile dans la dalle
        relative_tile_column = column % level_object.slab_width
        relative_tile_row = row % level_object.slab_height

        # Numéro de la tuile dans le header
        tile_index = relative_tile_row * level_object.slab_width + relative_tile_column

        # Calcul du chemin de la dalle contenant la tuile voulue
        slab_path = self.get_slab_path_from_infos(SlabType.DATA, level, slab_column, slab_row)

        # Récupération des offset et tailles des tuiles dans la dalle
        # Une dalle ROK4 a une en-tête fixe de 2048 octets, 
        # puis sont stockés les offsets (chacun sur 4 octets)
        # puis les tailles (chacune sur 4 octets)
        try:
            binary_index = get_data_binary(slab_path, (2048, 2 * 4 * level_object.slab_width * level_object.slab_height))
        except FileNotFoundError as e:
            # L'absence de la dalle est gérée comme simplement une absence de données
            return None

        offsets = numpy.frombuffer(
            binary_index,
            dtype = numpy.dtype('uint32'),
            count = level_object.slab_width * level_object.slab_height
        )
        sizes = numpy.frombuffer(
            binary_index,
            dtype = numpy.dtype('uint32'),
            offset = 4 * level_object.slab_width * level_object.slab_height,
            count = level_object.slab_width * level_object.slab_height
        )

        if sizes[tile_index] == 0:
            return None

        return get_data_binary(slab_path, (offsets[tile_index], sizes[tile_index]))

    def get_tile_data_raster(self, level: str, column: int, row: int) -> numpy.ndarray:
        """Get a raster pyramid's tile as 3-dimension numpy ndarray

        First dimension is the row, second one is column, third one is band.

        Args:
            level (str): Tile's level
            column (int): Tile's column
            row (int): Tile's row

        Limitations:
            Packbits (pyramid formats TIFF_PKB_FLOAT32 and TIFF_PKB_UINT8) and LZW (pyramid formats TIFF_LZW_FLOAT32 and TIFF_LZW_UINT8) compressions are not handled.

        Raises:
            Exception: Cannot get raster data for a vector pyramid
            Exception: Level not found in the pyramid
            NotImplementedError: Pyramid owns one-tile slabs
            NotImplementedError: Raster pyramid format not handled
            MissingEnvironmentError: Missing object storage informations
            StorageError: Storage read issue
            FormatError: Cannot decode tile

        Returns:
            str: data, as numpy array, None if no data
        """

        if self.type == PyramidType.VECTOR:
            raise Exception("Cannot get tile as raster data : it's a vector pyramid")

        binary_tile = self.get_tile_data_binary(level, column, row)

        if binary_tile is None:
            return None

        level_object = self.get_level(level)


        if self.__format == "TIFF_JPG_UINT8" or self.__format == "TIFF_JPG90_UINT8":
            
            try:
                img = Image.open(io.BytesIO(binary_tile))
            except Exception as e:
                raise FormatError("JPEG", "binary tile", e)
            
            data = numpy.asarray(img)

        elif self.__format == "TIFF_RAW_UINT8":
            data = numpy.frombuffer(
                binary_tile,
                dtype = numpy.dtype('uint8')
            )
            data.shape = (level_object.tile_matrix.tile_size[0], level_object.tile_matrix.tile_size[1], self.__raster_specifications["channels"]) 

        elif self.__format == "TIFF_PNG_UINT8":
            try:
                img = Image.open(io.BytesIO(binary_tile))
            except Exception as e:
                raise FormatError("PNG", "binary tile", e)
            
            data = numpy.asarray(img)

        elif self.__format == "TIFF_ZIP_UINT8":
            try:
                data = numpy.frombuffer(
                    zlib.decompress( binary_tile ),
                    dtype = numpy.dtype('uint8')
                )
            except Exception as e:
                raise FormatError("ZIP", "binary tile", e)

            data.shape = (level_object.tile_matrix.tile_size[0], level_object.tile_matrix.tile_size[1], self.__raster_specifications["channels"]) 

        elif self.__format == "TIFF_ZIP_FLOAT32":
            try:
                data = numpy.frombuffer(
                    zlib.decompress( binary_tile ),
                    dtype = numpy.dtype('float32')
                )
            except Exception as e:
                raise FormatError("ZIP", "binary tile", e)

            data.shape = (level_object.tile_matrix.tile_size[0], level_object.tile_matrix.tile_size[1], self.__raster_specifications["channels"]) 

        elif self.__format == "TIFF_RAW_FLOAT32":
            data = numpy.frombuffer(
                binary_tile,
                dtype = numpy.dtype('float32')
            )
            data.shape = (level_object.tile_matrix.tile_size[0], level_object.tile_matrix.tile_size[1], self.__raster_specifications["channels"]) 

        else:
            raise NotImplementedError(f"Cannot get tile as raster data for format {self.__format}")

        return data

    def get_tile_data_vector(self, level: str, column: int, row: int) -> Dict:
        """Get a vector pyramid's tile as GeoJSON dictionnary

        Args:
            level (str): Tile's level
            column (int): Tile's column
            row (int): Tile's row

        Raises:
            Exception: Cannot get vector data for a raster pyramid
            Exception: Level not found in the pyramid
            NotImplementedError: Pyramid owns one-tile slabs
            NotImplementedError: Vector pyramid format not handled
            MissingEnvironmentError: Missing object storage informations
            StorageError: Storage read issue
            FormatError: Cannot decode tile

        Returns:
            str: data, as GeoJSON dictionnary. None if no data
        """

        if self.type == PyramidType.RASTER:
            raise Exception("Cannot get tile as vector data : it's a raster pyramid")

        binary_tile = self.get_tile_data_binary(level, column, row)

        if binary_tile is None:
            return None

        level_object = self.get_level(level)

        if self.__format == "TIFF_PBF_MVT":
            try:
                data = mapbox_vector_tile.decode(binary_tile)
            except Exception as e:
                raise FormatError("PBF (MVT)", "binary tile", e)
        else:
            raise NotImplementedError(f"Cannot get tile as vector data for format {self.__format}")

        return data

    def get_tile_indices(self, x: float, y: float, level: str = None, **kwargs) -> Tuple[str, int, int, int, int]:
        """Get pyramid's tile and pixel indices from point's coordinates

        Used coordinates system have to be the pyramide one. If EPSG:4326, x is latitude and y longitude.

        Args:
            x (float): point's x
            y (float): point's y
            level (str, optional): Pyramid's level to take into account, the bottom one if None . Defaults to None.
            **srs (string): spatial reference system of provided coordinates, with authority and code (same as the pyramid's one if not provided)

        Raises:
            Exception: Cannot find level to calculate indices
            RuntimeError: Provided SRS is invalid for OSR

        Returns:
            Tuple[str, int, int, int, int]: Level identifier, tile's column, tile's row, pixel's (in the tile) column, pixel's row
        """

        level_object = self.bottom_level
        if level is not None:
            level_object = self.get_level(level)
        
        if level_object is None:
            raise Exception(f"Cannot found the level to calculate indices")

        if "srs" in kwargs and kwargs["srs"] is not None and kwargs["srs"].upper() != self.__tms.srs.upper():
            sr = srs_to_spatialreference(kwargs["srs"])
            x, y = reproject_point((x, y), sr, self.__tms.sr )

        return (level_object.id,) + level_object.tile_matrix.point_to_indices(x, y)
