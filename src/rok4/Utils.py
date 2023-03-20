"""Provide functions to manipulate OGR / OSR entities
"""

import os

from typing import Dict, List, Tuple, Union
from osgeo import ogr, osr
ogr.UseExceptions()
osr.UseExceptions()

__SR_BOOK = dict()
def srs_to_spatialreference(srs: str) -> 'osgeo.osr.SpatialReference':
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

        authority, code = srs.split(':', 1)

        sr = osr.SpatialReference()
        if authority.upper() == "EPSG":
            sr.ImportFromEPSG(int(code))
        else:
            sr.ImportFromProj4(f"+init={srs.upper()} +wktext")

        __SR_BOOK[srs.upper()] = sr


    return __SR_BOOK[srs.upper()]

def bbox_to_geometry(bbox: Tuple[float, float, float, float], densification: int = 0) -> 'osgeo.ogr.Geometry':  
    """Convert bbox coordinates to OGR geometry

    Args:
        bbox (Tuple[float, float, float, float]): bounding box (xmin, ymin, xmax, ymax)
        densification (int, optional): Number of point to add for each side of bounding box. Defaults to 0.

    Raises:
        RuntimeError: Provided SRS is invalid for OSR
        
    Returns:
        osgeo.ogr.Geometry: Corresponding OGR geometry, with spatial reference if provided
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



def reproject_bbox(bbox: Tuple[float, float, float, float], srs_src: str, srs_dst: str, densification: int = 5) -> Tuple[float, float, float, float]:
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
    sr_src_inv = (sr_src.EPSGTreatsAsLatLong() or sr_src.EPSGTreatsAsNorthingEasting())

    sr_dst = srs_to_spatialreference(srs_dst)
    sr_dst_inv = (sr_dst.EPSGTreatsAsLatLong() or sr_dst.EPSGTreatsAsNorthingEasting())

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


def reproject_point(point: Tuple[float, float], sr_src: 'osgeo.osr.SpatialReference', sr_dst: 'osgeo.osr.SpatialReference') -> Tuple[float, float]:
    """Reproject a point

    Args:
        point (Tuple[float, float]): source spatial reference point
        sr_src (osgeo.osr.SpatialReference): source spatial reference
        sr_dst (osgeo.osr.SpatialReference): destination spatial reference

    Returns:
        Tuple[float, float]: X/Y in destination spatial reference
    """

    sr_src_inv = (sr_src.EPSGTreatsAsLatLong() or sr_src.EPSGTreatsAsNorthingEasting())
    sr_dst_inv = (sr_dst.EPSGTreatsAsLatLong() or sr_dst.EPSGTreatsAsNorthingEasting())

    if sr_src.IsSame(sr_dst) and sr_src_inv == sr_dst_inv:
        # Les système sont vraiment les même, avec le même ordre des axes
        return (point[0], point[1])
    elif sr_src.IsSame(sr_dst) and sr_src_inv != sr_dst_inv:
        # Les système sont les même pour OSR, mais l'ordre des axes est différent
        return (point[1], point[0])

    # Systèmes différents
    ct = osr.CreateCoordinateTransformation(sr_src, sr_dst)
    x_dst, y_dst, z_dst = ct.TransformPoint(point[0], point[1])

    return (x_dst, y_dst)