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

"""Polices embarquées / Bundled fonts.

FR : RuneCast embarque ses propres polices, Noto Sans et Noto Sans Arabic
     (licence libre SIL Open Font License, fichiers OFL-*.txt). Elles
     contiennent toutes les lettres des langues de l'interface : latin
     étendu (ə, ğ, ı, ş, ň…), cyrillique (қ, ң, ү, ө…) et arabe (y compris
     les lettres ouïghoures). Ainsi, l'interface est identique sous Windows et
     sous Linux, et aucune lettre ne s'affiche en carré vide.

EN : RuneCast ships its own fonts, Noto Sans and Noto Sans Arabic (free SIL
     Open Font License, OFL-*.txt files). They contain every letter of the
     interface languages: extended Latin, Cyrillic and Arabic (including
     Uyghur letters). The interface therefore looks the same on Windows and
     Linux, and no letter shows up as an empty box.
"""

import logging

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from runecast.resources import resource_path

logger = logging.getLogger(__name__)

# FR : Fichiers de polices embarqués. EN : Bundled font files.
FONT_FILES = (
    "NotoSans-Regular.ttf",
    "NotoSans-Bold.ttf",
    "NotoSansArabic-Regular.ttf",
    "NotoSansArabic-Bold.ttf",
)

# FR : Ordre de préférence : Noto Sans pour le latin et le cyrillique, puis
#      Noto Sans Arabic pour l'arabe (Qt passe à la suivante automatiquement).
# EN : Order of preference: Noto Sans for Latin and Cyrillic, then Noto Sans
#      Arabic for Arabic (Qt moves to the next one automatically).
FONT_FAMILIES = ["Noto Sans", "Noto Sans Arabic"]


def load_fonts(app: QApplication) -> list[str]:
    """Charge les polices et les applique / Load the fonts and apply them.

    FR : Renvoie les noms des familles chargées. La taille reste celle du
         système, pour respecter les réglages d'accessibilité de l'utilisateur.
    EN : Returns the names of the loaded families. The size stays the system
         one, to respect the user's accessibility settings.
    """
    loaded: set[str] = set()
    for name in FONT_FILES:
        font_id = QFontDatabase.addApplicationFont(str(resource_path("fonts", name)))
        if font_id == -1:
            logger.error("Police non chargée / Font not loaded: %s", name)
            continue
        loaded.update(QFontDatabase.applicationFontFamilies(font_id))
    font = QFont(app.font())
    font.setFamilies(FONT_FAMILIES)
    app.setFont(font)
    return sorted(loaded)
