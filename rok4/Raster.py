"""Provide functions to read information on raster data from file path or object path

The module contains the following class :

    - 'Raster' - Structure describing raster data.

"""

from osgeo import ogr

# Enable GDAL/OGR exceptions
ogr.UseExceptions()


class Raster():
    """A structure describing raster data

    Attributes :
        path (str): path to the file/object
        bbox (Tuple[float, float, float, float]): bounding rectange in the data projection
        samples (int): number of color channels
        mask (str): path to the associated mask file or object, if any (same name, but ".msk" extension)
    """

    def __init__(self, path: str) -> None:
        """Basic constructor method

        Args:
            path (str): path to the file/object

        """

        self.path = path
        self.bbox = ""
        self.samples = 3
        self.mask = ""

