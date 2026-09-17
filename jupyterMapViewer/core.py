import json
import math

import geopandas as gpd
import ipyleaflet
from ipywidgets import HTML, Layout
from shapely.geometry import shape as shapely_shape


def _zoom_for_bounds(minx, miny, maxx, maxy):
    lat_span = maxy - miny
    lon_span = maxx - minx
    span = max(lat_span, lon_span)
    if span <= 0:
        return 14
    zoom = math.floor(math.log2(360 / span))
    return max(1, min(zoom, 18))


def _feature_center(feature):
    geom = shapely_shape(feature['geometry'])
    c = geom.centroid
    return [c.y, c.x]


def map_viewer(data, height='500px'):
    """Display geodata on an interactive ipyleaflet map.

    Parameters
    ----------
    data : str or pathlib.Path
        Path to a vector file (.shp, .gpkg).

    Returns
    -------
    ipyleaflet.Map
    """
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
    m.add_layer(geo_layer)

    return m
