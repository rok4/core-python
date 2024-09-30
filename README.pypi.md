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
from rok4.tile_matrix_set import TileMatrixSet

try:
    tms = TileMatrixSet("file:///path/to/tms.json")
except Exception as exc:
    print(exc)
```

Following environment variables could be used, by module :

* `storage` : more details in the module developer documentation
    * `ROK4_READING_LRU_CACHE_SIZE` : Cache size (0 for no limit)
    * `ROK4_READING_LRU_CACHE_TTL` : Cache validity time (0 for no limit)
    * `ROK4_CEPH_CONFFILE` : Ceph configuration file
    * `ROK4_CEPH_USERNAME` : Ceph cluster user
    * `ROK4_CEPH_CLUSTERNAME` : Ceph cluster name
    * `ROK4_S3_KEY` : Key(s) for S3 server(s)
    * `ROK4_S3_SECRETKEY` : Secret key(s) for S3 server(s)
    * `ROK4_S3_URL` : URL(s) for S3 server(s)
    * `ROK4_SSL_NO_VERIFY` : Disable SSL conrols for S3 access (any non empty value)
* `tile_matrix_set` :
    * `ROK4_TMS_DIRECTORY` : Root directory (file or object) for tile matrix sets
* `style` :
    * `ROK4_STYLES_DIRECTORY` : Root directory (file or object) for styles

More examples in the developer documentation
