import json
import math
from pathlib import Path

import geopandas as gpd
import ipyleaflet
import localtileserver
import rasterio
from ipywidgets import HTML, Layout
from rasterio.crs import CRS as RasterioCRS
from rasterio.warp import transform_bounds
from shapely.geometry import shape as shapely_shape

_WGS84 = RasterioCRS.from_epsg(4326)

_VECTOR_EXTS = {'.shp', '.gpkg', '.geojson', '.json'}
_RASTER_EXTS = {'.tif', '.tiff'}


def _zoom_for_bounds(minx, miny, maxx, maxy):
    span = max(maxy - miny, maxx - minx)
    if span <= 0:
        return 14
    return max(1, min(math.floor(math.log2(360 / span)), 18))


def _feature_center(feature):
    geom = shapely_shape(feature['geometry'])
    c = geom.centroid
    return [c.y, c.x]


def _vector_layer(gdf, m):
    geo_layer = ipyleaflet.GeoJSON(
        data=json.loads(gdf.to_json(default=str)),
        point_style={
            'radius': 5,
            'color': 'black',
            'fillColor': 'black',
            'fillOpacity': 1.0,
            'weight': 1,
        },
    )

    def on_click(feature=None, **kwargs):
        if not feature:
            return
        props = feature.get('properties', {}) or {}
        rows = ''.join(
            f'<tr><td style="padding:1px 6px"><b>{k}</b></td>'
            f'<td style="padding:1px 6px">{v}</td></tr>'
            for k, v in props.items()
            if v is not None
        )
        for layer in list(m.layers):
            if isinstance(layer, ipyleaflet.Popup):
                m.remove_layer(layer)
        m.add_layer(ipyleaflet.Popup(
            location=_feature_center(feature),
            child=HTML(f'<table style="font-size:12px">{rows}</table>'),
            auto_close=True,
            keep_in_view=True,
        ))

    geo_layer.on_click(on_click)
    return geo_layer


def map_viewer(data, height='500px'):
    """Display geodata on an interactive ipyleaflet map.

    Parameters
    ----------
    data : str or pathlib.Path
        Path to a vector (.shp, .gpkg) or raster (.tif) file.
    height : str
        CSS height of the map widget, e.g. '500px'.

    Returns
    -------
    ipyleaflet.Map
    """
    ext = Path(data).suffix.lower()

    if ext in _RASTER_EXTS:
        abs_path = Path(data).resolve().as_posix()
        client = localtileserver.TileClient(abs_path, host='127.0.0.1')

        # Build TileLayer manually to skip the metadata validation request,
        # which fails when nodata=nan (NaN is not valid JSON).
        tile_url = client.get_tile_url()
        tile_layer = ipyleaflet.TileLayer(url=tile_url, name='Raster')

        with rasterio.open(abs_path) as src:
            west, south, east, north = transform_bounds(src.crs, _WGS84, *src.bounds)
        center_lat = (south + north) / 2
        center_lon = (west + east) / 2
        zoom = _zoom_for_bounds(west, south, east, north)

        m = ipyleaflet.Map(
            center=(center_lat, center_lon),
            zoom=zoom,
            scroll_wheel_zoom=True,
            layout=Layout(height=height),
        )
        m.add_layer(tile_layer)

    else:
        gdf = gpd.read_file(data)
        gdf = gdf.to_crs(epsg=4326)
        bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        zoom = _zoom_for_bounds(*bounds)

        m = ipyleaflet.Map(
            center=(center_lat, center_lon),
            zoom=zoom,
            scroll_wheel_zoom=True,
            layout=Layout(height=height),
        )
        m.add_layer(_vector_layer(gdf, m))

    return m
