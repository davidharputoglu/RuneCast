# Suivi des étapes / Step tracking

Ce fichier indique, pour chaque étape du [plan](PLAN-V1.md), si les tests automatiques de GitHub sont passés, et si tu l'as testée toi-même sur tes deux PC.

Légende : ✅ validée · ⏳ test à faire · 🔄 en cours

Depuis le 31 octobre 2026, à ta demande, j'enchaîne les étapes sans attendre ton « OK » entre chacune, et je les envoie moi-même sur GitHub. Je m'arrête quand j'ai besoin de toi (prochain arrêt : étape 20, jeux de test). Pour récupérer les nouvelles étapes sur ton PC : `cd C:\ai\RuneCast` puis `git pull`.

| Étape | Description | Version | Tests GitHub | Ton test Windows 10 | Ton test Fedora 44 | Commit |
|---|---|---|---|---|---|---|
| 1 | Poste de travail (Git, uv, Python 3.13) et dépôt GitHub | — | ✅ | ✅ 18/10/2026 | ⏳ | `3dab253` |
| 2 | Squelette du projet : LICENSE, README, configuration, premiers tests | 0.1.0.dev0 | ✅ | ✅ 18/10/2026 | ⏳ | `7d73420` |
| 3 | Icônes (Windows, Linux, favicon) à partir du logo ; passage en 0.1.0 | 0.1.0 | ✅ | ✅ 18/10/2026 | ⏳ | `a6d820e` |
| 4 | Première fenêtre : icône, thème Turquoise, menus, « À propos » | 0.1.1 | ✅ | ✅ 18/10/2026 | ⏳ | `b581711` |
| 5 | Tests automatiques sur GitHub (Windows, Ubuntu, Fedora 44) — fin du jalon 1 | 0.1.2 | ✅ | ✅ 18/10/2026 | ⏳ | `e906322` |
| 6 | Dossiers de données, dossier personnalisé, mode portable, réglages, journal | 0.1.3 | ✅ | ✅ 18/10/2026 | ⏳ | `10f6316` |
| 7 | Langues de l'interface (FR, EN, AR en RTL), polices Noto | 0.1.4 | ✅ | ✅ 18/10/2026 | ⏳ | `a5bbca3` |
| 8 | 4 thèmes intégrés (Turquoise, Noir, Sombre, Clair) | 0.1.5 | ✅ | ✅ 18/10/2026 | ⏳ | `2535bba` |
| 9 | Éditeur de thèmes personnels (créer, enregistrer, importer, exporter, supprimer) ; cases à cocher lisibles | 0.1.6 | ✅ | ⏳ | ⏳ | `3428597` |
| 10 | Fenêtre principale complète (Paramètres, plein écran, journal, signaler un problème) ; fenêtre « Paramètres » | 0.1.7 | ✅ | ⏳ | ⏳ | `b97c466` |
| 11 | Protection des balises et variables Ren'Py (masquage, restauration, contrôle), environ 190 cas de test ; démonstration `runecast --protect` | 0.1.8 | ✅ | ⏳ | ⏳ | `63e18cb` |
| 12 | Cache et historique des traductions (SQLite) ; page « Cache des traductions » dans les Paramètres | 0.1.9 | ✅ | ⏳ | ⏳ | `27011fd` |
| 13 | Moteur local (modèles Argos avec CTranslate2) et gestionnaire de modèles : catalogue vérifié, téléchargement avec reprise, empreintes SHA-256, suppression, pack hors-ligne, « Essayer » | 0.1.10 | ✅ | ⏳ | ⏳ | `24ec9ff` |
| 14 | Banc d'essai vitesse et mémoire (`runecast --benchmark`, bouton « Mesurer la vitesse… ») ; réglages Performance | 0.1.11 | 🔄 | ⏳ | ⏳ | `ac425c7` + suivant |

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
- **Toutes les étapes** : `uv run pytest` se termine par « passed », sans « failed ».
- **Étape 14** : après avoir installé « English → Français » (étape 13), tape `uv run runecast --benchmark en fr`. Le tableau des vitesses s'affiche, puis « Conseillé » et « Mémoire stable : oui ». Le rapport est enregistré dans le dossier du journal : envoie-le-moi pour que je règle les valeurs par défaut sur tes vrais PC. Même chose dans Paramètres → Modèles de traduction → Performance → « Mesurer la vitesse… ».
- **Étape 13** : Fichier → Paramètres… → Modèles de traduction. Tape « Français » dans la recherche, choisis « English → Français », clique sur « Télécharger et installer » (environ 107 Mo, la barre de progression avance). Ensuite, **coupe le Wi-Fi**, écris « Hello, how are you? » dans « Essayer », clique sur « Traduire » : la traduction française s'affiche. Rallume le Wi-Fi.
- **Étape 12** : Fichier → Paramètres… → Cache des traductions : la page affiche « Phrases en mémoire : 0 » (le cache se remplira avec les premières traductions, à partir de l'étape 13). Le test « une phrase identique n'est pas retraduite » est fait automatiquement par `uv run pytest`.
- **Étape 11** : `uv run runecast --protect "{b}Bonjour{/b} [player] !"` affiche `[0]Bonjour[1] [2] !`, la liste des éléments protégés et « Contrôle du retour : OK ».
- **Étape 10** : Fichier → Paramètres… (ou Ctrl+virgule) ouvre la fenêtre « Paramètres » ; changer le thème puis « Appliquer » le change aussitôt ; « Annuler » ne change rien ; Affichage → Plein écran (F11) ; Aide → Ouvrir le dossier du journal ouvre le dossier ; Aide → Signaler un problème… ouvre la page GitHub.
- **Étape 9** : Affichage → Thème → Gérer les thèmes… → Dupliquer, changer une couleur, Enregistrer, Utiliser ce thème ; après avoir fermé et relancé `uv run runecast`, le thème personnel est toujours appliqué.
- **Étape 8** : Affichage → Thème → Noir, Sombre, Clair puis Turquoise : les couleurs changent aussitôt. Affichage → Thème → Noir, Sombre, Clair puis Turquoise : les couleurs changent aussitôt.
- **Étape 7** : Affichage → Langue de l'interface → English puis العربية : l'interface change aussitôt, et passe de droite à gauche en arabe.
- **Étape 6** : `uv run runecast --paths` affiche `~/.config/runecast`, `~/.local/share/runecast`, `~/.cache/runecast` et `~/.local/state/runecast/log` ; Aide → Dossiers de RuneCast… montre les mêmes dossiers.
- **Étape 4** : `uv run runecast --version` affiche la version en cours ; `uv run runecast` ouvre la fenêtre turquoise avec ton icône dans le dock ; les menus Fichier → Quitter et Aide → À propos fonctionnent.

## Mesures du banc d'essai (étape 14)

| Machine | Cœurs physiques | Réglage | Phrases par seconde (anglais → français) | Mémoire au plus haut | Mémoire stable |
|---|---|---|---|---|---|
| GitHub (Ubuntu, 31/10/2026) | 2 | 1 cœur, rapide | 44,9 | 192 Mo | oui |
| GitHub | 2 | 1 cœur, équilibrée | 29,8 | 217 Mo | oui |
| GitHub | 2 | 2 cœurs, rapide | 84,1 | 311 Mo | oui |
| GitHub | 2 | **2 cœurs, équilibrée (conseillé)** | **53,2** | **372 Mo** | oui (+0 Mo en 3 tours) |
| GitHub | 2 | 2 cœurs, précise | 30,9 | 421 Mo | oui |
| Ton PC Windows 10 | ⏳ | | | | |
| Ton PC Fedora 44 | ⏳ | | | | |

Réglages par défaut retenus : traduction « équilibrée » (largeur 2), cœurs automatiques (la moitié des cœurs logiques, entre 1 et 4), lots de 32 phrases. Mémoire de RuneCast avec un modèle chargé : moins de 400 Mo, très loin des 8 Go.
