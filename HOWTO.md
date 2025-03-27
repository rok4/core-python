
# Cas d'usage simple : exemple avec des données ALTI
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

# Cas d'usage simple avec le TileMatrixSet "PM": bucket de stockage : ```s3://tilematrixsets/PM.json```

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
      {},..
}
```

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