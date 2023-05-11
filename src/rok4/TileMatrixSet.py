"""Provide classes to use a tile matrix set.

The module contains the following classes:

- `TileMatrixSet` - Multi level grid
- `TileMatrix` - A tile matrix set level

Loading a tile matrix set requires environment variables :
- ROK4_TMS_DIRECTORY
"""

from rok4.Exceptions import *
from rok4.Storage import get_data_str
from rok4.Utils import *

from typing import Dict, List, Tuple
from json.decoder import JSONDecodeError
import json
import os

class TileMatrix:
    """A tile matrix is a tile matrix set's level.

    Attributes:
        id (str): TM identifiant (no underscore).
        tms (TileMatrixSet): TMS to whom it belong
        resolution (float): Ground size of a pixel, using unity of the TMS's coordinate system.
        origin (Tuple[float, float]): X,Y coordinates of the upper left corner for the level, the grid's origin.
        tile_size (Tuple[int, int]): Pixel width and height of a tile.
        matrix_size (Tuple[int, int]): Number of tile in the level, widthwise and heightwise.
    """

    def __init__(self, level: Dict, tms: 'TileMatrixSet') -> None:
        """Constructor method

        Args:
            level: Level attributes, according to JSON structure
            tms: TMS object containing the level to create

        Raises:
            MissingAttributeError: Attribute is missing in the content
        """

        self.tms = tms
        try:
            self.id = level["id"]
            if self.id.find("_") != -1:
                raise Exception(f"TMS {tms.path} owns a level whom id contains an underscore ({self.id})")
            self.resolution = level["cellSize"]
            self.origin = (level["pointOfOrigin"][0], level["pointOfOrigin"][1],)
            self.tile_size = (level["tileWidth"], level["tileHeight"],)
            self.matrix_size = (level["matrixWidth"], level["matrixHeight"],)
            self.__latlon = (self.tms.sr.EPSGTreatsAsLatLong() or self.tms.sr.EPSGTreatsAsNorthingEasting())
        except KeyError as e:
            raise MissingAttributeError(tms.path, f"tileMatrices[].{e}")

    def x_to_column(self, x: float) -> int:
        """Convert west-east coordinate to tile's column

        Args:
            x (float): west-east coordinate (TMS coordinates system)

        Returns:
            int: tile's column
        """
        return int((x - self.origin[0]) / (self.resolution * self.tile_size[0]))

    def y_to_row(self, y: float) -> int:
        """Convert north-south coordinate to tile's row

        Args:
            y (float): north-south coordinate (TMS coordinates system)

        Returns:
            int: tile's row
        """
        return int((self.origin[1] - y) / (self.resolution * self.tile_size[1]))

    def tile_to_bbox(self, tile_col: int, tile_row: int) -> Tuple[float, float, float, float]:
        """Get tile terrain extent (xmin, ymin, xmax, ymax), in TMS coordinates system

        TMS spatial reference is Lat / Lon case is handled.

        Args:
            tile_col (int): column indice
            tile_row (int): row indice

        Returns:
            Tuple[float, float, float, float]: terrain extent (xmin, ymin, xmax, ymax)
        """
        if self.__latlon:
            return (
                self.origin[1] - self.resolution * (tile_row + 1) * self.tile_size[1],
                self.origin[0] + self.resolution * tile_col * self.tile_size[0],
                self.origin[1] - self.resolution * tile_row * self.tile_size[1],
                self.origin[0] + self.resolution * (tile_col + 1) * self.tile_size[0]
            )
        else:
            return (
                self.origin[0] + self.resolution * tile_col * self.tile_size[0],
                self.origin[1] - self.resolution * (tile_row + 1) * self.tile_size[1],
                self.origin[0] + self.resolution * (tile_col + 1) * self.tile_size[0],
                self.origin[1] - self.resolution * tile_row * self.tile_size[1]
            )

    def bbox_to_tiles(self, bbox: Tuple[float, float, float, float]) -> Tuple[int, int, int, int]:
        """Get extrems tile columns and rows corresponding to provided bounding box

        TMS spatial reference is Lat / Lon case is handled.

        Args:
            bbox (Tuple[float, float, float, float]): bounding box (xmin, ymin, xmax, ymax), in TMS coordinates system

        Returns:
            Tuple[int, int, int, int]: extrem tiles (col_min, row_min, col_max, row_max)
        """

        if self.__latlon:
            return (
                self.x_to_column(bbox[1]),
                self.y_to_row(bbox[2]),
                self.x_to_column(bbox[3]),
                self.y_to_row(bbox[0])
            )
        else:
            return (
                self.x_to_column(bbox[0]),
                self.y_to_row(bbox[3]),
                self.x_to_column(bbox[2]),
                self.y_to_row(bbox[1])
            )

    def point_to_indices(self, x: float, y: float) -> Tuple[int, int, int, int]:
        """Get pyramid's tile and pixel indices from point's coordinates

        TMS spatial reference with Lat / Lon order is handled.

        Args:
            x (float): point's x
            y (float): point's y

        Returns:
            Tuple[int, int, int, int]: tile's column, tile's row, pixel's (in the tile) column, pixel's row
        """

        if self.__latlon:
            absolute_pixel_column = int((y - self.origin[0]) / self.resolution)
            absolute_pixel_row = int((self.origin[1] - x) / self.resolution)
        else:
            absolute_pixel_column = int((x - self.origin[0]) / self.resolution)
            absolute_pixel_row = int((self.origin[1] - y) / self.resolution)

        return absolute_pixel_column // self.tile_size[0], absolute_pixel_row // self.tile_size[1], absolute_pixel_column % self.tile_size[0], absolute_pixel_row % self.tile_size[1]

class TileMatrixSet:
    """A tile matrix set is multi levels grid definition

    Attributes:
        name (str): TMS's name
        path (str): TMS origin path (JSON)
        id (str): TMS identifier
        srs (str): TMS coordinates system
        sr (osgeo.osr.SpatialReference): TMS OSR spatial reference
        levels (Dict[str, TileMatrix]): TMS levels
    """

    def __init__(self, name: str) -> None:
        """Constructor method

        Args:
            name: TMS's name

        Raises:
            MissingEnvironmentError: Missing object storage informations
            Exception: No level in the TMS, CRS not recognized by OSR
            StorageError: Storage read issue
            FormatError: Provided path is not a well formed JSON
            MissingAttributeError: Attribute is missing in the content
        """

        self.name = name

        try:
            self.path = os.path.join(os.environ["ROK4_TMS_DIRECTORY"], f"{self.name}.json");
        except KeyError as e:
            raise MissingEnvironmentError(e)

        try:
            data = json.loads(get_data_str(self.path))

            self.id = data["id"]
            self.srs = data["crs"]
            self.sr = srs_to_spatialreference(self.srs)
            self.levels = {}
            for l in data["tileMatrices"]:
                lev = TileMatrix(l, self)
                self.levels[lev.id] = lev

            if len(self.levels.keys()) == 0:
                raise Exception(f"TMS '{self.path}' has no level")

            if data["orderedAxes"] != ["X", "Y"] and data["orderedAxes"] != ["Lon", "Lat"]:
                raise Exception(f"TMS '{self.path}' own invalid axes order : only X/Y or Lon/Lat are handled")

        except JSONDecodeError as e:
            raise FormatError("JSON", self.path, e)

        except KeyError as e:
            raise MissingAttributeError(self.path, e)

        except RuntimeError as e:
            raise Exception(f"Wrong attribute 'crs' ('{self.srs}') in '{self.path}', not recognize by OSR")

    def get_level(self, level_id: str) -> 'TileMatrix':
        """Get one level according to its identifier

        Args:
            level_id: Level identifier

        Returns:
            The corresponding tile matrix, None if not present
        """

        return self.levels.get(level_id, None)

    @property
    def sorted_levels(self) -> List[TileMatrix]:
        return sorted(self.levels.values(), key=lambda l: l.resolution)
