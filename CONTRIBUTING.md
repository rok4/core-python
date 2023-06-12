# Directives de contribution

Tout d'abord, merci d'envisager de contribuer à ce projet !

Il s'agit principalement de lignes directrices, et non de règles. Faites preuve de discernement, et n'hésitez pas à proposer des modifications à ce document dans une pull request.

## Git hooks

Nous utilisons les git hooks via [pre-commit](https://pre-commit.com/) pour appliquer et vérifier automatiquement certaines "règles". Veuillez l'installer avant de pousser un commit.

Voir le fichier de configuration correspondant : `.pre-commit-config.yaml`.

## CHANGELOG

Pour éviter les conflits d'édition du changelog en cas de multiples contributions parallèles, n'éditez pas directement le fichier `CHANGELOG.md` sur votre branche de travail.
A la place, indiquez en description ou commentaire de votre pull request, bien en évidence, le changelog qui concerne spécifiquement cette PR, avec le même formalisme que le fichier `CHANGELOG.md`.
Le mainteneur qui validera la PR éditera alors ce fichier dans le même temps, avec deux objectifs :

* la date de modification sera celle de la fusion de branches.
* le contenu pourra tenir compte de toutes les modifications depuis la dernière release.

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
