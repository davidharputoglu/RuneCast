# Journal des versions / Changelog

## Règle de numérotation / Numbering rule

Décidée le 18 octobre 2026 / Decided on 18 October 2026:

| Quand / When | Exemple / Example |
|---|---|
| Chaque étape validée ou correctif / Each validated step or fix | 0.1.0 → 0.1.1 → 0.1.2… |
| Fin d'un jalon (groupe d'étapes) / End of a milestone (group of steps) | 0.1.x → 0.2.0, puis/then 0.3.0… |
| Version complète du cahier des charges, publiée pour le public / Complete specification, public release | 1.0.0 |

## 0.1.0 (étape 3 / step 3)

- Icônes de l'application, fabriquées à partir du logo d'origine sans retouche : `.ico` pour Windows (16 à 256 px), PNG pour Linux (16 à 512 px), favicon (16, 32, 48 px), logo carré en pleine résolution.
  *Application icons built from the untouched original logo: Windows `.ico` (16–256 px), Linux PNG (16–512 px), favicon (16, 32, 48 px), full-resolution square logo.*
- Outil `tools/make_icons.py` pour refabriquer les icônes si le logo change.
  *`tools/make_icons.py` tool to rebuild the icons if the logo changes.*
- Tests automatiques des icônes (tailles, contenu identique au logo).
  *Automatic icon tests (sizes, content identical to the logo).*
- Le numéro de version passe de 0.1.0.dev0 à 0.1.0.
  *Version number moves from 0.1.0.dev0 to 0.1.0.*

## Avant 0.1.0 / Before 0.1.0

- **Étape 2 / Step 2** : squelette du projet, licence GPLv3 ou ultérieure, README, commande `runecast --version`, premiers tests automatiques.
  *Project skeleton, GPLv3-or-later license, README, `runecast --version` command, first automatic tests.*
- **Étape 1 / Step 1** : organisation du dépôt et configuration Git.
  *Repository layout and Git configuration.*
