import numpy as np
import pytest
import geopandas as gpd
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS
from shapely.geometry import Point


@pytest.fixture
def geojson_file(tmp_path):
    gdf = gpd.GeoDataFrame(
        {'name': ['A', 'B'], 'value': [1, 2]},
        geometry=[Point(0, 0), Point(1, 1)],
        crs='EPSG:4326',
    )
    path = tmp_path / 'test.geojson'
    gdf.to_file(path, driver='GeoJSON')
    return str(path)


@pytest.fixture
def tiff_file(tmp_path):
    path = tmp_path / 'test.tif'
    data = np.ones((10, 10), dtype=np.float32)
    transform = from_bounds(10.0, 20.0, 11.0, 21.0, 10, 10)
    with rasterio.open(
        path, 'w',
        driver='GTiff',
        height=10, width=10,
        count=1,
        dtype=np.float32,
        crs=CRS.from_epsg(4326),
        transform=transform,
    ) as dst:
        dst.write(data, 1)
    return str(path)
