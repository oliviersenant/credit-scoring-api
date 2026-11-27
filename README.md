# credit-scoring-api

Mise en production du modèle de scoring crédit de « Prêt à Dépenser » : une API qui reçoit le
dossier d'un client et rend une probabilité de défaut et une décision. Le projet couvre aussi la
conteneurisation, le pipeline CI/CD, le stockage des données de production, le suivi du data
drift et l'optimisation du temps d'inférence.

> Projet en construction. Cette page sera complétée à chaque étape.

## Le modèle servi

| | |
|---|---|
| Modèle | `credit-scoring` v3 (LightGBM), exporté du model registry MLflow |
| Entraînement | 307 511 clients, 447 variables (données Home Credit) |
| Coût métier | 0,4985 par client (un faux négatif coûte 10 faux positifs) |
| AUC | 0,7806 |
| Seuil de décision | **0,08** : au-dessus, le crédit est refusé |

Le modèle rend une **probabilité**, la décision naît du **seuil**. Les deux voyagent ensemble :
`artefacts/manifest.json` porte le seuil, la provenance du modèle (version, run d'origine),
son contrat d'entrée et l'empreinte SHA-256 du fichier.

### Points de vigilance sur le modèle

- **Variables protégées.** `CODE_GENDER` est la 4ᵉ variable la plus importante du modèle, l'âge
  la 7ᵉ et la situation familiale la 9ᵉ. Un usage réel demanderait un audit d'équité et,
  probablement, leur retrait.
- **Dépendance à des scores externes.** 41,8 % de l'importance du modèle repose sur les
  variables `EXT_SOURCE_*`, des scores fournis par des tiers. Une dérive de leur côté se
  répercute directement sur nos décisions : ce sont les premières variables surveillées.
- **Prétraitement hors du modèle.** `DAYS_EMPLOYED = 365243` signifie « sans emploi ». L'API
  le convertit en valeur manquante et calcule elle-même le drapeau associé, selon la règle
  écrite dans le manifest. Les appelants envoient les données brutes.

## Structure

```
scoring/      logique métier (chargement du modèle, validation, prédiction), sans FastAPI
app/          API FastAPI
monitoring/   tableau de bord de suivi
scripts/      export du modèle, simulation de trafic, bancs d'essai
notebooks/    analyse du data drift, optimisation
artefacts/    modèle exporté + manifest
tests/        tests automatisés
deploy/       configuration de déploiement
docs/         documentation
```

## Contribuer

`main` est la production : chaque push dessus déploie l'API. Tout changement passe par une
branche et une Pull Request. Conventions de branches, de commits et de versions :
[CONTRIBUTING.md](CONTRIBUTING.md).

## Données

Les données Home Credit ne sont pas versionnées : la licence de la compétition Kaggle n'en
autorise pas la redistribution. Les tests tournent sur des données synthétiques.

## Réexporter le modèle

Depuis l'environnement du projet d'entraînement, qui contient le registry MLflow :

```bash
uv run --project "../../5-Initiez-vous au MLOps Partie 1" python scripts/export_model.py
```
