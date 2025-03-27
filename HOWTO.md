
## Cas d'usage simple : exemple avec des données ALTI

*   ci-dessous les résultats obtenus avec l'exemple des données ALTI :

```sh
myusername@pcname:~$ python3 data_tilesmatrix_launcher.py
créer une pyramide à partir du path de son descriptor RASTER pyramid 'ALTI' (S3 storage)
type de pyramide PyramidType.RASTER
format des tuiles de données vecteur : TIFF_ZIP_FLOAT32
niveau le plus bas de la pyramide : RASTER pyramid's level '13' (S3 storage)
niveau le plus haut de la pyramide : RASTER pyramid's level '0' (S3 storage)
données du slab:

 type de slab SlabType.DATA
 identifiant du niveau 10
 nombre de tuiles en largeur par slab 21
 nombre de tuiles en hauteur par slab : 29
 ```

## Comment l'obtenir ?

```py
    #!/usr/bin/env python3

    # import des packages de rok4
    from rok4.enums import PyramidType, SlabType, StorageType, ColorFormat
    from rok4.pyramid import Pyramid, Level

    # chemin du descriptor de la pyramide alti
    path_to_pyramid_alti_descriptor = "s3://pyramids/ALTI.json"

    # descriptor de la pyramide ALTI
    pyr_alti_descriptor = Pyramid.from_descriptor(path_to_pyramid_alti_descriptor)

    print (f"créer une pyramide à partir du path de son descriptor {pyr_alti_descriptor}")

    print(f"type de pyramide {pyr_alti_descriptor.type}")
    print(f"format des tuiles de données vecteur : {pyr_alti_descriptor.format}")
    print(f"niveau le plus bas de la pyramide : {pyr_alti_descriptor.bottom_level}")
    print(f"niveau le plus haut de la pyramide : {pyr_alti_descriptor.top_level}")

    slab_type, level, column, row = pyr_alti_descriptor.get_infos_from_slab_path(slab_alti_path)
    slab_indexes = pyr_alti_descriptor.get_infos_from_slab_path(slab_alti_path)

    print ("données du slab: \n")
    print (f" type de slab {slab_indexes[0]}")
    print (f" identifiant du niveau {slab_indexes[1]}")
    print (f" nombre de tuiles en largeur par slab {slab_indexes[2]}")
    print (f" nombre de tuiles en hauteur par slab : {slab_indexes[3]}")
    level, col, row, pcol, prow = pyr_alti_descriptor.get_tile_indices(16, 16, "0", srs = "IGNF:LAMB93")
    data_raster = pyr_alti_descriptor.get_tile_data_raster(level, col, row)

    print(data_raster)
 ```

## Cas d'usage simple avec le TileMatrixSet "PM":

emplacement du bucket de stockage : ```s3://tilematrixsets/PM.json```

voici une partie de sa structure en objet json pour le tms ```PM```:

```json
{
   "tileMatrices" : [
      {
         "id" : "0",
         "tileWidth" : 256,
         "scaleDenominator" : 559082264.028718,
         "matrixWidth" : 1,
         "cellSize" : 156543.033928041,
         "matrixHeight" : 1,
         "tileHeight" : 256,
         "pointOfOrigin" : [
            -20037508.3427892,
            20037508.3427892
         ]
      },
      {
         "matrixHeight" : 2,
         "pointOfOrigin" : [
            -20037508.3427892,
            20037508.3427892
         ],
         "tileHeight" : 256,
         "cellSize" : 78271.5169640205,
         "scaleDenominator" : 279541132.014359,
         "matrixWidth" : 2,
         "tileWidth" : 256,
         "id" : "1"
      },
      {
         "cellSize" : 39135.7584820102,
         "pointOfOrigin" : [
            -20037508.3427892,
            20037508.3427892
         ],
         "tileHeight" : 256,
         "matrixHeight" : 4,
         "tileWidth" : 256,
         "matrixWidth" : 4,
         "scaleDenominator" : 139770566.007179,
         "id" : "2"
      },{},{},...
}
```

## Exploitation des données d'un fichier JSON d'un tilematrixset exemple : PM.json

```py
#!/usr/bin/env python3
import json
# import des packages de rok4
from rok4.enums import PyramidType, SlabType, StorageType, ColorFormat
from rok4.tile_matrix_set import TileMatrix, TileMatrixSet
try:
    tms = TileMatrixSet("PM")
    print ("\nExploitation de la classe TileMatrixSet\n")
    print(f"le nom du tms est le suivant : {tms.name}")
    print(f"le nom du tms est le suivant : {tms.path}")
    print(f"le code srs associé au système de projection planimétrique est le suivant : {tms.srs}")

    typePyramid = PyramidType("RASTER")
    slabType = SlabType("MASK")
    storageType = StorageType("s3://")

    print (f"type de pyramide : {typePyramid}")
    print (f"type de slab : {slabType}")
    print (f"type de stockage : {storageType}")

    # Ouverture d'un fichier JSON d'un tilematrixset
    print ("\nOuverture d'un fichier JSON d'un tilematrixset\n")

    with open("s3://tilematrixsets/PM.json") as json_file:
        data = json.load(json_file)
        print(f"type de structure de données de data : {type(data)}")
        print(f'nom de la pyramide : {data["id"]}')
        print(f'code srs projection planimétrique : {data["crs"]}')
        print(f'nombre de tuiles de la pyramide : {len(data["tileMatrices"])}')
        print(f'coordonnées du point origine : {data["tileMatrices"][0]["pointOfOrigin"]}')
        print(f'taille de la cellule : {data["tileMatrices"][0]["cellSize"]}')
        print(f'nombre d"éléments de la matrices de tuiles cad le nombre de tuiles : {len(data["tileMatrices"])}')

except Exception as exc :
    print (exc)
```

## Descripteur de couches des "layers" => exemple pour la BDORTHO : ```s3://layers/bdortho.json```

```list.txt``` contient tous les noms des buckets de stockage des listes sous forme d'une liste :

```txt
s3://layers/bdortho.json
s3://layers/alti.json
s3://layers/limadm.json
s3://layers/pente.json
s3://layers/bdparcellaire.json
```

*   Ci-jointe sa structure en objet json :

```json
{
    "title": "Photographies aériennes",
    "abstract": "Données BD Ortho",
    "keywords":
    [
        "Ortho-photographies",
        "Données RGB"
    ],
    "pyramids":
    [
        {
            "bottom_level": "15",
            "top_level": "0",
            "path": "s3://pyramids/BDORTHO.json"
        }
    ],
    "resampling": "bicubic",
    "styles":
    [
        "normal"
    ],
    "extra_crs":
    [
        "EPSG:4559"
    ],
    "extra_tilematrixsets":
    [
        "4326",
        "UTM20W84MART_2.5m"
    ],
    "wms":
    {
        "enabled": true
    },
    "wmts":
    {
        "enabled": true
    },
    "tms":
    {
        "enabled": true
    },
    "tiles":
    {
        "enabled": true
    }
}
```