# Librairies CORE Python

Ces librairies Python sont utilisées par les outils python du dépôt [pytools](https://github.com/rok4/pytools)

## Compiler la librairie

`VERSION=1.0.0 python3 setup.py bdist_wheel`

## Installer la librairie

```sh
apt install python3-rados python3-venv python3-pytest
python3 -m venv --system-site-packages venv
source venv/bin/activate
python3 -m pip install dist/rok4lib-1.0.0-py3-none-any.whl
```

## Jouer les tests unitaires

`python3 -m pytest`

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
python3 -m pip install pdoc3 
VERSION=1.0.0 pdoc --html rok4
```