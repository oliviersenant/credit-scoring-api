# Conventions de contribution

## Principe : `main` est la production

Chaque push sur `main` lance le pipeline complet : tests, construction de l'image, publication
sur GHCR, déploiement sur `scoring.senant.dev`, puis smoke test. `main` doit donc toujours être
déployable. On ne pousse jamais directement dessus : tout changement passe par une branche, puis
par une Pull Request dont les tests sont verts.

```
git switch -c feat/xxx   →   commits   →   git push -u origin feat/xxx
        →   Pull Request (tests en CI)   →   merge dans main   →   déploiement
```

`main` est protégée sur GitHub : PR obligatoire, CI verte obligatoire avant le merge.

## Branches

| Préfixe | Usage | Exemple |
|---|---|---|
| `feat/` | nouvelle fonctionnalité | `feat/api-predict` |
| `fix/` | correction de bug | `fix/sentinelle-days-employed` |
| `perf/` | optimisation mesurée | `perf/onnx-runtime` |
| `test/` | ajout ou correction de tests | `test/cas-critiques` |
| `ci/` | pipeline CI/CD | `ci/deploiement-vps` |
| `docs/` | documentation | `docs/monitoring` |
| `chore/` | maintenance, dépendances | `chore/bump-fastapi` |

Une branche = un sujet. Elle vit le temps d'une PR, puis elle est supprimée.

## Messages de commit

[Conventional Commits](https://www.conventionalcommits.org/fr/), à l'indicatif présent,
en français : `<type>(<portée optionnelle>): <quoi>`.

```
feat(api): POST /predict valide les 446 variables brutes
fix(scoring): applique la sentinelle avant predict_proba
perf: inférence via ONNX Runtime (p95 divisé par 3)
```

Types : `feat`, `fix`, `perf`, `test`, `ci`, `docs`, `refactor`, `chore`.
Le corps du commit explique **pourquoi**, quand ce n'est pas évident.

## Versions

Versionnage sémantique `vMAJEUR.MINEUR.CORRECTIF`, posé sur `main` à la fin de chaque étape
(`git tag -a v0.2.0 -m "API, Docker, CI/CD"`). Le tag ne déclenche rien : il marque un état
stable vers lequel revenir.

Chaque image publiée porte le SHA du commit, ce qui relie une réponse de l'API au code qui l'a
produite. La version du modèle (`model_version`) est indépendante : elle vient du manifest.

## Revenir en arrière

Si un déploiement casse la production, on annule le commit fautif par une PR
(`git revert <sha>`) : le pipeline redéploie l'état précédent, et l'historique garde la trace
de l'incident.

## Étapes de la mission et branches

| Étape | Branche | Tag |
|---|---|---|
| 0. Export du modèle | `main` (amorçage du dépôt) | |
| 1. Conventions du dépôt | `docs/conventions` | `v0.1.0` |
| 2. API, Docker, CI/CD | `feat/api`, `test/cas-critiques`, `ci/deploiement-vps` | `v0.2.0` |
| 3. Stockage et drift | `feat/stockage-production`, `feat/drift`, `feat/dashboard` | `v0.3.0` |
| 4. Optimisation | `perf/profilage`, `perf/onnx-runtime` | `v1.0.0` |
