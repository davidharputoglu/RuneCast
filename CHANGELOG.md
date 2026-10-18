# Journal des versions / Changelog

## Règle de numérotation / Numbering rule

Décidée le 18 octobre 2026 / Decided on 18 October 2026:

| Quand / When | Exemple / Example |
|---|---|
| Chaque étape validée ou correctif / Each validated step or fix | 0.1.0 → 0.1.1 → 0.1.2… |
| Fin d'un jalon (groupe d'étapes) / End of a milestone (group of steps) | 0.1.x → 0.2.0, puis/then 0.3.0… |
| Version complète du cahier des charges, publiée pour le public / Complete specification, public release | 1.0.0 |

## 0.2.3 (étape 8 / step 8)

- 4 thèmes intégrés : Turquoise (par défaut), Noir, Sombre et Clair, au choix dans Affichage → Thème. Le changement est immédiat et retenu au prochain lancement ; la barre de titre de Windows suit le thème (sombre ou claire).
  *4 built-in themes: Turquoise (default), Black, Dark and Light, chosen from View → Theme. The change is immediate and remembered; the Windows title bar follows the theme (dark or light).*
- Thèmes décrits dans des fichiers JSON (dossier `resources/themes`), vérifiés au chargement : ce format servira aux thèmes personnels de l'étape 9.
  *Themes described in JSON files (`resources/themes` folder), checked when loaded: this format will be used by the custom themes of step 9.*
- Lisibilité garantie par des tests : contraste d'au moins 4,5 (norme d'accessibilité WCAG) pour le texte, les liens et la sélection, dans chaque thème.
  *Readability guaranteed by tests: contrast of at least 4.5 (WCAG accessibility standard) for text, links and selection, in every theme.*

## 0.2.2 (étape 7 / step 7)

- Langues de l'interface : français, anglais et arabe, avec changement en direct (Affichage → Langue de l'interface), sans redémarrer. Choix « Langue du système » par défaut ; si la langue du système n'est pas disponible : anglais.
  *Interface languages: French, English and Arabic, switched live (View → Interface language), without restarting. "System language" by default; if the system language is not available: English.*
- Arabe : toute l'interface passe de droite à gauche ; chemins et adresses restent lisibles dans les phrases arabes.
  *Arabic: the whole interface switches to right-to-left; paths and addresses stay readable inside Arabic sentences.*
- Polices embarquées Noto Sans et Noto Sans Arabic (licence OFL) : toutes les lettres turciques, cyrilliques, arabes et ouïghoures s'affichent, identiques sous Windows et Linux.
  *Bundled Noto Sans and Noto Sans Arabic fonts (OFL license): all Turkic, Cyrillic, Arabic and Uyghur letters display, identical on Windows and Linux.*
- Traductions au format Qt (.ts / .qm) avec l'outil `tools/update_translations.py` ; les tests vérifient que chaque texte est traduit dans chaque langue.
  *Qt-format translations (.ts / .qm) with the `tools/update_translations.py` tool; tests check that every text is translated in every language.*

## 0.2.1 (étape 6 / step 6)

- Dossiers de données selon la norme de chaque système : réglages dans AppData\Roaming (Windows) ou ~/.config (Linux), gros fichiers dans AppData\Local ou ~/.local/share, plus cache et journaux.
  *Data folders following each system's standard: settings in AppData\Roaming (Windows) or ~/.config (Linux), large files in AppData\Local or ~/.local/share, plus cache and logs.*
- Choix d'un dossier personnalisé pour toutes les données (Aide → Dossiers de RuneCast…) : copie, vérification par empreinte SHA-256, puis suppression de l'ancien emplacement seulement si l'utilisateur l'accepte. Retour possible à l'emplacement standard.
  *Custom folder for all data (Help → RuneCast folders…): copy, SHA-256 verification, then deletion of the old location only if the user agrees. Going back to the standard location is possible.*
- Mode portable (fichier `portable.txt` à côté de l'application, ou option `--portable`).
  *Portable mode (`portable.txt` file next to the application, or `--portable` option).*
- Réglages enregistrés sans risque (écriture atomique, copie .bak, fichier abîmé mis de côté), avec numéro de version du format pour les futures migrations. La fenêtre se rouvre à la même taille et à la même place.
  *Settings saved safely (atomic write, .bak copy, damaged file set aside), with a format version number for future migrations. The window reopens at the same size and position.*
- Journal (logs) avec rotation : 1 Mo par fichier, 5 fichiers gardés. Option `--paths` pour afficher les dossiers.
  *Rotating log: 1 MB per file, 5 files kept. `--paths` option to print the folders.*
- Nouvelle dépendance : platformdirs (MIT).
  *New dependency: platformdirs (MIT).*

## 0.2.0 (étape 5, fin du jalon 1 / step 5, end of milestone 1)

- Tests automatiques sur GitHub (GitHub Actions) à chaque envoi : Windows, Ubuntu et Fedora 44, avec contrôle de la qualité du code.
  *Automatic tests on GitHub (GitHub Actions) on every push: Windows, Ubuntu and Fedora 44, with code quality checks.*
- Badge « Tests » sur la page d'accueil du projet.
  *"Tests" badge on the project home page.*
- Fin du jalon 1 (démarrage) : la version passe à 0.2.0.
  *End of milestone 1 (start-up): version moves to 0.2.0.*

## 0.1.1 (étape 4 / step 4)

- Première fenêtre de RuneCast : titre avec la version, icône, thème Turquoise de base (couleurs du logo, même aspect sous Windows et Linux), écran d'accueil.
  *First RuneCast window: title with version, icon, basic Turquoise theme (logo colours, same look on Windows and Linux), welcome screen.*
- Menus réels : Fichier → Quitter (Ctrl+Q) ; Aide → À propos de RuneCast, À propos de Qt.
  *Real menus: File → Quit (Ctrl+Q); Help → About RuneCast, About Qt.*
- Fenêtre « À propos » : logo, version, « Créé par HARPUTOGLU David, aidé par l'IA », contact, licence GPLv3 ou ultérieure, lien vers le code source.
  *"About" window: logo, version, credits, contact, GPLv3-or-later license, link to the source code.*
- Bonne icône dans la barre des tâches Windows ; outil `tools/install_desktop_entry.py` pour l'icône du dock sous Linux (Wayland).
  *Correct icon in the Windows taskbar; `tools/install_desktop_entry.py` tool for the dock icon on Linux (Wayland).*
- Nouvelle dépendance : PySide6-Essentials (Qt 6, LGPLv3). Outil de test : pytest-qt.
  *New dependency: PySide6-Essentials (Qt 6, LGPLv3). Test tool: pytest-qt.*

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
