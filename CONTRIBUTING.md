# Directives de contribution

Merci d'envisager de contribuer à ce projet !

## Git hooks

Nous utilisons les git hooks via [pre-commit](https://pre-commit.com/) pour appliquer et vérifier automatiquement certaines "règles". Veuillez l'installer avant de pousser un commit.

Voir le fichier de configuration correspondant : `.pre-commit-config.yaml`.

## Pull request

Complétez le fichier `CHANGELOG.md`, dans la partie `[Unreleased]`, en précisant les modifications fonctionnelles apportées. Celles ci seront utilisées pour rédiger le message de release sur GitHub. Le format est basé sur [Keep a Changelog](https://keepachangelog.com/). Les sections sont les suivantes :

```md
### Added

Liste de nouvelles fonctionnalités.

### Changed

Liste de fonctionnalités existantes modifiées.

### Deprecated

Liste de fonctionnalités dépréciées.

### Removed

Liste de foncitonnalités retirées.

### Fixed

Liste de corrections fonctionnelles.

### Security

Liste de corrections de sécurité.
```

Les parties vides, sans élément à lister, peuvent être ignorées.
