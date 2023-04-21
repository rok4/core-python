# Librairies ROK4 Python

![ROK4 Logo](https://rok4.github.io/assets/images/rok4.png)

Ces librairies facilitent la manipulation d'entités du projet ROK4 comme les Tile Matrix Sets, les pyramides ou encore les couches, ainsi que la manipulation des stockages associés.

- [Installer la librairie](#installer-la-librairie)
- [Utiliser la librairie](#utiliser-la-librairie)
- [Compiler la librairie](#compiler-la-librairie)
- [Publier la librairie sur Pypi](#publier-la-librairie-sur-pypi)

## Installer la librairie

Installations système requises :

- debian : `apt install python3-rados python3-gdal`

Depuis [PyPI](https://pypi.org/project/rok4/) : `pip install rok4`
Depuis [GitHub](https://github.com/rok4/core-python/releases/) : `pip install https://github.com/rok4/core-python/releases/download/x.y.z/rok4-x.y.z-py3-none-any.whl`

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

## Contribuer

- Installer les dépendances de développement :

    ```sh
    python3 -m pip install -e[dev]
    ```

- Consulter les [directives de contribution](./CONTRIBUTING.md)

## Compiler la librairie

```sh
apt install python3-venv
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade build bump2version
bump2version --allow-dirty --current-version 0.0.0 --new-version x.y.z patch pyproject.toml src/rok4/__init__.py

# Run unit tests
pip install -e .[test]
# To use system installed modules rados and osgeo
echo "/usr/lib/python3/dist-packages/" >.venv/lib/python3.10/site-packages/system.pth
python -c 'import sys; print (sys.path)'
# Run tests
coverage run -m pytest
# Get tests report and generate site
coverage report -m
coverage html -d dist/tests/

# Build documentation
pip install -e .[doc]
pdoc3 --html --output-dir dist/ rok4

# Build artefacts
python3 -m build
```

## Publier la librairie sur Pypi

Configurer le fichier `$HOME/.pypirc` avec les accès à votre compte PyPI.

```sh
python3 -m pip install --upgrade twine
python3 -m twine upload --repository pypi dist/rok4-x.y.z-py3-none-any.whl dist/rok4-x.y.z.tar.gz
```
