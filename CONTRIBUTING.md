# Directives de contribution

Tout d'abord, merci d'envisager de contribuer à ce projet !

Il s'agit principalement de lignes directrices, et non de règles. Faites preuve de discernement, et n'hésitez pas à proposer des modifications à ce document dans une pull request.

## Git hooks

Nous utilisons les git hooks via [pre-commit](https://pre-commit.com/) pour appliquer et vérifier automatiquement certaines "règles". Veuillez l'installer avant de pousser un commit.

Voir le fichier de configuration correspondant : `.pre-commit-config.yaml`.

## Style de code

Assurez-vous que votre code suit à peu près la PEP-8 [PEP-8](https://www.python.org/dev/peps/pep-0008/) et reste cohérent avec le reste du code :

- formatage: [black](https://black.readthedocs.io/) est utilisé pour formater automatiquement le code sans débat.
- tri des imports: [isort](https://pycqa.github.io/isort/) est utilisé pour trier les imports.
- analyse statique: [flake8](https://flake8.pycqa.org/en/latest/) est utilisé pour identifier les écarts vis à vis de PEP-8 et maintenir un code source de qualité.

## Branches

### Branches spéciales

- `master`: la branche principale.
