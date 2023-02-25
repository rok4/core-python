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

from rok4.Exceptions import *
from rok4.TileMatrixSet import TileMatrixSet
from rok4.Storage import *

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
        max_bbox = self.__pyramid.tms.get_level(self.__id).tile_to_bbox(self.__tile_limits["max_col"], self.__tile_limits["min_row"])

        return (min_bbox[0], min_bbox[1], max_bbox[2], max_bbox[3])

    @property
    def resolution(self) -> str: 
        return self.__pyramid.tms.get_level(self.__id).resolution

    def update_limits(self, bbox: Tuple[float, float, float, float]) -> None:
        """Update tile limits, based on provided bounding box

        Args:
            bbox (Tuple[float, float, float, float]): terrain extent (xmin, ymin, xmax, ymax), in TMS coordinates system

        """
        print(self.id)
        print(self.__tile_limits)
        col_min, row_min, col_max, row_max = self.__pyramid.tms.get_level(self.__id).bbox_to_tiles(bbox)
        self.__tile_limits = {
            "min_row": row_min,
            "max_col": col_max,
            "max_row": row_max,
            "min_col": col_min
        }
        print(self.__tile_limits)


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
        return self.__raster_specifications

    @property
    def storage_type(self) -> StorageType: 
        return self.__storage["type"]

    @property
    def storage_root(self) -> StorageType: 
        return self.__storage["root"].split("@", 1)[0] # Suppression de l'éventuel hôte de spécification du cluster S3

    @property
    def storage_depth(self) -> int: 
        return self.__storage.get("depth", None)


    @property
    def storage_s3_cluster(self) -> str: 
        if self.__storage["type"] == StorageType.S3:
            try:
                return self.__storage["root"].split("@")[1]
            except IndexError:
                return None
        else:
            return None


    @storage_depth.setter
    def storage_depth(self, d) -> None:
        if "depth" in self.__storage and self.__storage["depth"] != d:
            raise Exception(f"Pyramid {pyramid.__descriptor} owns levels with different path depths")
        self.__storage["depth"] = d

    @property
    def own_masks(self) -> int: 
        return self.__masks

    @property
    def format(self) -> str: 
        return self.__format

    @property
    def bottom_level(self) -> 'Level': 
        return sorted(self.__levels.values(), key=lambda l: l.resolution)[0]

    @property
    def top_level(self) -> 'Level': 
        return sorted(self.__levels.values(), key=lambda l: l.resolution)[-1]

    @property
    def type(self) -> PyramidType:
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
        content = json.dumps(self.serializable)
        put_data_str(content, self.__descriptor)

    def get_infos_from_slab_path(self, path: str) -> Tuple[SlabType, str, int, int]:
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
        if self.__storage["type"] == StorageType.FILE:
            slab_path = os.path.join(slab_type.value, level, b36_path_encode(column, row, self.__storage["depth"]))
        else:
            slab_path = f"{slab_type.value}_{level}_{column}_{row}"
        
        if full:
            return get_path_from_infos(self.__storage["type"], self.__storage["root"], self.__name, slab_path )
        else:
            return slab_path
        

