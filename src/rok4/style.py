"""Provide classes to use a ROK4 style.

The module contains the following classe:

- `Style` - Style descriptor, to convert raster data

Loading a style requires environment variables :

- ROK4_STYLES_DIRECTORY
"""

# -- IMPORTS --

# standard library
import json
import os
import re
from json.decoder import JSONDecodeError
from typing import Dict, List, Tuple

# package
from rok4.exceptions import FormatError, MissingAttributeError, MissingEnvironmentError
from rok4.storage import get_data_str, exists
from rok4.enums import ColorFormat

DEG_TO_RAD = 0.0174532925199432958

class Colour:
    """A palette's RGBA colour.

    Attributes:
        value (float): Value to convert to RGBA
        red (int): Red value (from 0 to 255)
        green (int): Green value (from 0 to 255)
        blue (int): Blue value (from 0 to 255)
        alpha (int): Alpha value (from 0 to 255)
    """

    def __init__(self, palette: Dict, style: "Style") -> None:
        """Constructor method

        Args:
            colour: Colour attributes, according to JSON structure
            style: Style object containing the palette's colour to create

        Examples:

            JSON colour section

                {
                    "value": 600,
                    "red": 220,
                    "green": 179,
                    "blue": 99,
                    "alpha": 255
                }

        Raises:
            MissingAttributeError: Attribute is missing in the content
            Exception: Invalid colour's band
        """

        try:
            self.value = palette["value"]

            self.red = palette["red"]
            if self.red < 0 or self.red > 255:
                raise Exception(f"In style '{style.path}', a palette colour band has an invalid value (integer between 0 and 255 expected)")
            self.green = palette["green"]
            if self.green < 0 or self.green > 255:
                raise Exception(f"In style '{style.path}', a palette colour band has an invalid value (integer between 0 and 255 expected)")
            self.blue = palette["blue"]
            if self.blue < 0 or self.blue > 255:
                raise Exception(f"In style '{style.path}', a palette colour band has an invalid value (integer between 0 and 255 expected)")
            self.alpha = palette["alpha"]
            if self.alpha < 0 or self.alpha > 255:
                raise Exception(f"In style '{style.path}', a palette colour band has an invalid value (integer between 0 and 255 expected)")

        except KeyError as e:
            raise MissingAttributeError(style.path, f"palette.colours[].{e}")

        except TypeError as e:
            raise Exception(f"In style '{style.path}', a palette colour band has an invalid value (integer between 0 and 255 expected)")

    @property
    def rgba(self) -> Tuple[int]:   
        return (self.red, self.green, self.blue, self.alpha)

    @property
    def rgb(self) -> Tuple[int]:   
        return (self.red, self.green, self.blue)
    

class Palette:
    """A style's RGBA palette.

    Attributes:
        no_alpha (bool): Colour without alpha band
        rgb_continuous (bool): Continuous RGB values ?
        alpha_continuous (bool): Continuous alpha values ?
        colours (List[Colour]): Palette's colours, input values ascending
    """

    def __init__(self, palette: Dict, style: "Style") -> None:
        """Constructor method

        Args:
            palette: Palette attributes, according to JSON structure
            style: Style object containing the palette to create

        Examples:

            JSON palette section

                {
                    "no_alpha": false,
                    "rgb_continuous": true,
                    "alpha_continuous": true,
                    "colours": [
                        { "value": -99999, "red": 255, "green": 255, "blue": 255, "alpha": 0 },
                        { "value": -99998.1, "red": 255, "green": 255, "blue": 255, "alpha": 0 },
                        { "value": -99998.0, "red": 255, "green": 0, "blue": 255, "alpha": 255 },
                        { "value": -501, "red": 255, "green": 0, "blue": 255, "alpha": 255 },
                        { "value": -500, "red": 1, "green": 29, "blue": 148, "alpha": 255 },
                        { "value": -15, "red": 19, "green": 42, "blue": 255, "alpha": 255 },
                        { "value": 0, "red": 67, "green": 105, "blue": 227, "alpha": 255 },
                        { "value": 0.01, "red": 57, "green": 151, "blue": 105, "alpha": 255 },
                        { "value": 300, "red": 230, "green": 230, "blue": 128, "alpha": 255 },
                        { "value": 600, "red": 220, "green": 179, "blue": 99, "alpha": 255 },
                        { "value": 2000, "red": 162, "green": 100, "blue": 51, "alpha": 255 },
                        { "value": 2500, "red": 122, "green": 81, "blue": 40, "alpha": 255 },
                        { "value": 3000, "red": 255, "green": 255, "blue": 255, "alpha": 255 },
                        { "value": 9000, "red": 255, "green": 255, "blue": 255, "alpha": 255 },
                        { "value": 9001, "red": 255, "green": 255, "blue": 255, "alpha": 255 }
                    ]
                }

        Raises:
            MissingAttributeError: Attribute is missing in the content
            Exception: No colour in the palette or invalid colour
        """

        try:
            self.no_alpha = palette["no_alpha"]
            self.rgb_continuous = palette["rgb_continuous"]
            self.alpha_continuous = palette["alpha_continuous"]

            self.colours = []
            for colour in palette["colours"]:
                self.colours.append(Colour(colour, style))
                if len(self.colours) >= 2 and self.colours[-1].value <= self.colours[-2].value:
                    raise Exception(f"Style '{style.path}' palette colours hav eto be ordered input value ascending")

            if len(self.colours) == 0:
                raise Exception(f"Style '{style.path}' palette has no colour")

        except KeyError as e:
            raise MissingAttributeError(style.path, f"palette.{e}")

    def convert(self, value: float) -> Tuple[int]:

        # Les couleurs dans la palette sont rangées par valeur croissante
        # On commence par gérer les cas où la valeur est en dehors de la palette

        if value <= self.colours[0].value:
            if self.no_alpha:
                return self.colours[0].rgb
            else:
                return self.colours[0].rgba

        if value >= self.colours[-1].value:
            if self.no_alpha:
                return self.colours[-1].rgb
            else:
                return self.colours[-1].rgba

        # On va maintenant chercher les deux couleurs entre lesquelles la valeur est 
        for i in range(1, len(self.colours)):
            if self.colours[i].value < value:
                continue

            # on est sur la première couleur de valeur supérieure
            colour_inf = self.colours[i-1]
            colour_sup = self.colours[i]
            break

        ratio = (value - colour_inf.value) / (colour_sup.value - colour_inf.value)
        if self.rgb_continuous:
            pixel = (
                colour_inf.red + ratio * (colour_sup.red - colour_inf.red),
                colour_inf.green + ratio * (colour_sup.green - colour_inf.green),
                colour_inf.blue + ratio * (colour_sup.blue - colour_inf.blue)
            )
        else:
            pixel = (colour_inf.red, colour_inf.green, colour_inf.blue)
        
        if self.no_alpha:
            return pixel
        else:
            if self.alpha_continuous:
                return pixel + (colour_inf.alpha + ratio * (colour_sup.alpha - colour_inf.alpha),)
            else:
                return pixel + (colour_inf.alpha,)

class Slope:
    """A style's slope parameters.

    Attributes:
        algo (str): Slope calculation algorithm chosen by the user ("H" for Horn)
        unit (str): Slope unit
        image_nodata (float): Nodata input value
        slope_nodata (float): Nodata slope value
        slope_max (float): Maximum value for the slope
    """

    def __init__(self, slope: Dict, style: "Style") -> None:
        """Constructor method

        Args:
            slope: Slope attributes, according to JSON structure
            style: Style object containing the slope to create

        Examples:

            JSON pente section

                {
                    "algo": "H",
                    "unit": "degree",
                    "image_nodata": -99999,
                    "slope_nodata": 91,
                    "slope_max": 90
                }

        Raises:
            MissingAttributeError: Attribute is missing in the content
        """

        try:
            self.algo = slope.get("algo", "H")
            self.unit = slope.get("unit", "degree")
            self.image_nodata = slope.get("image_nodata", -99999)
            self.slope_nodata = slope.get("slope_nodata", 0)
            self.slope_max = slope.get("slope_max", 90)
        except KeyError as e:
            raise MissingAttributeError(style.path, f"pente.{e}")

class Exposition:
    """A style's exposition parameters.

    Attributes:
        algo (str): Slope calculation algorithm chosen by the user ("H" for Horn)
        min_slope (int): Slope from which exposition is computed
        image_nodata (float): Nodata input value
        exposition_nodata (float): Nodata exposition value
    """

    def __init__(self, exposition: Dict, style: "Style") -> None:
        """Constructor method

        Args:
            exposition: Exposition attributes, according to JSON structure
            style: Style object containing the exposition to create

        Examples:

            JSON exposition section

                {
                    "algo": "H",
                    "min_slope": 1
                }

        Raises:
            MissingAttributeError: Attribute is missing in the content
        """

        try:
            self.algo = exposition.get("algo", "H")
            self.min_slope = exposition.get("min_slope", 1.0) * DEG_TO_RAD
            self.image_nodata = exposition.get("min_slope", -99999)
            self.exposition_nodata = exposition.get("aspect_nodata", -1)
        except KeyError as e:
            raise MissingAttributeError(style.path, f"exposition.{e}")


class Estompage:
    """A style's estompage parameters.

    Attributes:
        zenith (float): Sun's zenith in degree
        azimuth (float): Sun's azimuth in degree
        z_factor (int): Slope exaggeration factor
        image_nodata (float): Nodata input value
        estompage_nodata (float): Nodata estompage value
    """

    def __init__(self, estompage: Dict, style: "Style") -> None:
        """Constructor method

        Args:
            estompage: Estompage attributes, according to JSON structure
            style: Style object containing the estompage to create

        Examples:

            JSON estompage section

                {
                    "zenith": 45,
                    "azimuth": 315,
                    "z_factor": 1
                }

        Raises:
            MissingAttributeError: Attribute is missing in the content
        """

        try:
            # azimuth et azimuth sont converti en leur complémentaire en radian
            self.zenith = (90. - estompage.get("zenith", 45)) * DEG_TO_RAD
            self.azimuth = (360. - estompage.get("azimuth", 315)) * DEG_TO_RAD
            self.z_factor = estompage.get("z_factor", 1)
            self.image_nodata = estompage.get("image_nodata", -99999.0)
            self.estompage_nodata = estompage.get("estompage_nodata", 0.0)
        except KeyError as e:
            raise MissingAttributeError(style.path, f"estompage.{e}")

class Legend:
    """A style's legend.

    Attributes:
        format (str): Legend image's mime type
        url (str): Legend image's url
        height (int): Legend image's pixel height
        width (int): Legend image's pixel width
        min_scale_denominator (int): Minimum scale at which the legend is applicable
        max_scale_denominator (int): Maximum scale at which the legend is applicable
    """

    def __init__(self, legend: Dict, style: "Style") -> None:
        """Constructor method

        Args:
            legend: Legend attributes, according to JSON structure
            style: Style object containing the legend to create

        Examples:

            JSON legend section

                {
                    "format": "image/png",
                    "url": "http://ign.fr",
                    "height": 100,
                    "width": 100,
                    "min_scale_denominator": 0,
                    "max_scale_denominator": 30
                }

        Raises:
            MissingAttributeError: Attribute is missing in the content
        """

        try:
            self.format = legend["format"]
            self.url = legend["url"]
            self.height = legend["height"]
            self.width = legend["width"]
            self.min_scale_denominator = legend["min_scale_denominator"]
            self.max_scale_denominator = legend["max_scale_denominator"]
        except KeyError as e:
            raise MissingAttributeError(style.path, f"legend.{e}")

class Style:
    """A raster data style

    Attributes:
        path (str): TMS origin path (JSON)
        id (str): Style's technical identifier
        identifier (str): Style's public identifier
        title (str): Style's title
        abstract (str): Style's abstract
        keywords (List[str]): Style's keywords
        legend (Legend): Style's legend

        palette (Palette): Style's palette, optionnal
        estompage (Estompage): Style's estompage parameters, optionnal
        slope (Slope): Style's slope parameters, optionnal
        exposition (Exposition): Style's exposition parameters, optionnal

    """

    def __init__(self, id: str) -> None:
        """Constructor method

        Style's directory is defined with environment variable ROK4_STYLES_DIRECTORY. Provided id is used as file/object name, with pr without JSON extension

        Args:
            path: Style's id

        Raises:
            MissingEnvironmentError: Missing object storage informations
            StorageError: Storage read issue
            FileNotFoundError: Style file or object does not exist, with or without extension 
            FormatError: Provided path is not a well formed JSON
            MissingAttributeError: Attribute is missing in the content
            Exception: No colour in the palette or invalid colour
        """

        self.id = id

        try:
            self.path = os.path.join(os.environ["ROK4_STYLES_DIRECTORY"], f"{self.id}")
            if not exists(self.path):
                self.path = os.path.join(os.environ["ROK4_STYLES_DIRECTORY"], f"{self.id}.json")
                if not exists(self.path):
                    raise FileNotFoundError(f"{self.path}, even without extension")
        except KeyError as e:
            raise MissingEnvironmentError(e)


        try:
            data = json.loads(get_data_str(self.path))

            self.identifier = data["identifier"]
            self.title = data["title"]
            self.abstract = data["abstract"]
            self.keywords = data["keywords"]

            self.legend = Legend(data["legend"], self)

            if "palette" in data:
                self.palette = Palette(data["palette"], self)
            else:
                self.palette = None

            if "estompage" in data:
                self.estompage = Estompage(data["estompage"], self)
            else:
                self.estompage = None

            if "pente" in data:
                self.slope = Slope(data["pente"], self)
            else:
                self.slope = None

            if "exposition" in data:
                self.exposition = Exposition(data["exposition"], self)
            else:
                self.exposition = None


        except JSONDecodeError as e:
            raise FormatError("JSON", self.path, e)

        except KeyError as e:
            raise MissingAttributeError(self.path, e)

    @property
    def bands(self) -> int:
        """Bands count after style application

        Returns:
            int: Bands count after style application, None if style is identity
        """        
        if self.palette is not None:
            if self.palette.no_alpha:
                return 3
            else:
                return 4

        elif self.estompage is not None or self.exposition is not None or self.slope is not None:
            return 1

        else:
            return None

    @property
    def format(self) -> ColorFormat:
        """Bands format after style application

        Returns:
            ColorFormat: Bands format after style application, None if style is identity
        """    
        if self.palette is not None:
            return ColorFormat.UINT8

        elif self.estompage is not None or self.exposition is not None or self.slope is not None:
            return ColorFormat.FLOAT32

        else:
            return None

    @property
    def input_nodata(self) -> float:
        """Input nodata value

        Returns:
            float: Input nodata value, None if style is identity
        """    

        if self.estompage is not None:
            return self.estompage.image_nodata
        elif self.exposition is not None:
            return self.exposition.image_nodata
        elif self.slope is not None:
            return self.slope.image_nodata
        elif self.palette is not None:
            return self.palette.colours[0].value
        else:
            return None

    @property
    def is_identity(self) -> bool:
        """Is style identity

        Returns:
            bool: Is style identity
        """    

        return self.estompage is None and self.exposition is None and self.slope is None and self.palette is None

