# Suivi des étapes / Step tracking

Ce fichier indique, pour chaque étape du [plan](PLAN-V1.md), sur quelle machine elle a été testée et validée.

Légende : ✅ validée · ⏳ test à faire · 🔄 en cours

| Étape | Description | Windows 10 | Fedora 44 | Commit |
|---|---|---|---|---|
| 1 | Poste de travail (Git, uv, Python 3.13) et dépôt GitHub | ✅ 18/10/2026 | ⏳ | `3dab253` |
| 2 | Squelette du projet : LICENSE, README, configuration, premiers tests | 🔄 | ⏳ | — |

Les étapes suivantes seront ajoutées au fur et à mesure.

## Tests Fedora à rattraper

Quand ton PC Fedora 44 sera disponible, ouvre le Terminal et tape :

```bash
sudo dnf install git uv python3.13
mkdir -p ~/ai
cd ~/ai
git clone https://github.com/davidharputoglu/RuneCast.git
cd RuneCast
git --version
uv --version
uv run python --version
uv run pytest
uv run runecast --version
```

Si le dossier `~/ai/RuneCast` existe déjà, remplace les lignes `mkdir`, `cd ~/ai` et `git clone` par :

```bash
cd ~/ai/RuneCast
git pull
```

Résultat attendu :

- **Étape 1** : `uv run python --version` affiche Python 3.13.x.
- **Étape 2** : `uv run pytest` se termine en vert par « passed », sans « failed » ; `uv run runecast --version` affiche « Créé par HARPUTOGLU David, aidé par l'IA ».
