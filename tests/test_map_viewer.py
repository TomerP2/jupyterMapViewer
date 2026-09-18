import ipyleaflet
from jupyterMapViewer import map_viewer


def test_map_viewer_vector(geojson_file):
    result = map_viewer(geojson_file)
    assert isinstance(result, ipyleaflet.Map)


def test_map_viewer_raster(tiff_file):
    result = map_viewer(tiff_file)
    assert isinstance(result, ipyleaflet.Map)
