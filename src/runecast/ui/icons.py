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

"""Icône de l'application / Application icon.

FR : Construit l'icône Qt de RuneCast à partir des PNG embarqués, une image
     par taille. Qt choisit ensuite la plus adaptée selon l'endroit (barre de
     titre, barre des tâches, dock) et la résolution de l'écran.

EN : Builds the RuneCast Qt icon from the bundled PNG files, one image per
     size. Qt then picks the most suitable one depending on the place (title
     bar, taskbar, dock) and on the screen resolution.
"""

from PySide6.QtGui import QIcon

from runecast.resources import resource_path

# FR : Tailles embarquées dans l'application (voir tools/make_icons.py).
# EN : Sizes bundled with the application (see tools/make_icons.py).
ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)


def icon_file(size: int) -> str:
    """Chemin du PNG d'une taille donnée / Path of the PNG for a given size."""
    return str(resource_path("icons", f"runecast-{size}.png"))


def app_icon() -> QIcon:
    """Renvoie l'icône complète de RuneCast / Return the full RuneCast icon."""
    icon = QIcon()
    for size in ICON_SIZES:
        icon.addFile(icon_file(size))
    return icon
