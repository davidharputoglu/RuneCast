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

"""Démarrage de l'interface graphique / Graphical interface start-up.

FR : Prépare l'application Qt (nom, icône, identifiants pour Windows et
     Linux, thème Turquoise), ouvre la fenêtre principale, puis attend que
     l'utilisateur la ferme.

EN : Prepares the Qt application (name, icon, Windows and Linux identifiers,
     Turquoise theme), opens the main window, then waits until the user
     closes it.
"""

import ctypes
import sys

from PySide6.QtWidgets import QApplication

from runecast import about
from runecast.ui.icons import app_icon
from runecast.ui.main_window import MainWindow
from runecast.ui.theme import apply_turquoise_theme


def _set_windows_taskbar_id() -> None:
    """Icône correcte dans la barre des tâches Windows / Right Windows taskbar icon.

    FR : Sans cet identifiant, Windows regrouperait RuneCast avec Python et
         afficherait l'icône de Python. Ne fait rien sous Linux.
    EN : Without this identifier, Windows would group RuneCast with Python and
         show the Python icon. Does nothing on Linux.
    """
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            about.WINDOWS_APP_USER_MODEL_ID
        )
    except (AttributeError, OSError):
        # FR : Très ancien Windows : on continue sans, ce n'est pas bloquant.
        # EN : Very old Windows: carry on without it, this is not blocking.
        pass


def create_application(argv: list[str] | None = None) -> QApplication:
    """Crée et configure l'application Qt / Create and configure the Qt app."""
    _set_windows_taskbar_id()

    # FR : Qt n'accepte qu'une seule application par programme : on réutilise
    #      celle qui existe déjà (cas des tests automatiques).
    # EN : Qt accepts a single application per program: reuse the existing one
    #      (happens during automatic tests).
    app = QApplication.instance() or QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName(about.APP_NAME)
    app.setApplicationDisplayName(about.APP_NAME)
    app.setApplicationVersion(about.APP_VERSION)
    app.setOrganizationName(about.AUTHOR)
    # FR : Sous Linux (Wayland), relie la fenêtre au fichier .desktop de
    #      RuneCast, ce qui permet au dock d'afficher la bonne icône.
    # EN : On Linux (Wayland), links the window to the RuneCast .desktop file,
    #      which lets the dock display the right icon.
    app.setDesktopFileName(about.APP_ID)
    app.setWindowIcon(app_icon())
    apply_turquoise_theme(app)
    return app


def run(argv: list[str] | None = None) -> int:
    """Lance RuneCast avec sa fenêtre / Start RuneCast with its window.

    FR : Renvoie le code de sortie de Qt (0 = tout va bien).
    EN : Returns Qt's exit code (0 = all good).
    """
    app = create_application(argv)
    window = MainWindow()
    window.show()
    return app.exec()
