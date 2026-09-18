import ipyleaflet
from jupyterMapViewer import map_viewer


def test_map_viewer_vector(geojson_file):
    result = map_viewer(geojson_file)
    assert isinstance(result, ipyleaflet.Map)


def test_map_viewer_raster(tiff_file):
    result = map_viewer(tiff_file)
    assert isinstance(result, ipyleaflet.Map)


def test_map_viewer_list(geojson_file, tiff_file):
    result = map_viewer([geojson_file, tiff_file])
    assert isinstance(result, ipyleaflet.Map)
    # basemap + vector GeoJSON layer + raster TileLayer = at least 3 layers
    assert len(result.layers) >= 3
