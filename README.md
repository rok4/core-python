# Librairies ROK4 Python

Ces librairies Python sont utilisées par les outils python du dépôt [pytools](https://github.com/rok4/pytools). Le gestion du projet s'appuie sur l'outil [poetry](https://python-poetry.org/docs/).

## Utiliser la librairie

Installations système requises :

* debian : `apt install python3-rados python3-gdal`

### Installer depuis le fichier wheel en ligne

Exemple avec la version 1.2.0 :

```sh
pip install https://github.com/rok4/core-python/releases/download/1.2.0/rok4-1.2.0-py3-none-any.whl
# or, with poetry
poetry add https://github.com/rok4/core-python/releases/download/1.2.0/rok4-1.2.0-py3-none-any.whl
```

### Installer depuis le code source

Exemple avec la version 1.2.0 :

```sh
git clone --branch 1.2.0 --depth 1 https://github.com/rok4/core-python
cd core-python
poetry config virtualenvs.options.system-site-packages true
poetry self add poetry-bumpversion
poetry version 1.2.0
poetry install --without=dev
```

### Appels dans le code python

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


## Compiler la librairie

La compilation s'appuie sur l'outil poetry :

```sh
# To detect rados and osgeo libraries, we enable system-site-packages
poetry config virtualenvs.options.system-site-packages true
# Install bumpversion poetry plugin
poetry self add poetry-bumpversion
# Change version into pyproject.toml and rok4/__init__.py
poetry version 1.2.0
# Install dependencies
apt install python3-rados python3-gdal
poetry install --no-interaction --no-root
# Run unit tests
poetry run coverage run -m pytest
# Get unit tests coverage
poetry run coverage report -m
# Build unit test coverage HTML report
poetry run coverage html -d dist/${{ github.ref_name }}/tests/
# Build wheel and tarball files
poetry build
# Build devs documentation
poetry install -E doc
poetry run pdoc3 --html --output-dir dist/1.2.0/ rok4
```
