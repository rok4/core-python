"""Provide functions to manipulate OGR / OSR entities
"""

# -- IMPORTS --

# standard library
import os
import re
from typing import Dict, List, Tuple

# 3rd party
from osgeo import gdal, ogr, osr

# package
from rok4.enums import ColorFormat
from rok4.storage import get_data_str, get_osgeo_path

# -- GLOBALS --
ogr.UseExceptions()
osr.UseExceptions()
gdal.UseExceptions()

__SR_BOOK = {}


def srs_to_spatialreference(srs: str) -> "osgeo.osr.SpatialReference":
    """Convert coordinates system as string to OSR spatial reference

    Using a cache, to instanciate a Spatial Reference from a string only once.

    Args:
        srs (str): coordinates system PROJ4 compliant, with authority and code, like EPSG:3857 or IGNF:LAMB93

    Raises:
        RuntimeError: Provided SRS is invalid for OSR

    Returns:
        osgeo.osr.SpatialReference: Corresponding OSR spatial reference
    """

    global __SR_BOOK

    if srs.upper() not in __SR_BOOK:
        authority, code = srs.split(":", 1)

        sr = osr.SpatialReference()
        if authority.upper() == "EPSG":
            sr.ImportFromEPSG(int(code))
        else:
            sr.ImportFromProj4(f"+init={srs.upper()} +wktext")

        __SR_BOOK[srs.upper()] = sr

    return __SR_BOOK[srs.upper()]


def bbox_to_geometry(
    bbox: Tuple[float, float, float, float], densification: int = 0
) -> "osgeo.ogr.Geometry":
    """Convert bbox coordinates to OGR geometry

    Args:
        bbox (Tuple[float, float, float, float]): bounding box (xmin, ymin, xmax, ymax)
        densification (int, optional): Number of point to add for each side of bounding box. Defaults to 0.

    Returns:
        osgeo.ogr.Geometry: Corresponding OGR geometry
    """

    ring = ogr.Geometry(ogr.wkbLinearRing)

    if densification > 0:
        step_x = (bbox[2] - bbox[0]) / (densification + 1)
        step_y = (bbox[3] - bbox[1]) / (densification + 1)

        for i in range(densification + 1):
            ring.AddPoint(bbox[0] + step_x * i, bbox[1])
        for i in range(densification + 1):
            ring.AddPoint(bbox[2], bbox[1] + step_y * i)
        for i in range(densification + 1):
            ring.AddPoint(bbox[2] - step_x * i, bbox[3])
        for i in range(densification + 1):
            ring.AddPoint(bbox[0], bbox[3] - step_y * i)
        ring.AddPoint(bbox[0], bbox[1])

    else:
        ring.AddPoint(bbox[0], bbox[1])
        ring.AddPoint(bbox[2], bbox[1])
        ring.AddPoint(bbox[2], bbox[3])
        ring.AddPoint(bbox[0], bbox[3])
        ring.AddPoint(bbox[0], bbox[1])

    geom = ogr.Geometry(ogr.wkbPolygon)
    geom.AddGeometry(ring)
    geom.SetCoordinateDimension(2)

    return geom


def wkt_to_geometry(wkt: str) -> "osgeo.ogr.Geometry":
    """Convert WKT string to OGR geometry

    Args:
        wkt (str): WKT geometry

    Raises:
        RuntimeError: OGR/GDAL issue

    Returns:
        osgeo.ogr.Geometry: Corresponding OGR geometry
    """

    return ogr.CreateGeometryFromWkt(wkt)


def geojson_to_geometry(geojson: str) -> "osgeo.ogr.Geometry":
    """Convert GeoJSON string to OGR geometry

    Args:
        geojson (str): GeoJSON geometry

    Raises:
        RuntimeError: OGR/GDAL issue

    Returns:
        osgeo.ogr.Geometry: Corresponding OGR geometry
    """

    return ogr.CreateGeometryFromJson(geojson)


def path_to_geometry(path: str) -> "osgeo.ogr.Geometry":
    """Convert file content to OGR geometry

    We use format according to extension : .json and .geojson will be read as GeoJSON, other extensions as WKT

    Args:
        path (str): Path to file or object containing geometry.

    Raises:
        StorageError: Storage read issue
        RuntimeError: OGR/GDAL issue

    Returns:
        osgeo.ogr.Geometry: Corresponding OGR geometry
    """

    geometry_string = get_data_str(path)

    if path.endswith(".json") or path.endswith(".geojson"):
        return geojson_to_geometry(geometry_string)
    else:
        return wkt_to_geometry(geometry_string)


def reproject_geometry(
    geometry: "osgeo.ogr.Geometry", srs_src: str, srs_dst: str
) -> "osgeo.ogr.Geometry":
    """Return geometry in other coordinates system

    Points are added to be sure output bounding box contains input bounding box

    Args:
        geometry (osgeo.ogr.Geometry): geometry with source coordinates system
        srs_src (str): source coordinates system
        srs_dst (str): destination coordinates system

    Returns:
        osgeo.ogr.Geometry: geometry with destination coordinates system
    """

    sr_src = srs_to_spatialreference(srs_src)
    sr_src_inv = sr_src.EPSGTreatsAsLatLong() or sr_src.EPSGTreatsAsNorthingEasting()

    sr_dst = srs_to_spatialreference(srs_dst)
    sr_dst_inv = sr_dst.EPSGTreatsAsLatLong() or sr_dst.EPSGTreatsAsNorthingEasting()

    if sr_src.IsSame(sr_dst) and sr_src_inv == sr_dst_inv:
        # Les système sont vraiment les même, avec le même ordre des axes
        return geometry.Clone()
    elif sr_src.IsSame(sr_dst) and sr_src_inv != sr_dst_inv:
        # Les système sont les même pour OSR, mais l'ordre des axes est différent
        return geometry.Clone().SwapXY()

    # Systèmes différents

    geometry.AssignSpatialReference(sr_src)

    rgeometry = geometry.Clone()
    os.environ["OGR_ENABLE_PARTIAL_REPROJECTION"] = "YES"
    rgeometry.TransformTo(sr_dst)
    return rgeometry


def reproject_bbox(
    bbox: Tuple[float, float, float, float], srs_src: str, srs_dst: str, densification: int = 5
) -> Tuple[float, float, float, float]:
    """Return bounding box in other coordinates system

    Points are added to be sure output bounding box contains input bounding box

    Args:
        bbox (Tuple[float, float, float, float]): bounding box (xmin, ymin, xmax, ymax) with source coordinates system
        srs_src (str): source coordinates system
        srs_dst (str): destination coordinates system
        densification (int, optional): Number of point to add for each side of bounding box. Defaults to 5.

    Returns:
        Tuple[float, float, float, float]: bounding box (xmin, ymin, xmax, ymax) with destination coordinates system
    """

    sr_src = srs_to_spatialreference(srs_src)
    sr_src_inv = sr_src.EPSGTreatsAsLatLong() or sr_src.EPSGTreatsAsNorthingEasting()

    sr_dst = srs_to_spatialreference(srs_dst)
    sr_dst_inv = sr_dst.EPSGTreatsAsLatLong() or sr_dst.EPSGTreatsAsNorthingEasting()

    if sr_src.IsSame(sr_dst) and sr_src_inv == sr_dst_inv:
        # Les système sont vraiment les même, avec le même ordre des axes
        return bbox
    elif sr_src.IsSame(sr_dst) and sr_src_inv != sr_dst_inv:
        # Les système sont les même pour OSR, mais l'ordre des axes est différent
        return (bbox[1], bbox[0], bbox[3], bbox[2])

    # Systèmes différents

    bbox_src = bbox_to_geometry(bbox, densification)
    bbox_src.AssignSpatialReference(sr_src)

    bbox_dst = bbox_src.Clone()
    os.environ["OGR_ENABLE_PARTIAL_REPROJECTION"] = "YES"
    bbox_dst.TransformTo(sr_dst)

    env = bbox_dst.GetEnvelope()
    return (env[0], env[2], env[1], env[3])


def reproject_point(
    point: Tuple[float, float],
    sr_src: "osgeo.osr.SpatialReference",
    sr_dst: "osgeo.osr.SpatialReference",
) -> Tuple[float, float]:
    """Reproject a point

    Args:
        point (Tuple[float, float]): source spatial reference point
        sr_src (osgeo.osr.SpatialReference): source spatial reference
        sr_dst (osgeo.osr.SpatialReference): destination spatial reference

    Returns:
        Tuple[float, float]: X/Y in destination spatial reference
    """

    sr_src_inv = sr_src.EPSGTreatsAsLatLong() or sr_src.EPSGTreatsAsNorthingEasting()
    sr_dst_inv = sr_dst.EPSGTreatsAsLatLong() or sr_dst.EPSGTreatsAsNorthingEasting()

    if sr_src.IsSame(sr_dst) and sr_src_inv == sr_dst_inv:
        # Les système sont vraiment les mêmes, avec le même ordre des axes
        return (point[0], point[1])
    elif sr_src.IsSame(sr_dst) and sr_src_inv != sr_dst_inv:
        # Les système sont les même pour OSR, mais l'ordre des axes est différent
        return (point[1], point[0])

    # Systèmes différents
    ct = osr.CreateCoordinateTransformation(sr_src, sr_dst)
    x_dst, y_dst, z_dst = ct.TransformPoint(point[0], point[1])

    return (x_dst, y_dst)


def get_geometry_parts(
    geometry: "osgeo.ogr.Geometry",
) -> List[Tuple["osgeo.ogr.Geometry", Tuple[float, float, float, float]]]:
    parts = []
    geometry = ogr.ForceToMultiPolygon(geometry)
    for i in range(0, geometry.GetGeometryCount()):
        g = geometry.GetGeometryRef(i).Clone()
        env = g.GetEnvelope()
        parts.append((g, (env[0], env[2], env[1], env[3])))

    return parts


def intersects(geometry1: "osgeo.ogr.Geometry", geometry2: "osgeo.ogr.Geometry") -> bool:
    inter = geometry1.Intersection(geometry2)
    return inter is not None and inter.Area() > 0


def compute_bbox(source_dataset: gdal.Dataset) -> Tuple:
    """Image boundingbox computing method

    Args:
        source_dataset (gdal.Dataset): Dataset instanciated from the raster image

    Limitations:
        Image's axis must be parallel to SRS' axis

    Raises:
        AttributeError: source_dataset is not a gdal.Dataset instance.
        Exception: The dataset does not contain transform data.
    """
    bbox = None
    transform_vector = source_dataset.GetGeoTransform()
    if transform_vector is None:
        raise Exception(
            "No transform vector found in the dataset created from "
            + f"the following file : {source_dataset.GetFileList()[0]}"
        )
    width = source_dataset.RasterXSize
    height = source_dataset.RasterYSize
    x_range = (
        transform_vector[0],
        transform_vector[0] + width * transform_vector[1] + height * transform_vector[2],
    )
    y_range = (
        transform_vector[3],
        transform_vector[3] + width * transform_vector[4] + height * transform_vector[5],
    )
    spatial_ref = source_dataset.GetSpatialRef()
    if spatial_ref is not None and spatial_ref.GetDataAxisToSRSAxisMapping() == [2, 1]:
        # Coordonnées terrain de type (latitude, longitude)
        # => on permute les coordonnées terrain par rapport à l'image
        bbox = (min(y_range), min(x_range), max(y_range), max(x_range))
    else:
        # Coordonnées terrain de type (longitude, latitude) ou pas de SRS
        # => les coordonnées terrain sont dans le même ordre que celle de l'image
        bbox = (min(x_range), min(y_range), max(x_range), max(y_range))
    return bbox


def compute_format(dataset: gdal.Dataset, path: str = None) -> ColorFormat:
    """Image color format computing method

    Args:
        dataset (gdal.Dataset): Dataset instanciated from the image
        path (str, optionnal): path to the original file/object

    Raises:
        AttributeError: source_dataset is not a gdal.Dataset instance.
        Exception: No color band found or unsupported color format.
    """
    color_format = None
    if path is None:
        path = dataset.GetFileList()[0]
    if dataset.RasterCount < 1:
        raise Exception(f"Image {path} contains no color band.")

    band_1_datatype = dataset.GetRasterBand(1).DataType
    data_type_name = gdal.GetDataTypeName(band_1_datatype)
    data_type_size = gdal.GetDataTypeSize(band_1_datatype)
    color_interpretation = dataset.GetRasterBand(1).GetRasterColorInterpretation()
    color_name = None
    if color_interpretation is not None:
        color_name = gdal.GetColorInterpretationName(color_interpretation)
    compression_regex_match = re.search(r"COMPRESSION\s*=\s*PACKBITS", gdal.Info(dataset))

    if (
        data_type_name == "Byte"
        and data_type_size == 8
        and color_name == "Palette"
        and compression_regex_match
    ):
        # Compris par libTIFF comme du noir et blanc sur 1 bit
        color_format = ColorFormat.BIT
    elif data_type_name == "Byte" and data_type_size == 8:
        color_format = ColorFormat.UINT8
    elif data_type_name == "Float32" and data_type_size == 32:
        color_format = ColorFormat.FLOAT32
    else:
        raise Exception(
            f"Unsupported color format for image {path} : "
            + f"'{data_type_name}' ({data_type_size} bits)"
        )
    return color_format


def get_raster_infos(path: str) -> Dict:
    """Get image informations

    Args:
        path (str): Image's path (file or object) tp get informations

    Raises:
        RuntimeError: raised by OGR/GDAL if anything goes wrong
        NotImplementedError: Storage type not handled

    Returns:
        Dict: Informations about image : bbox (Tuple[float]), bands (int), format (ColorFormat) and dimensions (Tuple[int])
    """

    work_image_path = get_osgeo_path(path)

    image_datasource = gdal.Open(work_image_path)

    infos = {}
    infos["bbox"] = compute_bbox(image_datasource)
    infos["bands"] = image_datasource.RasterCount
    infos["format"] = compute_format(image_datasource, path)
    infos["dimensions"] = (image_datasource.RasterXSize, image_datasource.RasterYSize)

    return infos
