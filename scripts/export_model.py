"""Exporte le modèle `credit-scoring@champion` du registry MLflow vers `artefacts/`.

## Pourquoi exporter plutôt que servir depuis MLflow

En production, l'API n'a besoin que de trois choses : le modèle, son seuil de décision et le
contrat d'entrée (colonnes et types). Faire tourner un serveur MLflow à côté de l'API ajouterait
un service à maintenir, une base à sauvegarder et une dépendance lourde dans l'image, pour lire
un fichier de 3 Mo une seule fois au démarrage.

Ce que l'export fait perdre, c'est la traçabilité : un fichier posé dans un dossier ne dit pas
d'où il vient. `manifest.json` la rend. Il recopie depuis le registry la version, le run
d'origine, le seuil, les métriques et la signature, et il ajoute l'empreinte SHA-256 du fichier :
l'API refuse de démarrer si le modèle ne correspond pas à son manifest.

## Pourquoi le format skops

Le modèle est conservé dans le format où la mission 5 l'a journalisé, `skops`, plutôt que
converti en `pickle`/`joblib`. Charger un pickle exécute du code arbitraire ; skops ne
reconstruit que les types déclarés comme sûrs, listés dans le manifest.

## Lancement

Le script lit le registry de la mission 5, donc il tourne dans l'environnement de la mission 5
(qui a MLflow) ; l'API, elle, n'aura pas MLflow :

    uv run --project "../../5-Initiez-vous au MLOps Partie 1" python scripts/export_model.py

Le registry est lu directement dans sa base SQLite : pas besoin de lancer le serveur MLflow.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import lightgbm
import mlflow
import sklearn
import skops
import yaml

RACINE = Path(__file__).resolve().parents[1]
MISSION5 = RACINE.parents[1] / "5-Initiez-vous au MLOps Partie 1"
NOM = "credit-scoring"
ALIAS = "champion"
TAG_SEUIL = "seuil_decision"


def sha256(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def exporter(tracking_uri: str, sortie: Path) -> dict:
    mlflow.set_tracking_uri(tracking_uri)
    client = mlflow.MlflowClient()
    version = client.get_model_version_by_alias(NOM, ALIAS)
    if TAG_SEUIL not in version.tags:
        raise RuntimeError(f"la version {version.version} n'a pas de tag « {TAG_SEUIL} »")

    with tempfile.TemporaryDirectory() as tmp:
        local = Path(mlflow.artifacts.download_artifacts(
            artifact_uri=f"models:/{NOM}@{ALIAS}", dst_path=tmp))
        mlmodel = yaml.safe_load((local / "MLmodel").read_text())
        fichier = local / mlmodel["flavors"]["sklearn"]["pickled_model"]
        sortie.mkdir(parents=True, exist_ok=True)
        cible = sortie / "model.skops"
        shutil.copyfile(fichier, cible)

    info = mlflow.models.get_model_info(f"models:/{NOM}@{ALIAS}")
    entrees = info.signature.inputs.to_dict()

    manifest = {
        "nom": NOM,
        "alias": ALIAS,
        "version": int(version.version),
        "run_id": version.run_id,
        "model_id": mlmodel.get("model_id"),
        "seuil_decision": float(version.tags[TAG_SEUIL]),
        "metriques": {
            "cout_par_client": float(version.tags["cout_par_client"]),
            "auc": float(version.tags["auc"]),
        },
        "entrainement": {
            "n_lignes": int(version.tags["n_lignes_entrainement"]),
            "version_features": version.tags["version_features"],
            "famille": version.tags["famille"],
        },
        "fichier": {"nom": cible.name, "sha256": sha256(cible), "octets": cible.stat().st_size},
        "skops_trusted_types": mlmodel["flavors"]["sklearn"]["skops_trusted_types"],
        "versions": {
            "python": mlmodel["flavors"]["python_function"]["python_version"],
            "scikit-learn": sklearn.__version__,
            "lightgbm": lightgbm.__version__,
            "skops": skops.__version__,
            "mlflow": mlflow.__version__,
        },
        # Le contrat d'entrée tel que le registry l'a enregistré : nom et type de chaque colonne,
        # dans l'ordre. L'API construit son schéma de validation à partir de cette liste.
        "entrees": [{"nom": c["name"], "type": c["type"]} for c in entrees],
        "exporte_le": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    (sortie / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tracking-uri", default=f"sqlite:///{MISSION5 / 'mlflow.db'}")
    parser.add_argument("--sortie", type=Path, default=RACINE / "artefacts")
    args = parser.parse_args()
    m = exporter(args.tracking_uri, args.sortie)
    print(f"{m['nom']} v{m['version']} exporté · seuil {m['seuil_decision']} · "
          f"{len(m['entrees'])} entrées · {m['fichier']['octets'] / 1e6:.1f} Mo · "
          f"sha256 {m['fichier']['sha256'][:12]}…")


if __name__ == "__main__":
    main()
