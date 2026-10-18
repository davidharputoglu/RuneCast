# Suivi des étapes / Step tracking

Ce fichier indique, pour chaque étape du [plan](PLAN-V1.md), sur quelle machine elle a été testée et validée.

Légende : ✅ validée · ⏳ test à faire · 🔄 en cours

| Étape | Description | Version | Windows 10 | Fedora 44 | Commit |
|---|---|---|---|---|---|
| 1 | Poste de travail (Git, uv, Python 3.13) et dépôt GitHub | — | ✅ 18/10/2026 | ⏳ | `3dab253` |
| 2 | Squelette du projet : LICENSE, README, configuration, premiers tests | 0.1.0.dev0 | ✅ 18/10/2026 | ⏳ | `7d73420` |
| 3 | Icônes (Windows, Linux, favicon) à partir du logo ; passage en 0.1.0 | 0.1.0 | ✅ 18/10/2026 | ⏳ | `a6d820e` |
| 4 | Première fenêtre : icône, thème Turquoise, menus, « À propos » | 0.1.1 | ✅ 18/10/2026 | ⏳ | `b581711` |
| 5 | Tests automatiques sur GitHub (Windows, Ubuntu, Fedora 44) — fin du jalon 1 | 0.2.0 | 🔄 | ⏳ | — |

Les étapes suivantes seront ajoutées au fur et à mesure.

Depuis l'étape 5, GitHub teste aussi automatiquement chaque envoi sous Fedora 44 (sans écran). Les tests manuels ci-dessous restent utiles pour vérifier l'affichage réel : fenêtre, icône dans le dock, menus.

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
xdg-open assets/icons/png/runecast-256.png
uv run python tools/install_desktop_entry.py
uv run runecast
```

Avant la première commande `uv run runecast`, si Qt se plaint de « xcb-cursor », installe aussi : `sudo dnf install xcb-util-cursor`.

Si le dossier `~/ai/RuneCast` existe déjà, remplace les lignes `mkdir`, `cd ~/ai` et `git clone` par :

```bash
cd ~/ai/RuneCast
git pull
```

Résultat attendu :

- **Étape 1** : `uv run python --version` affiche Python 3.13.x.
- **Étape 2** : `uv run runecast --version` affiche « Créé par HARPUTOGLU David, aidé par l'IA ».
- **Étape 3** : `xdg-open` ouvre l'icône 256 px, identique à celle de Windows.
- **Étape 4** : `uv run pytest` se termine par « 51 passed », sans « failed » ; `uv run runecast --version` affiche « RuneCast 0.2.0 » ; `uv run runecast` ouvre la fenêtre turquoise avec ton icône dans le dock ; les menus Fichier → Quitter et Aide → À propos fonctionnent.
