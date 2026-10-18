# RuneCast v1.0 : avis technique, dépendances et plan de développement

> **Premier livrable demandé (règle n° 2) : aucun code.**
> Rédigé le 18 octobre 2026, **mis à jour le même jour avec tes réponses** (moteurs en ligne, langues, mode local, GitHub, icône, installation directe). Statut : **en attente de ta validation (« OK plan »).**
> Projet : RuneCast, créé par HARPUTOGLU David, aidé par l'IA. Licence GPLv3.

## Sommaire

1. Décisions en un coup d'œil
2. Avis argumenté sur les 7 points de la section 13
3. Architecture évolutive (phases 2, 3 et 4)
4. Liste complète des dépendances
5. Plan de développement (51 étapes)
6. Questions à trancher avant de coder
7. Sources

---

## 1. Décisions en un coup d'œil

| # | Sujet | Ma proposition | Question liée |
|---|---|---|---|
| 1 | Langage | **Python 3.13** (confirmé), installé et géré par **uv** sur tes deux PC | — |
| 2 | Traduction locale | **Modèles Argos** (exécutés par CTranslate2, quantifiés int8) par défaut. **NLLB-200 600M** en option pour les langues qu'Argos ne couvre pas | Q6 |
| 3 | Moteurs en ligne | **Yandex en premier** (ton préféré) : gratuit par la méthode du « widget » (celle de l'extension WordPress LocoAI) si elle fonctionne, ou par clé officielle. **Google gratuit sans compte** en second. DeepL, LibreTranslate, Google Cloud et Microsoft avec clé, en option | ✅ tranché |
| 4 | Interface | **PySide6 (Qt 6, Qt Widgets)** | — |
| 5 | Dépôt apt/dnf | Dépôt statique **signé GPG**, publié automatiquement sur **GitHub Pages** à chaque version | — |
| 6 | Ren'Py | **Système de traduction officiel de Ren'Py** (`game/tl/<langue>/`), généré si possible par le moteur du jeu lui-même. Sauvegarde et restauration systématiques. **Deux façons d'installer, au choix** : ajout d'une traduction, ou remplacement des textes d'origine (mode avancé) | Q12 |
| 7 | Langues turciques | **Turc, azéri, ouzbek, kazakh, turkmène, kirghiz, tatar, ouïghour** (8 langues ; 15 langues d'interface au total) | ✅ tranché |

---

## 2. Avis argumenté sur les 7 points de la section 13

### Point 1 : Python ou une alternative ?

**Verdict : Python, confirmé.**

Pourquoi :

- **Ren'Py est écrit en Python.** Les scripts compilés des jeux (`.rpyc`) sont des objets Python sérialisés (« pickles ») : seul Python sait les relire proprement. L'outil de référence, unrpyc, couvre Ren'Py 6.18 à 8. De plus, le moteur Ren'Py livré avec chaque jeu est lui-même un programme Python que RuneCast pourra piloter (voir point 6).
- **Traduction locale et OCR (phase 2)** : les briques sérieuses (CTranslate2, SentencePiece, moteurs OCR au format ONNX) ont des interfaces Python matures. Le calcul lourd est fait en C++ par ces bibliothèques : Python ne fait qu'orchestrer, donc la vitesse n'est pas un problème.
- **Un seul langage** pour tout le projet : plus simple à installer et à tester pour toi, plus simple à reprendre pour des contributeurs.

Pourquoi pas Tauri + Rust : les exécutables seraient plus légers et l'interface en technologies web, mais il faudrait **de toute façon** embarquer Python à côté (pour Ren'Py et les modèles). On aurait deux langages, deux chaînes d'outils et deux fois plus de sources de panne. Sous Linux, Tauri dépend en plus de WebKitGTK, dont la version varie selon les distributions.

Les vrais inconvénients de Python, et leurs parades :

| Inconvénient | Parade |
|---|---|
| Application plus volumineuse (ordre de grandeur 100 à 150 Mo installée, à mesurer) | Acceptable pour un logiciel de bureau. Les modèles de traduction sont téléchargés à part |
| Démarrage lent si tout est empaqueté dans un seul .exe qui se décompresse à chaque lancement | Distribution « en dossier » (voir Q7 pour la version portable) |
| Les .exe fabriqués par PyInstaller et non signés déclenchent parfois SmartScreen ou l'antivirus | Signature de code gratuite via le programme open source de la SignPath Foundation (étape 49) |
| L'interface peut se figer pendant les gros calculs | Traductions exécutées en arrière-plan : l'interface reste fluide |

Version : **Python 3.13**, installée par **uv** sur les deux machines (uv est dans les dépôts de Fedora 44 et s'installe en une commande sous Windows). On **ne touche pas** au Python du système Fedora 44 (3.14). Les bibliothèques clés (PySide6, CTranslate2) publient déjà des paquets pour 3.13 et 3.14 ; 3.13 est le choix le plus sûr pour l'ensemble de la chaîne, empaquetage compris.

### Point 2 : modèle de traduction local (8 Go de RAM, sans GPU)

Constat vérifié dans l'index officiel Argos (octobre 2026) : Argos propose des modèles **anglais ↔** français, espagnol, portugais (Portugal et Brésil), italien, arabe, turc, azéri, kirghiz, et une quarantaine d'autres langues. En revanche, **pas de kazakh, ni d'ouzbek, ni de turkmène.**

| Option | Couverture | Disque / RAM (ordre de grandeur, mesuré à l'étape 14) | Licence | Rôle proposé |
|---|---|---|---|---|
| **Argos Translate** (format CTranslate2, int8) | ~50 langues, en passant par l'anglais | ~100 Mo par sens de traduction / quelques centaines de Mo | Libres (affichées pour chaque modèle) | **Par défaut** |
| **NLLB-200 distillé 600M** (int8) | 200 langues, dont kazakh, ouzbek, turkmène, ouïghour, tatar, en traduction directe | ~600 Mo / ~1 à 1,5 Go | **CC-BY-NC 4.0** : usage non commercial ; Meta le présente comme un « modèle de recherche » | **Option**, téléchargée après acceptation explicite de la licence |
| OPUS-MT anglais → langues turciques | 24 variantes turciques | ~300 Mo | Apache 2.0 | Écarté : scores très faibles en ouzbek (BLEU 3,4), turkmène (5,9) et kazakh (11,1) |
| Petit modèle de langage local (Ollama, LM Studio) | Variable | 3 à 5 Go de RAM, lent sur CPU | Variable | Plus tard (v1.x), option avancée |

Choix technique important : **je n'utiliserai pas la bibliothèque Python `argostranslate` elle-même**, seulement ses **fichiers de modèles**, lus directement par CTranslate2 et SentencePiece. Raison : en version 1.10 (octobre 2025), elle dépend encore de Stanza, qui entraîne PyTorch, soit plusieurs centaines de Mo inutiles et beaucoup de RAM. Les répliques de jeux sont courtes : un découpage en phrases simple suffit.

**Embarqués ou téléchargés ? Téléchargés au premier usage**, uniquement pour les langues choisies (embarquer tous les modèles représenterait plusieurs Go). Avec : barre de progression, vérification d'empreinte SHA-256, reprise après coupure, suppression. Un **pack hors-ligne** pourra être importé (téléchargé sur un autre PC, copié par clé USB) pour les machines sans internet. Le catalogue des modèles est versionné et hébergé sur un dépôt GitHub dédié.

Limites à connaître :

- Argos passe par l'anglais pour les paires sans anglais (français → turc devient français → anglais → turc), ce qui baisse la qualité. Comme la grande majorité des jeux Ren'Py sont en anglais, le cas courant (anglais → X) est direct.
- Pour traduire un jeu **vers** le kazakh, l'ouzbek ou le turkmène en local, seul NLLB donne un résultat utilisable (voir Q6).
- La traduction automatique locale reste nettement en dessous d'un traducteur humain : l'éditeur intégré sert à corriger.

### Point 3 : accès à Yandex et moteurs alternatifs

**Méthode : l'API officielle Yandex Translate v2**, aujourd'hui rattachée à Yandex AI Studio, appelée par un petit client écrit dans RuneCast.

- Point d'accès : `translate.api.cloud.yandex.net/translate/v2/translate`, avec une clé API et un identifiant de dossier (folderId).
- Atouts utiles : mode HTML (aide à protéger les balises), glossaire natif (jusqu'à 50 paires par requête), jusqu'à 10 000 caractères par requête.
- Coût affiché : environ **4,10 $ HT par million de caractères**, sans offre gratuite mentionnée. Un gros jeu (environ 1 million de caractères) coûterait donc environ 4 $. RuneCast affichera une estimation avant de lancer la traduction.

Pourquoi pas la bibliothèque `deep-translator` : sa partie Yandex vise l'ancienne API v1.5, dont Yandex a arrêté les clés gratuites. Pour les autres moteurs, un client maison de quelques dizaines de lignes par moteur fait mieux (gestion fine des erreurs, des quotas et du repli).

**Trois réserves que je dois te signaler :**

1. **Ouverture d'un compte depuis la France incertaine.** Les clients hors de Russie sont facturés en dollars via des entités en Serbie ou à Dubaï, et la page « international » de Yandex ne proposait qu'un type de compte « Entreprise (non-résident) ». Je n'ai pas pu confirmer qu'un particulier français peut s'inscrire et payer.
2. **Contexte des sanctions européennes** sur les paiements liés à la Russie : à vérifier de ton côté (je ne suis pas juriste).
3. **Fiabilité actuelle** : selon Meduza (15 octobre 2026), des frappes de drones sur trois centres de données de Yandex (7 au 11 octobre) ont perturbé ses services cloud, et la page d'état de Yandex indiquait AI Studio indisponible. Je n'ai pas pu consulter cette page moi-même.

Conséquence : Yandex reste le **moteur par défaut du mode en ligne**, comme le demande le cahier des charges, et le **repli automatique** (vers le moteur suivant, puis vers le local) couvrira non seulement la coupure d'internet, mais aussi un service en panne, un blocage, un quota dépassé ou une clé refusée.

Moteurs alternatifs (tous par API officielle, clé saisie par l'utilisateur) :

| Moteur | Accès | Remarque |
|---|---|---|
| DeepL | API Free (quota mensuel gratuit, compte requis) ou Pro | Excellente qualité en langues européennes ; gère les balises |
| LibreTranslate | Adresse configurable (serveur personnel, ou instance publique avec clé) | Libre ; utilise la même famille de modèles qu'Argos |
| Google Cloud Translation | Clé Google Cloud (payant au-delà du quota gratuit) | Très large couverture, langues turciques comprises |
| Microsoft Translator | Clé Azure (palier gratuit) | Optionnel |

**Ta décision (18 octobre) : tous ces moteurs, plus deux accès gratuits sans compte.**

| Ordre par défaut | Moteur | Comment | Fiabilité |
|---|---|---|---|
| 1 | **Yandex gratuit** | Méthode du « widget de traduction de page » de Yandex, celle qu'utilise l'extension WordPress LocoAI (plus de 70 000 sites, mise à jour en octobre 2026). Testée à l'étape 16 | Non officielle : Yandex peut la modifier ou l'arrêter |
| 1 bis | **Yandex avec clé officielle** | Si une clé est saisie, elle passe avant la méthode gratuite | Fiable (payant) |
| 2 | **Google gratuit** | Comme sur le site Google Traduction, sans compte | Non officielle : a déjà cassé une fois chez d'autres logiciels, puis a été réparée |
| 3 | Moteurs avec clé (DeepL, Google Cloud, Microsoft, LibreTranslate) | Clé saisie dans Paramètres | Fiables |
| Dernier recours | **Traduction locale** | Sur le PC | Toujours disponible |

L'ordre sera réglable dans Paramètres. À savoir sur les accès gratuits :

- Le site de Yandex affiche aujourd'hui un captcha (« je ne suis pas un robot ») aux programmes : d'autres logiciels de traduction de jeux, comme Translumo, ont dû abandonner cette voie. C'est pour cela que je passerai par le widget, qui fonctionne encore.
- Yandex et Google ne prévoient pas ces accès pour un logiciel comme RuneCast (leurs API officielles sont faites pour cela) : ils peuvent s'arrêter ou bloquer du jour au lendemain. RuneCast le dira dans l'avertissement, et le repli automatique prendra le relais si l'un d'eux tombe.
- Si le widget ne peut fonctionner qu'avec un navigateur intégré (Qt WebEngine), cela ajouterait environ 150 à 200 Mo à l'application et quelques centaines de Mo de RAM pendant la traduction. J'essaierai d'abord sans.

Conception : tous les moteurs respectent le même « contrat » (langues disponibles lues en direct auprès du moteur, traduction par lots, limites de débit, glossaire natif ou non). Les clés sont rangées dans le **trousseau sécurisé du système** (Gestionnaire d'identification Windows ; GNOME Trousseau ou KWallet sous Linux), sauf en mode portable, où elles restent dans le dossier portable, avec un avertissement.

### Point 4 : framework d'interface

**Verdict : PySide6** (Qt 6, la bibliothèque officielle de Qt pour Python, licence LGPLv3 compatible GPLv3), avec **Qt Widgets**.

- **Thèmes** : les feuilles de style Qt (QSS, proches du CSS) sont générées à partir d'un fichier de thème JSON (couleurs, arrondis, polices). Les 4 thèmes intégrés et les thèmes personnels utilisent le même mécanisme ; l'éditeur de thème modifie ce fichier avec un aperçu en direct.
- **Multilingue** : système de traduction natif de Qt (fichiers `.ts` éditables avec Qt Linguist, compatibles avec les plateformes de traduction collaborative comme Weblate). Changement de langue sans redémarrer.
- **Arabe (RTL)** : Qt inverse automatiquement toute la mise en page (menus, tableaux, boîtes de dialogue) et gère la liaison des lettres arabes.
- **Polices embarquées** : Noto Sans (latin étendu et cyrillique : ə, ğ, ı, ş, ң, ү, ө, қ…) et Noto Sans Arabic, sous licence OFL. Même rendu sur Windows et Fedora, aucune case vide.
- **Gros volumes** : les tableaux Qt n'affichent que les lignes visibles, donc l'éditeur reste fluide même avec 50 000 répliques.
- **Fedora 44 fonctionne en Wayland uniquement par défaut** (X11 retiré de l'installation par défaut). Qt 6 y fonctionne nativement ; il faut juste un fichier `.desktop` bien relié pour que l'icône s'affiche dans le dock (prévu à l'étape 4).
- Conséquence de version : PySide6 6.12 (octobre 2026) exige sous Linux une glibc 2.34 ou plus récente. **Distributions minimales : Ubuntu 22.04, Debian 12, Linux Mint 21, Fedora 35, Mageia 9.** Debian 11 et Ubuntu 20.04 ne seront pas prises en charge.

Écartés : Tkinter (RTL et thèmes très limités), wxPython (thèmes limités), Dear PyGui (pas de RTL ni de liaison des lettres arabes), Flet/Flutter (couche supplémentaire, plus lourd), QML/Qt Quick (plus moderne visuellement, mais plus complexe pour un gain faible ici).

### Point 5 : dépôt apt/dnf signé GPG

Principe (comme pour Firefox ou Chrome) : un dépôt « statique », c'est-à-dire de simples fichiers sur un site web, que apt et dnf consultent. Les métadonnées sont **signées** avec une clé GPG RuneCast, ce qui évite tout avertissement de sécurité.

Déroulement d'une publication, entièrement automatique :

1. Tu crées une étiquette de version (par exemple `v1.0.0`) sur GitHub.
2. GitHub Actions construit les fichiers .exe, .deb, .rpm et AppImage.
3. Ils sont publiés dans GitHub Releases, avec leurs empreintes SHA-256 et leurs signatures.
4. Les dépôts apt et dnf sont régénérés, signés et publiés sur GitHub Pages.
5. Les utilisateurs .deb/.rpm reçoivent la mise à jour par leur gestionnaire de paquets habituel.

Détails :

- **Clé GPG** dédiée « RuneCast Repository », RSA 4096 bits (acceptée partout, y compris par les rpm anciens), valable 3 ans et renouvelable. Tu la crées toi-même sur Fedora, je te guiderai pas à pas, avec un certificat de révocation et une copie hors-ligne (clé USB). Elle est confiée à GitHub sous forme de « secret » chiffré pour signer automatiquement.
- **apt** (Debian, Ubuntu, Mint) : métadonnées générées par `apt-ftparchive`, fichier `InRelease` signé. Côté utilisateur, un fichier `runecast.sources` au format moderne avec `Signed-By` (et non `apt-key`, obsolète).
- **dnf** (Fedora, Mageia) : métadonnées `createrepo_c`, **chaque .rpm signé** ainsi que `repomd.xml`. Côté utilisateur, un fichier `runecast.repo` avec `gpgcheck=1` et `repo_gpgcheck=1`. Fedora 44 utilise dnf5, dont la commande d'ajout de dépôt diffère de dnf4 : install.sh gérera les deux.
- **openSUSE** utilise `zypper` et non dnf : même dépôt rpm, autre commande, gérée par install.sh.
- **Hébergement : GitHub Pages**, gratuit. Limites : site de 1 Go maximum et environ 100 Go de trafic par mois (limite souple). On conserve les 3 dernières versions dans le dépôt. Si RuneCast devient populaire, on bascule vers un CDN (Cloudflare R2, par exemple) en changeant seulement l'adresse ; un nom de domaine à toi faciliterait cette bascule (facultatif).
- Alternative étudiée : openSUSE Build Service (gratuit, signe pour toutes les distributions). Il impose un empaquetage « natif » par distribution, beaucoup plus complexe avec PySide6 et CTranslate2. Écarté pour la v1.

### Point 6 : module d'extraction et de traduction Ren'Py

Idée centrale : **utiliser le système de traduction officiel de Ren'Py.** Ren'Py sait charger des traductions rangées dans `game/tl/<langue>/` sans toucher aux scripts d'origine. C'est le format qu'utilisent les traducteurs humains, et il résiste aux mises à jour du jeu.

Chaîne de traitement :

1. **Détection du jeu** : dossier `game/`, version de Ren'Py (6, 7 ou 8 ; dernière version stable : 8.5.3), plateformes incluses (Windows, Linux), archives `.rpa`, présence de scripts sources `.rpy` ou seulement de scripts compilés `.rpyc`, traductions déjà présentes.
2. **Lecture des archives `.rpa`** en lecture seule (formats RPA-2.0, RPA-3.0 et variantes courantes), extraction vers un espace de travail RuneCast, **jamais dans le jeu**. Lecteur écrit dans RuneCast, avec une lecture **sécurisée** de l'index : l'index d'une archive est un « pickle » Python qui, mal lu, pourrait exécuter du code malveillant.
3. **Extraction des textes**, selon trois stratégies :
   - **A (préférée)** : faire générer **par le moteur Ren'Py du jeu lui-même** le modèle de traduction officiel. Les identifiants sont alors exacts, y compris pour les jeux livrés uniquement en `.rpyc`, et les textes de l'interface du moteur (Sauvegarder, Préférences…) sont inclus.
   - **B (repli)** : décompiler les `.rpyc` avec unrpyc et générer nous-mêmes les blocs de traduction.
   - **C (cas particulier)** : jeu Windows copié sous Fedora, sans moteur Linux dans son dossier. On télécharge une seule fois le SDK Ren'Py officiel de la même version, ou on utilise la stratégie B.

   L'étape 20 (expérimentation) validera A, B et C sur tes vrais jeux **avant** l'écriture du module définitif.
4. **Modèle interne unique** : chaque texte devient une « unité de traduction » (identifiant, fichier, ligne, personnage, type : dialogue, menu, interface ou description, texte source, traduction, statut). Les trois modes de travail, le cache, le glossaire, et plus tard l'OCR et les plugins, manipulent tous ce même objet.
5. **Protection des balises et des variables** avant l'envoi au moteur, puis restauration et contrôle. Sont protégés : les balises Ren'Py `{b}`, `{i}`, `{u}`, `{s}`, `{color=…}`, `{size=…}`, `{font=…}`, `{a=…}`, `{w}`, `{p}`, `{nw}`, `{fast}`, `{cps=…}`, `{image=…}`, `{rb}`/`{rt}`… ; les interpolations `[nom]`, `[nom!t]`, `[objet.attribut]` ; les échappements `{{`, `[[`, `%%`, `\n` ; les formats Python `%s`, `%(nom)s`, `{0}`. Toute ligne dont la restauration échoue est marquée « à vérifier » au lieu d'être écrite.
6. **Polices et sens d'écriture dans le jeu** : beaucoup de jeux utilisent une police sans cyrillique ni arabe, ce qui donne des carrés vides. Le fichier d'activation de la langue ajoute une police de remplacement (Noto) pour la langue cible et active le mode droite-à-gauche de Ren'Py pour l'arabe (à valider sur tes jeux).
7. **Sortie** (les deux modes du cahier des charges) :
   - **Patch séparé** : dossier ou zip contenant `tl/<langue>/`, un petit fichier d'activation de la langue et un LISEZMOI. Il suffit de le copier dans `game/`.
   - **Installation directe, au choix de l'utilisateur** (ta décision du 18 octobre) :
     - *Ajout d'une traduction* (recommandé) : les mêmes fichiers sont écrits dans le jeu, **après sauvegarde automatique** de tout fichier qui serait écrasé ; les scripts d'origine ne sont pas modifiés. « Restaurer » supprime ce que RuneCast a ajouté et remet les originaux.
     - *Remplacement des textes d'origine* (mode avancé) : les textes sont remplacés directement dans les scripts du jeu, après sauvegarde complète. Plus risqué, car un script décompilé n'est pas toujours fidèle : RuneCast l'indique clairement avant de lancer, et « Restaurer » remet le jeu exactement comme avant.
8. **Sauvegarde et restauration** : avant toute écriture, les originaux sont copiés dans le dossier de données RuneCast avec un manifeste (chemin, taille, empreinte SHA-256). La copie est vérifiée, et seulement ensuite le jeu est modifié. La restauration revérifie les empreintes. L'espace disque est contrôlé avant la sauvegarde.
9. **Limites** : certains jeux chiffrent ou modifient leurs archives (formats maison) ou leur chargeur de scripts. RuneCast les détectera et le dira clairement, plutôt que de produire une traduction cassée.

Des outils proches existent (par exemple RenLocalizer ou renpy-translator-gui). J'ai regardé leurs approches, mais RuneCast ne reprend pas leur code.

### Point 7 : liste exacte des langues turciques de l'interface

| Langue | Nom natif | Code | Écriture proposée | Sens | Remarque |
|---|---|---|---|---|---|
| Turc | Türkçe | tr | latine | gauche → droite | |
| Azéri | Azərbaycan dili | az | latine | gauche → droite | Azéri d'Azerbaïdjan ; l'azéri d'Iran s'écrit en alphabet arabe |
| Ouzbek | Oʻzbekcha | uz | latine | gauche → droite | Écriture officielle ; le cyrillique reste très répandu |
| Kazakh | Қазақша | kk | **cyrillique** | gauche → droite | Passage au latin annoncé, toujours sans calendrier (septembre 2026). Variante latine ajoutable plus tard |
| Turkmène | Türkmençe | tk | latine | gauche → droite | |
| Kirghiz | Кыргызча | ky | cyrillique | gauche → droite | |
| Tatar | Татарча | tt | cyrillique | gauche → droite | Ajouté le 18 octobre |
| Ouïghour | ئۇيغۇرچە | ug | arabe | **droite → gauche** | Ajouté le 18 octobre ; réutilise le support RTL de l'arabe |

Interface : **15 langues** (8 turciques, plus arabe, français, anglais, espagnol, portugais et italien). Deux s'écrivent de droite à gauche : l'arabe et l'ouïghour.

Je peux produire les traductions de l'interface et des pages légales dans toutes ces langues. Pour le turkmène, le kirghiz, le kazakh, l'ouzbek, le tatar et l'ouïghour, une **relecture par un locuteur natif** est vivement recommandée avant la v1.0. Une plateforme comme Weblate (gratuite pour les projets libres) permettra ensuite à la communauté de corriger.

---

## 3. Architecture évolutive (phases 2, 3 et 4)

Organisation du code en couches (dans `src/runecast/`) :

| Couche | Contenu | Dépend de Qt ? |
|---|---|---|
| `core` | Unités de traduction, glossaires, cache, protection des balises, sauvegardes, configuration | Non |
| `engines` | Moteurs de traduction (local, Yandex, DeepL…) | Non |
| `formats` | Lecteurs et écrivains de jeux. **Ren'Py est le premier « format »** | Non |
| `platform` | Dossiers système, mises à jour, trousseau, détection du réseau | Non |
| `ui` | Fenêtres, thèmes, langues de l'interface | Oui |

- **Phase 2 (OCR et overlay)** : ajout d'une « source de texte » (capture d'écran + OCR) et d'une « sortie d'affichage » (overlay ou fenêtre flottante), qui produisent et consomment les mêmes unités de traduction. Point de vigilance noté dès maintenant : sous Wayland (Fedora 44), les fenêtres « toujours au premier plan » et la capture d'écran sont volontairement restreintes ; il faudra passer par les portails du système. Rien à faire en v1.
- **Phase 3 (plugins)** : un plugin est un nouveau « format » (Unity, RPG Maker…) qui respecte le même contrat que le module Ren'Py. Le module Ren'Py est construit dès la v1 comme s'il était un plugin.
- **Phase 4 (jeux en ligne)** : même logique (source = chat, affichage = fenêtre flottante).
- La logique (`core`, `engines`, `formats`) ne dépend pas de l'interface : elle est testable automatiquement et pourra aussi servir en ligne de commande.

Emplacement des données :

| Données | Windows | Linux | Mode portable |
|---|---|---|---|
| Configuration, thèmes, glossaires, profils de jeux | `%APPDATA%\RuneCast` | `~/.config/runecast` | `RuneCast-Portable\data\` |
| Modèles, cache, historique, sauvegardes des jeux (volumineux) | `%LOCALAPPDATA%\RuneCast` | `~/.local/share/runecast` | `RuneCast-Portable\data\` |

Le cahier des charges mentionne `~/.config`. Je propose de suivre la norme Linux (XDG), qui range les gros fichiers (modèles de plusieurs centaines de Mo) dans `~/.local/share` (Q11). Les installeurs et les mises à jour ne touchent **jamais** ces dossiers. Chaque fichier de données porte un numéro de version pour pouvoir le migrer sans perte.

**Mode local, tel que tu l'as précisé** : au premier lancement, RuneCast demande si l'on veut traduire avec internet ou en local (modifiable ensuite dans Paramètres). En mode local, **aucune phrase n'est envoyée à un service de traduction** : tout est traduit sur le PC. Internet reste utilisé pour le reste : mises à jour de RuneCast et téléchargement des modèles de traduction. En mode en ligne, RuneCast envoie les phrases au moteur choisi (Yandex, Google…).

---

## 4. Liste complète des dépendances

### 4.1 À installer sur ton PC Windows 10 (développement)

| Outil | Utilité | À partir de l'étape |
|---|---|---|
| Git for Windows | Historique du code, envoi vers GitHub | 1 |
| uv | Installe Python 3.13 et toutes les bibliothèques, sans toucher au système | 1 |
| Visual Studio Code (recommandé) | Éditeur de code | 1 |
| Compte GitHub | Hébergement du code | 1 |
| Inno Setup 6 | Fabrication de RuneCast-Setup.exe pour tes tests (la version officielle est construite par GitHub) | 36 |

Pas besoin d'installer Python à la main : uv s'en charge.

### 4.2 À installer sur ton PC Fedora 44 (développement)

| Paquet(s) | Utilité | À partir de l'étape |
|---|---|---|
| `git`, `uv` | Comme sous Windows (uv est dans les dépôts Fedora 44) | 1 |
| VS Code (dépôt Microsoft) ou un autre éditeur | Édition du code | 1 |
| `xcb-util-cursor` | Bibliothèque exigée par Qt 6 en mode X11/XWayland | 4 |
| `distrobox` et/ou GNOME Boxes | Tester .deb et AppImage sur Ubuntu, Mint ou Debian sans autre PC | 39 |
| `dpkg` (facultatif) | Inspecter les .deb depuis Fedora | 39 |
| `gnupg2`, `rpm-sign`, `createrepo_c` | Clé GPG, signature et test du dépôt | 43 |

Les commandes exactes seront données à chaque étape.

### 4.3 Bibliothèques Python (embarquées dans RuneCast : rien à installer pour l'utilisateur)

| Bibliothèque | Rôle | Licence | Étape |
|---|---|---|---|
| PySide6-Essentials | Interface Qt 6 (version allégée, sans modules inutiles) | LGPLv3 | 4 |
| PySide6-Addons (Qt WebEngine), **seulement si nécessaire** | Navigateur intégré, au cas où le widget Yandex gratuit l'exigerait | LGPLv3 | 16 |
| platformdirs | Bons dossiers de données selon le système | MIT | 6 |
| httpx | Échanges réseau (moteurs en ligne, modèles, mises à jour) | BSD | 13 |
| ctranslate2 | Exécution des modèles locaux sur CPU (int8) | MIT | 13 |
| sentencepiece | Découpage du texte pour les modèles | Apache 2.0 | 13 |
| psutil | Mesure de la RAM et du CPU (choix du modèle, nombre de cœurs) | BSD | 13 |
| keyring | Rangement sécurisé des clés API | MIT | 16 |
| unrpyc (copié dans le code source, licence conservée) | Décompilation des `.rpyc` (stratégie B) | MIT, revérifiée lors de l'intégration | 24 |
| cryptography | Vérification de la signature des mises à jour | Apache 2.0 / BSD | 46 |
| packaging | Comparaison des numéros de version | Apache 2.0 / BSD | 46 |

Bibliothèque standard de Python (déjà incluse) : sqlite3 (cache, historique), json, zipfile, zlib, hashlib, logging.

Outils de développement (non livrés aux utilisateurs) : pytest et pytest-qt (tests automatiques), ruff (qualité et mise en forme du code), PyInstaller (fabrication des exécutables), outils de traduction Qt lupdate et lrelease (fournis avec PySide6).

Toutes ces licences sont compatibles avec la GPLv3.

### 4.4 Outils de fabrication (exécutés automatiquement par GitHub Actions)

Inno Setup (installeur Windows), PyInstaller, nfpm (.deb et .rpm), appimagetool avec le nouveau runtime AppImage, apt-ftparchive, createrepo_c, rpmsign, GnuPG. La version Linux est construite dans un conteneur à glibc 2.34–2.35, pour rester compatible avec les distributions un peu anciennes.

### 4.5 Ce que l'utilisateur final doit avoir

| Plateforme | Prérequis |
|---|---|
| Windows 10 (22H2) ou 11, 64 bits | Rien |
| Fedora, Mageia (.rpm) | Bibliothèques graphiques standard (Mesa/OpenGL, fontconfig, freetype, libxkbcommon, xcb-util-cursor, D-Bus). Déclarées par nom de bibliothèque (« soname ») dans le .rpm : dnf les installe automatiquement, quel que soit le nom du paquet dans la distribution |
| openSUSE (.rpm via zypper) | Comme Fedora |
| Debian, Ubuntu, Mint (.deb) | `libgl1`, `libegl1`, `libfontconfig1`, `libfreetype6`, `libxkbcommon0`, `libxkbcommon-x11-0`, `libxcb-cursor0`, les bibliothèques `libxcb-*` utilisées par Qt, `libdbus-1-3`. Installées automatiquement par apt ; liste exacte figée à l'étape 39 |
| AppImage (toute distribution x86_64 récente) | FUSE 3, présent par défaut presque partout. Le nouveau runtime AppImage n'exige plus libfuse2 ; à défaut de FUSE, lancement possible avec `--appimage-extract-and-run`. install.sh vérifie et propose l'installation |
| Code source | Git et uv (procédure documentée, identique sous Windows et Linux) |
| Facultatif sous Linux | Un trousseau (GNOME Keyring ou KWallet) pour les clés API ; sinon stockage local avec avertissement |
| Matériel | 8 Go de RAM, processeur 64 bits, pas de GPU. Disque : environ 300 Mo pour l'application, plus les modèles choisis |

Distributions minimales : glibc 2.34 ou plus récente (voir point 4).
Internet n'est nécessaire que pour le mode en ligne, le téléchargement des modèles et les mises à jour.

---

## 5. Plan de développement (51 étapes)

Règles appliquées à **chaque** étape :

- une seule étape à la fois ;
- je fournis le code complet des fichiers créés ou modifiés, les commandes de test pour **Windows 10 et Fedora 44**, la liste des points à vérifier et les nouvelles dépendances avec leur utilité ;
- tu testes sur une **copie** de jeu, jamais sur ton seul exemplaire ;
- un **commit git** est créé à chaque étape validée ;
- j'attends ton « OK étape X » avant de continuer.

La dernière colonne renvoie aux sections de ta checklist (document 2).

### Jalon 1 : démarrage (étapes 1 à 5)

| N° | Étape | Ce que tu pourras vérifier | Checklist |
|---|---|---|---|
| 1 | Préparer les deux PC (Git, uv, Python 3.13, éditeur) et créer le dépôt public `davidharputoglu/RuneCast` (dossier principal : `C:\ai\RuneCast`) | `git --version` et `uv run python --version` (3.13) répondent sur les deux PC ; dépôt visible sur GitHub | B |
| 2 | Squelette du projet : LICENSE GPLv3, README avec la structure des dossiers, configuration, en-tête GPL type, premier test automatique | `uv run pytest` réussit sur les deux PC ; LICENSE visible sur GitHub | B |
| 3 | Logo → icônes : ton image **sans retouche**, découpée en carré autour de l'hexagone puis réduite. .ico Windows (16 à 256 px), PNG Linux (16 à 512 px), favicon | Icônes identiques à l'aperçu du 18 octobre | B |
| 4 | Première fenêtre : icône, thème turquoise de base, menu Aide → À propos (crédits, e-mail, version, GPLv3) | Se lance sur Windows 10 et Fedora 44 (Wayland) ; icône dans la barre des tâches et le dock | E |
| 5 | Tests automatiques sur GitHub (Windows et Linux) à chaque envoi de code | Coche verte sur GitHub | A |

### Jalon 2 : socle de l'application (étapes 6 à 10)

| N° | Étape | Ce que tu pourras vérifier | Checklist |
|---|---|---|---|
| 6 | Dossiers de données, configuration versionnée, mode portable, journal (logs) | Fichiers créés aux bons endroits ; en mode portable, tout est écrit à côté de l'exécutable | — |
| 7 | Langues de l'interface : mécanisme, français, anglais, arabe d'essai (RTL), polices Noto | Bascule FR/EN sans redémarrer ; l'arabe s'affiche en miroir | E |
| 8 | Les 4 thèmes intégrés, Turquoise par défaut | Turquoise au premier lancement ; bascule vers Noir, Sombre, Clair | E |
| 9 | Éditeur de thèmes personnels : créer, enregistrer, recharger, importer, exporter | Thème personnel conservé après redémarrage | E |
| 10 | Fenêtre principale complète : vrais menus et boîte Paramètres ; tout élément visible fonctionne | Aucun bouton ni menu factice | E |

### Jalon 3 : traduction (étapes 11 à 19)

| N° | Étape | Ce que tu pourras vérifier | Checklist |
|---|---|---|---|
| 11 | Protection des balises et variables Ren'Py (masquage, restauration, contrôle), avec une centaine de cas de test | Tests réussis ; démonstration en ligne de commande | D |
| 12 | Cache et historique des traductions (SQLite) | Une phrase identique n'est pas retraduite (visible dans le journal) | D |
| 13 | Moteur local : modèles Argos via CTranslate2, gestionnaire de modèles (catalogue, téléchargement, SHA-256, suppression, pack hors-ligne) | Traduction anglais → français avec le Wi-Fi coupé | D |
| 14 | Banc d'essai sur tes deux PC : vitesse et RAM ; réglages par défaut (cœurs, taille des lots) | Chiffres mesurés ; RAM stable | D |
| 15 | *(si Q6 = oui)* Modèle étendu NLLB-200, avec acceptation de la licence | Traduction anglais → kazakh en local | D |
| 16 | Moteurs en ligne : Yandex gratuit (widget) et Yandex avec clé, Google gratuit, DeepL, LibreTranslate, Google Cloud, Microsoft ; ordre réglable ; clés dans le trousseau ; bouton « Tester » ; estimation du coût pour les moteurs payants | Test réel de Yandex et de Google gratuit, et d'au moins un moteur avec clé | D |
| 17 | Repli automatique (moteur suivant, puis local) et mode local | Wi-Fi coupé en pleine traduction : ça continue en local. En mode local, aucune connexion vers un service de traduction (seuls les mises à jour et les modèles utilisent internet) | D |
| 18 | Glossaires par jeu : tableau éditable, import/export CSV, application forcée et rapport de contrôle | Un terme imposé est identique partout | D |
| 19 | Assistant de premier lancement (langue, thème, en ligne ou local, modèle) | Apparaît sur un profil vierge ; les choix restent modifiables dans Paramètres | E |

### Jalon 4 : cœur Ren'Py (étapes 20 à 27)

| N° | Étape | Ce que tu pourras vérifier | Checklist |
|---|---|---|---|
| 20 | Expérimentation sur tes jeux de test, sans interface : versions, archives, jeux en `.rpyc` seuls, génération par le moteur du jeu. Rapport et choix final entre les stratégies A, B, C | Rapport relu ensemble | C |
| 21 | Détection et analyse d'un jeu, création de son profil | Informations correctes sur tes jeux, sur les deux PC | C |
| 22 | Sauvegarde et restauration (manifeste SHA-256), avant toute écriture | Modification puis restauration : empreintes identiques à l'original | C |
| 23 | Lecture des archives `.rpa` (lecture seule) | Extraction réussie sur un jeu sous Fedora et sur un jeu sous Windows | C |
| 24 | Extraction des textes : dialogues, menus, interface, textes du moteur | Comptes et exemples cohérents ; menus bien détectés | C |
| 25 | Écriture de `tl/<langue>`, activation de la langue, polices et RTL ; installation directe et désinstallation | Le jeu se lance traduit sur les deux PC ; la restauration fonctionne | C |
| 26 | Export « patch séparé » (zip + LISEZMOI) | Patch installé à la main sur une copie propre : il fonctionne | C |
| 27 | Mode avancé : remplacement des textes d'origine dans les scripts du jeu (après sauvegarde complète) | Jeu traduit, puis restauration identique à l'original | C |

### Jalon 5 : modes de travail (étapes 28 à 32)

| N° | Étape | Ce que tu pourras vérifier | Checklist |
|---|---|---|---|
| 28 | Bibliothèque de jeux (un profil par jeu) | Ajouter, retirer et rouvrir un jeu | C |
| 29 | Mode 1 : éditeur intégré avec prévisualisation, puis application | Une ligne corrigée apparaît corrigée dans le jeu | C |
| 30 | Mode 2 : traduction entièrement automatique (progression, pause, reprise, annulation, temps restant) | Jeu complet traduit ; interface jamais figée ; RAM stable | C, D |
| 31 | Mode 3 : édition a posteriori de traductions existantes (y compris faites par d'autres outils) | Rouvrir, modifier, réappliquer | C |
| 32 | Export et import des configurations, glossaires et profils | Export sous Windows, puis import sous Fedora | H |

### Jalon 6 : langues et pages légales (étapes 33 et 34)

| N° | Étape | Ce que tu pourras vérifier | Checklist |
|---|---|---|---|
| 33 | Traduction complète de l'interface dans les 15 langues | Toutes les langues basculent ; en arabe, aucun texte tronqué ni inversé | E |
| 34 | Pages Avertissement, À propos, Licence, Crédits dans toutes les langues. Pour la Licence : résumé traduit + texte officiel anglais de la GPLv3 (seule version juridiquement valable) | Pages présentes dans chaque langue ; crédits et e-mail visibles | E |

### Jalon 7 : paquets Windows (étapes 35 à 37)

| N° | Étape | Ce que tu pourras vérifier | Checklist |
|---|---|---|---|
| 35 | Exécutable Windows (PyInstaller, format dossier) | Se lance sur un Windows 10 sans Python (machine virtuelle ou Bac à sable Windows) | F |
| 36 | RuneCast-Setup.exe (Inno Setup) : installation pour l'utilisateur sans droits administrateur, raccourcis, désinstallation qui conserve tes données | Installer, lancer, désinstaller : les données restent intactes | F |
| 37 | RuneCast-Portable.exe | Fonctionne depuis une clé USB, sans installation, données à côté | F |

### Jalon 8 : paquets Linux (étapes 38 à 41)

| N° | Étape | Ce que tu pourras vérifier | Checklist |
|---|---|---|---|
| 38 | Exécutable Linux et paquet .rpm | Installation du fichier avec dnf sur Fedora 44 ; entrée de menu et icône | F |
| 39 | Paquet .deb | Installation avec apt sur Mint ou Ubuntu (machine virtuelle ou distrobox) | F |
| 40 | AppImage | Se lance sur Fedora 44 et sur au moins une autre distribution | F |
| 41 | *(si Q8 = oui)* Paquets ARM64 | Construits par GitHub (non testables sur tes PC) | F |

### Jalon 9 : publication et mises à jour (étapes 42 à 48)

| N° | Étape | Ce que tu pourras vérifier | Checklist |
|---|---|---|---|
| 42 | Publication automatique : une étiquette de version produit tous les fichiers, empreintes et signatures dans GitHub Releases | Version de test publiée avec tous ses fichiers | G |
| 43 | Clé GPG (tu la crées, je te guide) et dépôts apt et dnf sur GitHub Pages | Après ajout du dépôt sur Fedora, `dnf install runecast` sans avertissement ; idem avec apt sur Mint (machine virtuelle) | G |
| 44 | Mises à jour système : publication d'une fausse version 1.0.1 | `dnf upgrade` et `apt upgrade` la récupèrent | G |
| 45 | install.sh : détection de la distribution, de l'architecture et des dépendances manquantes ; choix du format ; ajout du dépôt | Cas testés : Fedora, Mint, distribution inconnue, ARM | F |
| 46 | Mise à jour intégrée Windows (Setup et portable) : téléchargement en arrière-plan, vérification de signature, installation silencieuse | Passage 1.0 → 1.1 de test sans intervention (ou une simple confirmation si droits administrateur) | G |
| 47 | Mise à jour intégrée de l'AppImage | Même test | G |
| 48 | Conservation des données après mise à jour (migrations) | Thèmes, glossaires et profils intacts | G |

### Jalon 10 : finalisation (étapes 49 à 51)

| N° | Étape | Ce que tu pourras vérifier | Checklist |
|---|---|---|---|
| 49 | *(facultatif, en parallèle)* Candidature SignPath pour signer l'exécutable Windows | Plus d'alerte SmartScreen « éditeur inconnu » | H |
| 50 | Documentation : README complet, guide utilisateur FR/EN, guide de contribution, installation depuis les sources | Procédure « depuis les sources » testée sur les deux PC | H |
| 51 | Recette finale v1.0 : test de bout en bout, RAM, console propre, en-têtes GPL vérifiés automatiquement, restauration ; publication de la v1.0.0 | Toutes les cases de la section H cochées | H |

---

## 6. Questions

### Tranchées le 18 octobre

| Q | Sujet | Ta réponse |
|---|---|---|
| Q1 | Moteurs en ligne | Tous : Yandex gratuit (essai par le widget) et Yandex avec clé, Google gratuit, et les moteurs avec clé. Yandex en premier |
| Q2 | Installation directe dans le jeu | Les deux façons, au choix de l'utilisateur ; le remplacement des textes d'origine est marqué « avancé » |
| Q3 | Langues turciques | Les 8 : turc, azéri, ouzbek, kazakh, turkmène, kirghiz, tatar, ouïghour |
| Q5 | Mode local | Local = aucune traduction par internet ; les mises à jour et les modèles peuvent utiliser internet |
| Q9 | GitHub | Dépôt public `davidharputoglu/RuneCast`, dossier principal `C:\ai\RuneCast` |
| Q10 | Icône | Ton image sans retouche : découpe carrée autour de l'hexagone, puis réduction aux tailles standard |

**Ajustement de ta checklist (section D)** suite à ta réponse Q5 : la case « En mode local : aucune connexion réseau sortante » devient « En mode local : aucune phrase envoyée à un service de traduction ».

### À poser plus tard, une par une, quand on arrivera à l'étape

| Q | Question (en clair) | Ma proposition | Étape |
|---|---|---|---|
| Q11 | Linux : ranger les gros fichiers (modèles, sauvegardes) dans `~/.local/share/runecast` et les réglages dans `~/.config/runecast` ? | Oui | 6 |
| Q6 | Proposer le modèle NLLB-200 (licence non commerciale) en téléchargement optionnel, pour le kazakh, l'ouzbek et le turkmène en local ? | Oui, avec écran d'acceptation | 15 |
| Q12 | Quels jeux Ren'Py utiliser pour les tests ? | 2 ou 3 jeux : un ancien, un récent (Doki Doki Literature Club est gratuit sur Steam) | 20 |
| Q4 | Portugais du Portugal ou du Brésil ? Espagnol d'Espagne ou d'Amérique latine ? | Brésil ; Espagne | 33 |
| Q7 | Version portable Windows : se décompresse une seule fois dans un dossier (rapide) ou à chaque lancement (lent) ? | Une seule fois | 37 |
| Q8 | Linux sur processeur ARM : paquets dédiés, ou installation depuis les sources ? | Depuis les sources en v1 | 41 |

**À préparer dès maintenant** : des copies de 2 ou 3 jeux Ren'Py, pour l'étape 20.

---

## 7. Sources (consultées le 18 octobre 2026)

- Yandex Translate, tarifs : https://aistudio.yandex.ru/en/docs/ai-studio/pricing
- Yandex Translate, référence de l'API v2 : https://aistudio.yandex.ru/en/docs/translate/api-ref/Translation/translate
- Yandex Cloud pour les clients internationaux : https://cloud.yandex.ru/promo/for-international-companies/
- Arrêt des clés gratuites de l'ancienne API Yandex (Habr Q&A) : https://qna.habr.com/q/876847
- Meduza, frappes sur les centres de données de Yandex (15 oct. 2026) : https://meduza.io/en/feature/2026/10/15/ukrainian-strikes-on-yandex-s-data-centers-could-set-back-russia-s-ai-development-by-years-never-a-rival-to-the-u-s-or-china-in-ai-russia-may-now-fall-behind-kazakhstan-too
- Index des modèles Argos : https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json
- Argos Translate : https://github.com/argosopentech/argos-translate
- Argos Translate 1.10 (Stanza toujours présent) : https://community.libretranslate.com/t/argos-translate-1-10/1977
- NLLB-200 distillé 600M, fiche et licence : https://huggingface.co/facebook/nllb-200-distilled-600M/blob/main/README.md
- OPUS-MT anglais → langues turciques : https://huggingface.co/Helsinki-NLP/opus-mt-en-trk
- CTranslate2 (versions et paquets) : https://simple-repository.app.cern.ch/project/ctranslate2
- PySide6 (versions, glibc requise) : https://simple-repository.app.cern.ch/project/pyside6
- Fedora 44 (Python 3.14, GNOME 50, Wayland par défaut) : https://fale.io/blog/2026/04/30/fedora-44-released
- uv dans Fedora 44 : https://linuxsecurity.com/advisories/fedora/fedora-44-uv-2026-407b957a3b
- Ren'Py (dernière version stable) : https://en.wikipedia.org/wiki/Ren%27Py
- unrpyc : https://gittrend.io/repo/CensoredUsername/unrpyc
- Nouveau runtime AppImage et libfuse : https://lists.cinelerra-gg.org/pipermail/cin/2024-October/008890.html
- Limites de GitHub Pages : https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
- Dépôts apt et dnf sur GitHub Pages (retour d'expérience) : https://blog.thestateofme.com/2026/02/27/publishing-apt-and-yum-dnf-repos-on-github-pages/
- SignPath, signature de code gratuite pour l'open source : https://about.signpath.io/product/open-source
- Kazakh, transition vers l'alphabet latin : https://hronika.kz/?p=18619
- Outils existants : https://github.com/AnwarAllal23/renpy-translator-gui et https://lordofturk.itch.io/renlocalizer/devlog
- LocoAI (traduction gratuite Yandex par widget, WordPress) : https://wordpress.org/plugins/automatic-translator-addon-for-loco-translate/
- Translumo, passage de Yandex à l'API officielle (captcha) : https://github.com/ramjke/Translumo/releases
