# SPDX-License-Identifier: GPL-3.0-or-later
#
# RuneCast — traduction de jeux vidéo / video game translation
# Copyright (C) 2026 HARPUTOGLU David
# Créé par HARPUTOGLU David, aidé par l'IA / Created by HARPUTOGLU David, assisted by AI
# Contact : kasparof57@gmail.com
#
# FR : Ce programme est un logiciel libre : vous pouvez le redistribuer et/ou
#      le modifier selon les termes de la Licence publique générale GNU (GNU GPL)
#      telle que publiée par la Free Software Foundation, soit la version 3 de
#      la licence, soit (à votre choix) toute version ultérieure.
#      Ce programme est distribué dans l'espoir qu'il sera utile, mais SANS
#      AUCUNE GARANTIE, sans même la garantie implicite de QUALITÉ MARCHANDE ou
#      d'ADÉQUATION À UN USAGE PARTICULIER. Voir la GNU GPL pour plus de détails.
#      Vous devriez avoir reçu une copie de la GNU GPL avec ce programme
#      (fichier LICENSE). Sinon, voir <https://www.gnu.org/licenses/>.
#
# EN : This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#      GNU General Public License for more details.
#      You should have received a copy of the GNU General Public License
#      along with this program (LICENSE file). If not, see <https://www.gnu.org/licenses/>.

"""Changement de langue de l'interface / Interface language switching.

FR : Charge les traductions de RuneCast et celles de Qt (boutons « Oui »,
     « Annuler », fenêtres de choix de dossier…), règle le sens d'écriture
     (de droite à gauche pour l'arabe) et prévient toutes les fenêtres, qui se
     traduisent aussitôt, sans redémarrer.

EN : Loads the RuneCast translations and Qt's own ones ("Yes", "Cancel"
     buttons, folder selection windows…), sets the writing direction
     (right-to-left for Arabic) and notifies every window, which translates
     itself immediately, without restarting.
"""

import logging

from PySide6.QtCore import QCoreApplication, QEvent, QLibraryInfo, QLocale, Qt, QTranslator
from PySide6.QtWidgets import QApplication

from runecast.core.languages import LANGUAGES, SOURCE_LANGUAGE
from runecast.resources import resource_path

logger = logging.getLogger(__name__)


def keep_left_to_right(text: object) -> str:
    """Garde un chemin ou une adresse lisible dans une phrase arabe / Keep paths readable.

    FR : Dans une phrase écrite de droite à gauche (arabe, ouïghour), un chemin
         comme « C:\\Jeux\\RuneCast » ou une adresse e-mail serait affiché dans
         le désordre. Les caractères Unicode « isolement gauche-à-droite »
         (U+2066 … U+2069) l'affichent correctement, dans toutes les langues.
    EN : In a right-to-left sentence (Arabic, Uyghur), a path such as
         "C:\\Games\\RuneCast" or an e-mail address would be displayed out of
         order. The Unicode "left-to-right isolate" characters (U+2066 … U+2069)
         display it correctly, in every language.
    """
    return f"\u2066{text}\u2069"


def translation_file(code: str) -> str:
    """FR : fichier de traduction compilé de RuneCast pour une langue.

    EN : RuneCast compiled translation file for a language.
    """
    return str(resource_path("translations", f"runecast_{code}.qm"))


class LanguageManager:
    """Gère la langue de l'interface / Manages the interface language."""

    def __init__(self, app: QApplication) -> None:
        self.app = app
        self.current = SOURCE_LANGUAGE
        self._translators: list[QTranslator] = []

    def apply(self, code: str) -> None:
        """Passe l'interface dans la langue « code » / Switch the interface to "code"."""
        language = LANGUAGES[code]

        # FR : 1. On retire les traductions précédentes.
        # EN : 1. Remove the previous translations.
        for translator in self._translators:
            self.app.removeTranslator(translator)
        self._translators.clear()

        # FR : 2. Traductions de Qt lui-même (boutons standard, etc.).
        # EN : 2. Qt's own translations (standard buttons, etc.).
        qt_folder = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
        self._load(f"qtbase_{code}", qt_folder)

        # FR : 3. Traductions de RuneCast (sauf en français, la langue du code).
        # EN : 3. RuneCast translations (except French, the code's language).
        if code != SOURCE_LANGUAGE:
            self._load_file(translation_file(code))

        # FR : 4. Sens d'écriture et format des nombres et dates.
        # EN : 4. Writing direction and number and date format.
        direction = (
            Qt.LayoutDirection.RightToLeft
            if language.right_to_left
            else Qt.LayoutDirection.LeftToRight
        )
        self.app.setLayoutDirection(direction)
        QLocale.setDefault(QLocale(code))

        # FR : 5. Qt prévient les fenêtres par un message « la langue a changé » ;
        #      on le délivre tout de suite pour que l'affichage suive aussitôt.
        # EN : 5. Qt notifies windows with a "language changed" message; deliver
        #      it right away so that the display follows immediately.
        QCoreApplication.sendPostedEvents(None, QEvent.Type.LanguageChange)
        self.current = code
        logger.info("Langue de l'interface / Interface language: %s", code)

    def _load(self, name: str, folder: str) -> None:
        """FR : charge une traduction de Qt si elle existe. EN : load a Qt translation."""
        translator = QTranslator(self.app)
        if translator.load(name, folder):
            self.app.installTranslator(translator)
            self._translators.append(translator)

    def _load_file(self, path: str) -> None:
        """FR : charge un fichier de traduction de RuneCast. EN : load a RuneCast file."""
        translator = QTranslator(self.app)
        if translator.load(path):
            self.app.installTranslator(translator)
            self._translators.append(translator)
        else:
            logger.error("Traduction introuvable / Translation not found: %s", path)
