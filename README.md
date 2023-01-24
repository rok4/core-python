# Librairies CORE Python

Ces librairies Python sont utilisées par les outils python du dépôt [pytools](https://github.com/rok4/pytools)

## Compiler la librairie

`VERSION=1.0.0 python setup.py bdist_wheel`

## Installer la librairie

```sh
apt install python3-rados python3-gdal python3-venv python3-pytest
python -m venv --system-site-packages venv
source venv/bin/activate
python3 -m pip install dist/rok4lib-1.0.0-py3-none-any.whl
```

## Jouer les tests unitaires

`python3 -m pytest`

Pour avoir la couverture des tests unitaires :
```sh
source venv/bin/activate
python3 -m pip install coverage
coverage run -m pytest
coverage report -m
```

## Utiliser la librairie

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

## Compiler la documentation

```bash
source venv/bin/activate
python3 -m pip install pdoc3 
VERSION=1.0.0 pdoc --html rok4
```
