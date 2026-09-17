# jupyterMapViewer

A python package that uses ipyleaflet enable jupyter notebook users to quicklky visualize their geodata using an interactive map. Similar to R's [MapView](https://r-spatial.github.io/mapview/). 

# Usage (example notebook cell)
```python
from jupyterMapViewer import map_viewer

example_data = 'data/vector.shp'

map_viewer(example_data)
```
*Code creates interactive map

# Features
 - Supports vector and raster data (.shp, .gpkg, .tif)
 - Supports displaying multiple layers simultaneously
 - Supports different basemaps: OSM, Satellite