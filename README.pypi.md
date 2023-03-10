# ROK4 Python libraries

![ROK4 Logo](https://rok4.github.io/assets/images/rok4.png)

The `rok4` package help to use [ROK4 project](https://rok4.github.io/) concepts, like Tile Matrix Sets, data pyramids or layers.

## Installation

Required system packages :
* debian : `apt install python3-rados python3-gdal`

The `rok4` package is available on :
* [PyPI](https://pypi.org/project/rok4/) : `pip install rok4`
* [GitHub](https://github.com/rok4/core-python/releases/) : `pip install https://github.com/rok4/core-python/releases/download/<version>/rok4-<version>-py3-none-any.whl`

## Usage

```python
from rok4.TileMatrixSet import TileMatrixSet
from rok4.Vector import Vector

try:
    tms = TileMatrixSet("file:///path/to/tms.json")
    vector = Vector("file:///path/to/vector.shp")
    vector_csv1 = Vector("file:///path/to/vector.csv", delimiter, column_x, column_y)
    vector_csv1 = Vector("file:///path/to/vector.csv", delimiter, column_WKT)
except Exception as exc:
    print(exc)
```