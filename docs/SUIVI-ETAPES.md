# Suivi des étapes / Step tracking

Ce fichier indique, pour chaque étape du [plan](PLAN-V1.md), sur quelle machine elle a été testée et validée.

Légende : ✅ validée · ⏳ test à faire · 🔄 en cours

| Étape | Description | Version | Windows 10 | Fedora 44 | Commit |
|---|---|---|---|---|---|
| 1 | Poste de travail (Git, uv, Python 3.13) et dépôt GitHub | — | ✅ 18/10/2026 | ⏳ | `3dab253` |
| 2 | Squelette du projet : LICENSE, README, configuration, premiers tests | 0.1.0.dev0 | ✅ 18/10/2026 | ⏳ | `7d73420` |
| 3 | Icônes (Windows, Linux, favicon) à partir du logo ; passage en 0.1.0 | 0.1.0 | ✅ 18/10/2026 | ⏳ | `a6d820e` |
| 4 | Première fenêtre : icône, thème Turquoise, menus, « À propos » | 0.1.1 | ✅ 18/10/2026 | ⏳ | `b581711` |
| 5 | Tests automatiques sur GitHub (Windows, Ubuntu, Fedora 44) — fin du jalon 1 | 0.1.2 | ✅ 18/10/2026 | ✅ GitHub (sans écran) | `e906322` |
| 6 | Dossiers de données, dossier personnalisé, mode portable, réglages, journal | 0.1.3 | ✅ 18/10/2026 | ⏳ | `10f6316` |
| 7 | Langues de l'interface (FR, EN, AR en RTL), polices Noto | 0.1.4 | ✅ 18/10/2026 | ⏳ | `a5bbca3` |
| 8 | 4 thèmes intégrés (Turquoise, Noir, Sombre, Clair) | 0.1.5 | ✅ 18/10/2026 | ⏳ | `2535bba` |
| 9 | Éditeur de thèmes personnels (créer, enregistrer, importer, exporter, supprimer) ; cases à cocher lisibles | 0.1.6 | 🔄 à tester | ⏳ | — |

Numéros de version : les deux premiers chiffres (« 0.1 ») sont décidés par David ; le dernier augmente à chaque étape validée ou correctif. Les étapes 5 à 8 avaient été numérotées 0.2.x par erreur et ont été corrigées (voir CHANGELOG.md).

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
uv run runecast --paths
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
- **Étape 9** : `uv run pytest` se termine par « 182 passed », sans « failed » ; Affichage → Thème → Gérer les thèmes… → Dupliquer, changer une couleur, Enregistrer, Utiliser ce thème ; après avoir fermé et relancé `uv run runecast`, le thème personnel est toujours appliqué.
- **Étape 8** : Affichage → Thème → Noir, Sombre, Clair puis Turquoise : les couleurs changent aussitôt. Affichage → Thème → Noir, Sombre, Clair puis Turquoise : les couleurs changent aussitôt.
- **Étape 7** : Affichage → Langue de l'interface → English puis العربية : l'interface change aussitôt, et passe de droite à gauche en arabe.
- **Étape 6** : `uv run runecast --paths` affiche `~/.config/runecast`, `~/.local/share/runecast`, `~/.cache/runecast` et `~/.local/state/runecast/log` ; Aide → Dossiers de RuneCast… montre les mêmes dossiers.
- **Étape 4** : `uv run runecast --version` affiche la version en cours ; `uv run runecast` ouvre la fenêtre turquoise avec ton icône dans le dock ; les menus Fichier → Quitter et Aide → À propos fonctionnent.
