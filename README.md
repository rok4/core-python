# Librairies CORE Python

Ces librairies Python sont utilisées par les outils python du dépôt [pytools](https://github.com/rok4/pytools)

## Compiler la librairie

`VERSION=1.0.0 python setup.py bdist_wheel`

## Installer la librairie

```sh
apt install python3-rados python3-gdal
python -m venv --system-site-packages venv
source venv/bin/activate
pip install rok4lib-1.0.0-py3-none-any.whl
```

## Jouer les tests unitaires

`pytest`

Pour avoir la couverture des tests unitaires :
```sh
source venv/bin/activate
pip install coverage
coverage run -m pytest
coverage report -m
```

## Utiliser la librairie

```python
from rok4.TileMatrixSet import TileMatrixSet

try:
    tms = TileMatrixSet("file:///path/to/tms.json")
except Exception as exc:
    print(exc)
```

## Compiler la documentation

```bash
source venv/bin/activate
pip install pdoc3 
VERSION=1.0.0 pdoc --html rok4
```