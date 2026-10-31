# Journal des versions / Changelog

## Règle de numérotation / Numbering rule

Décidée le 18 octobre 2026 / Decided on 18 October 2026:

| Chiffre / Number | Qui le change / Who changes it | Exemple / Example |
|---|---|---|
| Les deux premiers (« 0.1 ») / The first two ("0.1") | **Uniquement l'auteur, HARPUTOGLU David** / **Only the author, HARPUTOGLU David** | 0.1 → 0.2, 1.0… |
| Le dernier / The last one | À chaque étape validée ou correctif / With each validated step or fix | 0.1.0 → 0.1.1 → 0.1.2… |

> **Correction du 18 octobre 2026** : les étapes 5 à 8 avaient été numérotées 0.2.0 à 0.2.3 par erreur (Claude avait changé lui-même le chiffre du milieu). Elles sont renumérotées 0.1.2 à 0.1.5 ci-dessous. Les messages de commit de ces étapes gardent l'ancien numéro.
> *Correction of 18 October 2026: steps 5 to 8 had been numbered 0.2.0 to 0.2.3 by mistake (Claude had changed the middle number on its own). They are renumbered 0.1.2 to 0.1.5 below. The commit messages of these steps keep the old number.*

## 0.1.16 (correctif / fix)

- Yandex gratuit : nouvelle porte d'entrée, le service de traduction du navigateur Yandex (celui de Yandex Browser) : pas de clé, pas de session, plusieurs phrases par demande. Méthode documentée par le projet libre OverTranslate (licence MIT), mesurée le 30 octobre 2026. L'ancienne méthode du widget (LocoAI), qui répondait « 429 limited », reste essayée en second ; la première qui répond est retenue.
  *Yandex free: new entrance, Yandex Browser's translation service: no key, no session, several sentences per request. Method documented by the free project OverTranslate (MIT license), measured on 30 October 2026. The old widget method (LocoAI), which answered "429 limited", is still tried second; the first one answering is kept.*
- Yandex n'écrit que le chinois simplifié : le chinois traditionnel est laissé au moteur suivant.
  *Yandex writes Simplified Chinese only: Traditional Chinese is left to the next engine.*

## 0.1.15 (étape 18 / step 18)

- Glossaires par jeu (`core/glossary.py`), un fichier par glossaire dans le dossier des réglages (`glossaires`), avec numéro de format. Ils seront reliés aux profils de jeux aux étapes 21 et 28.
  *Per-game glossaries, one file per glossary in the settings folder, with a format number. They will be linked to game profiles in steps 21 and 28.*
- Application forcée : chaque terme imposé est protégé comme une balise avant l'envoi au moteur (qui ne le voit jamais), puis remplacé par sa traduction imposée. Mots entiers (« Ann » ne touche pas « Anna »), les plus longs d'abord, majuscules ignorées sauf si demandé, balises et variables jamais touchées. Les lignes avec un terme imposé ne passent pas par le cache.
  *Forced application: each imposed term is protected like a tag before being sent to the engine (which never sees it), then replaced by its imposed translation. Whole words, longest first, case ignored unless asked, tags and variables never touched. Lines with an imposed term skip the cache.*
- Rapport de contrôle : chaque ligne est vérifiée ; un terme imposé absent la marque « à vérifier ».
  *Control report: each line is checked; a missing imposed term marks it "to check".*
- Outils → Glossaires… : créer, renommer, supprimer ; tableau modifiable (terme, traduction imposée, note, respecter la casse) ; import et export CSV (virgule ou point-virgule, compatible Excel et LibreOffice) ; « Traduire et contrôler » avec rapport.
  *Tools → Glossaries…: create, rename, delete; editable table; CSV import and export (Excel and LibreOffice compatible); "Translate and check" with report.*
- Nouveau menu « Outils ».
  *New "Tools" menu.*

## 0.1.14 (étape 17 / step 17)

- Chaîne de traduction (`engines/chain.py`) : protection des balises, cache, moteurs en ligne cochés dans l'ordre, puis modèles Argos, puis NLLB-200. Une ligne qui perd une balise est marquée « à vérifier » et n'entre pas dans le cache.
  *Translation chain: tag protection, cache, checked online engines in order, then Argos models, then NLLB-200. A line losing a tag is marked "to check" and does not enter the cache.*
- Repli automatique : un moteur qui ne répond plus (internet coupé, limite atteinte, clé refusée, service en panne) est mis de côté pour la suite du travail et le suivant prend le relais. Le travail avance par paquets de 20 lignes : un Wi-Fi coupé en pleine traduction ne fait perdre aucune ligne.
  *Automatic fallback: an engine that stops answering is set aside for the rest of the job and the next one takes over. Work goes in chunks of 20 lines: a Wi-Fi cut mid-translation loses no line.*
- Mode 100 % local : les moteurs en ligne ne sont même pas créés, et un verrou bloque toute connexion vers un service de traduction (les mises à jour et le téléchargement des modèles restent possibles).
  *100 % local mode: online engines are not even created, and a lock blocks any connection to a translation service (updates and model downloads remain possible).*
- Paramètres → Traduction : choix du mode, ordre réellement utilisé, et essai de la chaîne (une phrase par ligne) montrant le moteur de chaque ligne et les relais.
  *Settings → Translation: mode choice, order really used, and chain test (one sentence per line) showing each line's engine and the hand-overs.*

## 0.1.13 (étape 16 / step 16)

- Moteurs de traduction en ligne, tous avec le même contrat que le moteur local : Yandex gratuit (méthode du widget de LocoAI, non officielle), Yandex Cloud (clé officielle, passe avant le gratuit), Google gratuit (non officiel), DeepL (clé Free « :fx » ou Pro), Google Cloud, Microsoft Translator et LibreTranslate (serveur au choix).
  *Online translation engines, all with the same contract as the local engine: Yandex free (LocoAI's widget method, unofficial), Yandex Cloud (official key, goes before the free one), Google free (unofficial), DeepL (Free ":fx" or Pro key), Google Cloud, Microsoft Translator and LibreTranslate (server of your choice).*
- Chaque panne devient une raison claire (pas d'internet, clé refusée, limite atteinte, service en panne), prête pour le repli automatique de l'étape 17. Textes envoyés par lots qui respectent les limites de chaque service.
  *Every failure becomes a clear reason (no internet, key refused, limit reached, service down), ready for step 17's automatic fallback. Texts sent in batches respecting each service's limits.*
- Paramètres → Moteurs en ligne : moteurs à cocher et ordre réglable (« Monter », « Descendre »), clé et réglages de chaque moteur, prix indicatif et estimation pour un jeu moyen, avertissement pour les accès non officiels, bouton « Tester ».
  *Settings → Online engines: engines to check and adjustable order, key and settings for each engine, indicative price and estimate for an average game, warning for unofficial accesses, "Test" button.*
- Clés rangées dans le trousseau sécurisé du système (Gestionnaire d'identification Windows, GNOME Trousseau ou KWallet), jamais dans les réglages ; en mode portable, dans le dossier portable (avec un avertissement).
  *Keys stored in the system's secure keyring, never in the settings; in portable mode, in the portable folder (with a warning).*
- Essai réel par GitHub : Google gratuit fonctionne et garde balises et variables ; Yandex gratuit répond « limite atteinte » depuis les serveurs de GitHub (à essayer depuis une connexion personnelle).
  *Real test by GitHub: Google free works and keeps tags and variables; Yandex free answers "limit reached" from GitHub's servers (to be tried from a personal connection).*
- Nouvelle dépendance : keyring (MIT), avec ses petites bibliothèques (jaraco, more-itertools, jeepney, SecretStorage, cryptography ; toutes compatibles GPLv3).
  *New dependency: keyring (MIT), with its small libraries (all GPLv3-compatible).*

## 0.1.12 (étape 15 / step 15)

- Modèle étendu NLLB-200 (Meta, version « distillée 600M », format CTranslate2 int8, environ 600 Mo) : traduction locale directe entre 38 langues proposées, dont le kazakh, l'ouzbek, le turkmène, le tatar et l'ouïghour, que les modèles Argos ne couvrent pas.
  *NLLB-200 extended model (Meta, "distilled 600M", CTranslate2 int8, about 600 MB): direct local translation between 38 offered languages, including Kazakh, Uzbek, Turkmen, Tatar and Uyghur, which Argos models do not cover.*
- Téléchargé seulement après acceptation de sa licence (CC-BY-NC 4.0, usage non commercial) dans une fenêtre dédiée ; la date d'acceptation est enregistrée.
  *Downloaded only after its license (CC-BY-NC 4.0, non-commercial use) is accepted in a dedicated window; the acceptance date is recorded.*
- Fichiers figés sur une révision précise du dépôt Hugging Face, chacun vérifié par son empreinte SHA-256 ; installation complète ou rien.
  *Files pinned to one precise revision of the Hugging Face repository, each checked by its SHA-256 fingerprint; complete-or-nothing installation.*
- Vérifié pour de vrai par GitHub : « Hello, how are you today? » → « Сәлем, бүгін қалайсыз? » (kazakh), « Salom, bugun qandaysan? » (ouzbek), « Salam, bu gün nähili? » (turkmène), « Сәлам, син бүген ничек? » (tatar), « ئەسسالامۇ ئەلەيكۇم، بۈگۈن قانداق؟ » (ouïghour).
  *Really checked by GitHub (see the sentences above).*
- « Essayer » utilise NLLB-200 quand aucun modèle Argos ne couvre la paire de langues.
  *"Try" uses NLLB-200 when no Argos model covers the language pair.*

## 0.1.11 (étape 14 / step 14)

- Banc d'essai de la traduction locale : `runecast --benchmark [de vers]` mesure, sur le PC, la vitesse (phrases par seconde) et la mémoire pour chaque nombre de cœurs et chaque largeur de recherche (rapide, équilibrée, précise), vérifie que la mémoire reste stable, conseille les meilleurs réglages et enregistre un rapport dans le dossier du journal.
  *Local translation benchmark: `runecast --benchmark [from to]` measures speed and memory for each core count and search width, checks that memory stays stable, recommends the best settings and saves a report in the log folder.*
- Paramètres → Modèles de traduction → Performance : cœurs utilisés (automatique ou au choix) et traduction rapide, équilibrée ou précise ; bouton « Mesurer la vitesse… » qui choisit les réglages conseillés.
  *Settings → Translation models → Performance: cores used and fast/balanced/accurate translation; "Measure the speed…" button selecting the recommended settings.*
- Mesures réelles sur la machine de GitHub (2 cœurs) : 53 phrases par seconde en anglais → français, moins de 400 Mo de mémoire, stable. Réglages par défaut confirmés : équilibrée, cœurs automatiques.
  *Real measures on GitHub's machine (2 cores): 53 sentences per second English → French, under 400 MB of memory, stable. Default settings confirmed: balanced, automatic cores.*
- Nouvelle dépendance : psutil (BSD), pour mesurer la mémoire et compter les cœurs.
  *New dependency: psutil (BSD), to measure memory and count cores.*

## 0.1.10 (étape 13 / step 13)

- Moteur de traduction locale : les modèles libres d'Argos Translate tournent sur le PC, sans internet et sans GPU, grâce à CTranslate2 (format compact « int8 ») et SentencePiece. S'il n'y a pas de modèle direct, RuneCast passe par l'anglais (Français → English → Türkçe). Au plus deux modèles en mémoire, pour rester léger sur 8 Go.
  *Local translation engine: Argos Translate's free models run on the PC, without internet and without GPU, thanks to CTranslate2 (compact "int8" format) and SentencePiece. When there is no direct model, RuneCast goes through English. At most two models in memory, to stay light on 8 GB.*
- Contrat commun des moteurs (`engines/base.py`) : les moteurs en ligne de l'étape 16 suivront le même.
  *Common engine contract (`engines/base.py`): the online engines of step 16 will follow the same one.*
- Catalogue de 85 modèles (`resources/models/argos-catalog.json`), chacun avec sa taille et son empreinte SHA-256. Ces empreintes ont été mesurées par GitHub, qui a téléchargé chaque modèle et lui a fait traduire une phrase avec le moteur de RuneCast (nouveau test automatique « Modèles », relancé quand le catalogue ou le moteur change).
  *Catalogue of 85 models, each with its size and SHA-256 fingerprint. These fingerprints were measured by GitHub, which downloaded each model and made it translate a sentence with RuneCast's engine (new "Models" automatic check, re-run when the catalogue or the engine changes).*
- Paramètres → Modèles de traduction : recherche par langue (noms écrits dans chaque langue), téléchargement avec barre de progression, annulation et reprise après coupure, vérification de l'empreinte, installation sûre (archive vérifiée, ancien modèle remplacé seulement si tout réussit), suppression, pack hors-ligne (« Télécharger pour un autre PC… » puis « Importer des fichiers… »), et « Essayer » pour traduire une phrase.
  *Settings → Translation models: search by language, download with progress bar, cancel and resume, fingerprint check, safe installation, deletion, offline pack, and "Try" to translate a sentence.*
- Limite connue : 15 modèles Argos utilisent un autre découpeur de texte (« BPE » : tchèque, danois, hongrois, indonésien, lituanien, polonais, et espagnol, finnois, roumain, ukrainien vers l'anglais). Les lire demanderait 5 bibliothèques de plus : ils ne sont pas proposés pour l'instant (les moteurs en ligne de l'étape 16 couvrent ces langues).
  *Known limit: 15 Argos models use another text splitter ("BPE"). Reading them would need 5 more libraries: they are not offered for now (the online engines of step 16 cover these languages).*
- Nouvelles dépendances : ctranslate2 (MIT, avec numpy et PyYAML), sentencepiece (Apache 2.0), httpx (BSD).
  *New dependencies: ctranslate2 (MIT, with numpy and PyYAML), sentencepiece (Apache 2.0), httpx (BSD).*

## 0.1.9 (étape 12 / step 12)

- Cache des traductions (base SQLite `translations.sqlite3` dans le dossier des données) : une phrase identique n'est jamais retraduite, et chaque phrase n'est envoyée qu'une fois au moteur même si elle se répète. Le journal indique combien de phrases viennent du cache.
  *Translation cache (SQLite base `translations.sqlite3` in the data folder): an identical sentence is never translated again, and each sentence is sent only once to the engine even when it repeats. The log says how many sentences came from the cache.*
- Historique des traductions : date, jeu, moteur, langues, et origine (moteur, cache ou correction à la main).
  *Translation history: date, game, engine, languages, and origin (engine, cache or manual fix).*
- Base protégée : numéro de version pour les futures conversions, fichier abîmé mis de côté (jamais effacé), utilisation simultanée possible.
  *Protected base: version number for future conversions, damaged file set aside (never deleted), simultaneous use possible.*
- Paramètres → Cache des traductions : nombre de phrases, lignes d'historique, taille ; boutons pour vider le cache ou l'historique (après confirmation).
  *Settings → Translation cache: number of sentences, history lines, size; buttons to empty the cache or the history (after confirmation).*
- Correctif : les tailles de fichiers (fenêtre « Dossiers de RuneCast ») s'affichent maintenant dans la langue choisie (« 11.8 MB » en anglais) au lieu de toujours en français.
  *Fix: file sizes ("RuneCast folders" window) are now shown in the chosen language ("11.8 MB" in English) instead of always in French.*

## 0.1.8 (étape 11 / step 11)

- Protection des balises et des variables avant traduction (`core/protect.py`) : balises Ren'Py ({b}, {color=…}, {w}, {a=…}, {rb}/{rt}…), variables ([player], [mc!t], [items[0]]…), échappements ({{, [[, %%, \n…), formats Python (%s, %(nom)s, {0}…), retours à la ligne et espaces de début et de fin. Chaque élément est remplacé par un repère numéroté ([0], [1]… ou <x id="0"/> pour les moteurs HTML), puis remis à sa place.
  *Tag and variable protection before translation (`core/protect.py`): Ren'Py tags, variables, escapes, Python formats, line breaks and leading/trailing spaces. Each item is replaced by a numbered marker ([0], [1]… or <x id="0"/> for HTML engines), then put back.*
- Contrôle après traduction : repère perdu, en double ou inventé, balises dans le désordre, « [ » ou « { » ajouté par le moteur, traduction vide. Une ligne qui échoue est marquée « à vérifier » au lieu d'être écrite dans le jeu.
  *Check after translation: lost, duplicated or made-up marker, tags out of order, "[" or "{" added by the engine, empty translation. A failing line is marked "to check" instead of being written into the game.*
- Environ 190 cas de test tirés de vrais jeux Ren'Py, et démonstration en ligne de commande : `runecast --protect "texte"`.
  *About 190 test cases taken from real Ren'Py games, and a command-line demonstration: `runecast --protect "text"`.*

## 0.1.7 (étape 10 / step 10)

- Fenêtre « Paramètres » (Fichier → Paramètres…, ou Ctrl+virgule), avec les boutons OK, Annuler et Appliquer, et trois pages :
  *"Settings" window (File → Settings…, or Ctrl+comma), with OK, Cancel and Apply buttons, and three pages:*
  - Général : langue de l'interface et thème (avec accès à l'éditeur de thèmes) ;
    *General: interface language and theme (with access to the theme editor);*
  - Fenêtre : rouvrir ou non la fenêtre à la même taille et à la même place ;
    *Window: reopen the window with the same size and position, or not;*
  - Dossiers et journal : dossiers utilisés, accès à « Dossiers de RuneCast », journal détaillé (pour signaler un problème), ouverture du dossier du journal.
    *Folders and log: folders in use, access to "RuneCast folders", detailed log (to report a problem), opening the log folder.*
- Nouveaux menus : Affichage → Plein écran (F11) ; Aide → Ouvrir le dossier du journal ; Aide → Signaler un problème… (page GitHub du projet).
  *New menus: View → Full screen (F11); Help → Open the log folder; Help → Report a problem… (project's GitHub page).*
- Un test automatique vérifie qu'aucune entrée de menu n'est factice (règle du cahier des charges).
  *An automatic test checks that no menu entry is a dummy (specification rule).*
- Réglages : deux nouveaux réglages (`remember_window`, `detailed_log`), avec une valeur par défaut ; les anciens fichiers de réglages restent lisibles.
  *Settings: two new settings (`remember_window`, `detailed_log`), with a default value; older settings files stay readable.*

## 0.1.6 (étape 9 / step 9)

- Éditeur de thèmes personnels (Affichage → Thème → Gérer les thèmes…) : dupliquer un thème, changer ses 12 couleurs (sélecteur de couleurs ou code #RRGGBB), son nom et le caractère sombre ou clair, avec un aperçu en direct.
  *Custom theme editor (View → Theme → Manage themes…): duplicate a theme, change its 12 colours (colour picker or #RRGGBB code), its name and the dark/light flag, with a live preview.*
- Avertissement de lisibilité : si un texte devient difficile à lire (contraste inférieur à 4,5:1, norme WCAG), l'éditeur l'indique.
  *Readability warning: when a text becomes hard to read (contrast below 4.5:1, WCAG standard), the editor says so.*
- Enregistrer, utiliser, supprimer (après confirmation), importer et exporter un thème (fichier .json). Les thèmes personnels sont rangés dans le dossier `themes` des réglages, voyagent avec les données si on les déplace, et sont toujours là après un redémarrage. Les thèmes intégrés ne sont jamais modifiés.
  *Save, use, delete (after confirmation), import and export a theme (.json file). Custom themes are stored in the `themes` folder of the settings, travel with the data when it is moved, and are still there after a restart. Built-in themes are never modified.*
- Un fichier de thème abîmé est ignoré (et noté dans le journal), sans être supprimé et sans empêcher RuneCast de démarrer. Un export ne remplace jamais un fichier existant sans accord.
  *A damaged theme file is skipped (and logged), without being deleted and without preventing RuneCast from starting. An export never replaces an existing file without consent.*
- Correctif : les cases à cocher sont maintenant bien visibles dans tous les thèmes (leur contour disparaissait sur le thème Noir).
  *Fix: check boxes are now clearly visible in every theme (their outline disappeared on the Black theme).*

## 0.1.5 (étape 8 / step 8)

- 4 thèmes intégrés : Turquoise (par défaut), Noir, Sombre et Clair, au choix dans Affichage → Thème. Le changement est immédiat et retenu au prochain lancement ; la barre de titre de Windows suit le thème (sombre ou claire).
  *4 built-in themes: Turquoise (default), Black, Dark and Light, chosen from View → Theme. The change is immediate and remembered; the Windows title bar follows the theme (dark or light).*
- Thèmes décrits dans des fichiers JSON (dossier `resources/themes`), vérifiés au chargement : ce format servira aux thèmes personnels de l'étape 9.
  *Themes described in JSON files (`resources/themes` folder), checked when loaded: this format will be used by the custom themes of step 9.*
- Lisibilité garantie par des tests : contraste d'au moins 4,5 (norme d'accessibilité WCAG) pour le texte, les liens et la sélection, dans chaque thème.
  *Readability guaranteed by tests: contrast of at least 4.5 (WCAG accessibility standard) for text, links and selection, in every theme.*

## 0.1.4 (étape 7 / step 7)

- Langues de l'interface : français, anglais et arabe, avec changement en direct (Affichage → Langue de l'interface), sans redémarrer. Choix « Langue du système » par défaut ; si la langue du système n'est pas disponible : anglais.
  *Interface languages: French, English and Arabic, switched live (View → Interface language), without restarting. "System language" by default; if the system language is not available: English.*
- Arabe : toute l'interface passe de droite à gauche ; chemins et adresses restent lisibles dans les phrases arabes.
  *Arabic: the whole interface switches to right-to-left; paths and addresses stay readable inside Arabic sentences.*
- Polices embarquées Noto Sans et Noto Sans Arabic (licence OFL) : toutes les lettres turciques, cyrilliques, arabes et ouïghoures s'affichent, identiques sous Windows et Linux.
  *Bundled Noto Sans and Noto Sans Arabic fonts (OFL license): all Turkic, Cyrillic, Arabic and Uyghur letters display, identical on Windows and Linux.*
- Traductions au format Qt (.ts / .qm) avec l'outil `tools/update_translations.py` ; les tests vérifient que chaque texte est traduit dans chaque langue.
  *Qt-format translations (.ts / .qm) with the `tools/update_translations.py` tool; tests check that every text is translated in every language.*

## 0.1.3 (étape 6 / step 6)

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

## 0.1.2 (étape 5, fin du jalon 1 / step 5, end of milestone 1)

- Tests automatiques sur GitHub (GitHub Actions) à chaque envoi : Windows, Ubuntu et Fedora 44, avec contrôle de la qualité du code.
  *Automatic tests on GitHub (GitHub Actions) on every push: Windows, Ubuntu and Fedora 44, with code quality checks.*
- Badge « Tests » sur la page d'accueil du projet.
  *"Tests" badge on the project home page.*
- Fin du jalon 1 (démarrage).
  *End of milestone 1 (start-up).*

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
