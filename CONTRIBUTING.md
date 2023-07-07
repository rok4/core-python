# Directives de contribution

Merci d'envisager de contribuer à ce projet !

## Git hooks

Nous utilisons les git hooks via [pre-commit](https://pre-commit.com/) pour appliquer et vérifier automatiquement certaines "règles". Veuillez l'installer avant de pousser un commit.

Voir le fichier de configuration correspondant : `.pre-commit-config.yaml`.

## Changelog

Pour éviter les conflits d'édition du changelog en cas de multiples contributions parallèles, n'éditez pas directement le fichier `CHANGELOG.md` sur votre branche de travail.

A la place, indiquez en description ou commentaire de votre pull request, bien en évidence, le changelog qui concerne spécifiquement cette PR, avec le même formalisme que le fichier `CHANGELOG.md`.

Lors de la release de la prochaine version, le mainteneur ajoutera vos notes de modifications dans le fichier `CHANGELOG.md` ce fichier dans le même temps, avec deux objectifs :

* la date de modification sera celle de la fusion de branches.
* le contenu pourra tenir compte de toutes les modifications depuis la dernière release.

Le formalisme du changelog est le suivant, en markdown :

```md
Résumé des objectifs des modifications apportées

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
