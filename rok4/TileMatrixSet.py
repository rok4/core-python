"""Provide classes to use a tile matrix set.

The module contains the following classes:

- `TileMatrixSet` - Multi level grid
- `TileMatrix` - A tile matrix set level

Loading a tile matrix set requires environment variables :
- ROK4_TMS_DIRECTORY
"""

from rok4.Exceptions import *
from rok4.Storage import get_data_str

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
        except KeyError as e:
            raise MissingAttributeError(tms.path, f"tileMatrices[].{e}")

class TileMatrixSet:
    """A tile matrix set is multi levels grid definition

    Attributes:
        name (str): TMS's name
        path (str): TMS origin path (JSON)
        id (str): TMS identifier
        srs (str): TMS coordinates system
        levels (Dict[str, TileMatrix]): TMS levels
    """

    def __init__(self, name: str) -> None:
        """Constructor method

        Args:
            name: TMS's name

        Raises:
            MissingEnvironmentError: Missing object storage informations
            Exception: No level in the TMS
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
            self.levels = {}
            for l in data["tileMatrices"]:
                lev = TileMatrix(l, self)
                self.levels[lev.id] = lev

            if len(self.levels.keys()) == 0:
                raise Exception(f"TMS '{self.path}' has no level")

        except JSONDecodeError as e:
            raise FormatError("JSON", self.path, e)

        except KeyError as e:
            raise MissingAttributeError(self.path, e)

    def get_level(self, level_id: str) -> 'TileMatrix':
        """Get one level according to its identifier

        Args:
            level_id: Level identifier

        Returns:
            The corresponding tile matrix, None if not present
        """
      
        return self.levels.get(level_id, None)
