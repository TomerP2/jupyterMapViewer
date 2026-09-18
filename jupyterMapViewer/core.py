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


def map_viewer(data, height='500px'):
    if isinstance(data, list):
        return _multi_map(data, height)
    ext = Path(data).suffix.lower()
    if ext in _RASTER_EXTS:
        return _raster_map(data, height)
    return _vector_map(data, height)


def _raster_map(path, height):
    layer, bounds = _raster_layer_and_bounds(path)
    m = _base_map(*bounds, height)
    m.add_layer(layer)
    return m


def _vector_map(path, height):
    gdf, bounds = _vector_gdf_and_bounds(path)
    m = _base_map(*bounds, height)
    m.add_layer(_vector_layer(gdf, m))
    return m


def _multi_map(paths, height):
    items = []
    for path in paths:
        if Path(path).suffix.lower() in _RASTER_EXTS:
            items.append(_raster_layer_and_bounds(path))
        else:
            items.append(_vector_gdf_and_bounds(path))

    all_bounds = [bounds for _, bounds in items]
    union = (
        min(b[0] for b in all_bounds),
        min(b[1] for b in all_bounds),
        max(b[2] for b in all_bounds),
        max(b[3] for b in all_bounds),
    )
    m = _base_map(*union, height)

    for data, _ in items:
        if isinstance(data, gpd.GeoDataFrame):
            m.add_layer(_vector_layer(data, m))
        else:
            m.add_layer(data)

    return m


def _raster_layer_and_bounds(path):
    abs_path = Path(path).resolve().as_posix()
    client = localtileserver.TileClient(abs_path, host='127.0.0.1')
    # Build TileLayer manually to skip the metadata validation request,
    # which fails when nodata=nan (NaN is not valid JSON).
    layer = ipyleaflet.TileLayer(url=client.get_tile_url(), name=Path(path).name)
    with rasterio.open(abs_path) as src:
        bounds = transform_bounds(src.crs, _WGS84, *src.bounds)
    return layer, bounds


def _vector_gdf_and_bounds(path):
    gdf = gpd.read_file(path).to_crs(epsg=4326)
    b = gdf.total_bounds  # minx, miny, maxx, maxy
    return gdf, (b[0], b[1], b[2], b[3])


def _base_map(west, south, east, north, height):
    return ipyleaflet.Map(
        center=((south + north) / 2, (west + east) / 2),
        zoom=_zoom_for_bounds(west, south, east, north),
        scroll_wheel_zoom=True,
        layout=Layout(height=height),
    )


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


def _zoom_for_bounds(minx, miny, maxx, maxy):
    span = max(maxy - miny, maxx - minx)
    if span <= 0:
        return 14
    return max(1, min(math.floor(math.log2(360 / span)), 18))


def _feature_center(feature):
    geom = shapely_shape(feature['geometry'])
    c = geom.centroid
    return [c.y, c.x]
