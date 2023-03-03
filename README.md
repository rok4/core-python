# Librairies ROK4 Python

Ces librairies facilitent la manipulation d'entités du projet ROK4 comme les Tile Matrix Sets, les pyramides ou encore les couches, ainsi que la manipulation des stockages associés. Le gestion du projet s'appuie sur l'outil [poetry](https://python-poetry.org/docs/).

## Utiliser la librairie

Installations système requises :

* debian : `apt install python3-rados python3-gdal`

### Installer depuis le fichier wheel en ligne

```sh
pip install https://github.com/rok4/core-python/releases/download/x.y.z/rok4-x.y.z-py3-none-any.whl
# or, with poetry
poetry add https://github.com/rok4/core-python/releases/download/x.y.z/rok4-x.y.z-py3-none-any.whl
```

### Installer depuis le code source

```sh
git clone --branch x.y.z --depth 1 https://github.com/rok4/core-python
cd core-python
poetry config virtualenvs.options.system-site-packages true
poetry self add poetry-bumpversion
poetry version x.y.z
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
# venv in the project directory
poetry config virtualenvs.in-project true
# Install bumpversion poetry plugin
poetry self add poetry-bumpversion
# Change version into pyproject.toml and rok4/__init__.py
poetry version x.y.z
# Install dependencies
apt install python3-rados python3-gdal
poetry install --no-interaction --no-root
# To look for system libraries
# adapt python version to yours
cp site-packages/*.pth .venv/lib/python3.8/site-packages/
# Run unit tests
poetry run coverage run -m pytest
# Get unit tests coverage
poetry run coverage report -m
# Build unit test coverage HTML report
poetry run coverage html -d dist/x.y.z/tests/
# Build wheel and tarball files
poetry build
# Build devs documentation
poetry install -E doc
poetry run pdoc3 --html --output-dir dist/x.y.z/ rok4
```
