# Directives de contribution

Merci d'envisager de contribuer à ce projet !

## Git hooks

Nous utilisons les git hooks via [pre-commit](https://pre-commit.com/) pour appliquer et vérifier automatiquement certaines "règles". Veuillez l'installer avant de pousser un commit.

Voir le fichier de configuration correspondant : `.pre-commit-config.yaml`.

## Pull request

Le titre de la PR est utilisé pour constituer automatiquement les notes de release. Vous pouvez préciser en commentaire de votre PR des détails qui seront ajoutés dans le fichier `CHANGELOG.md` par les mainteneurs du projet.

Le formalisme du changelog est le suivant, en markdown :

```md
### [Added]

Liste de nouvelles fonctionnalités.

### [Changed]

Liste de fonctionnalités existantes modifiées.

### [Deprecated]

Liste de fonctionnalités dépréciées.

### [Removed]

Liste de foncitonnalités retirées.

### [Fixed]

Liste de corrections fonctionnelles.

### [Security]

Liste de corrections de sécurité.
```

Les parties vides, sans élément à lister, peuvent être ignorées.
