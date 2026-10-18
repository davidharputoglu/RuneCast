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

FR : Choisit les dossiers de données, démarre le journal, lit les réglages,
     prépare l'application Qt (nom, icône, identifiants pour Windows et Linux,
     polices, thème Turquoise, langue), ouvre la fenêtre principale, puis
     attend que l'utilisateur la ferme.

EN : Chooses the data folders, starts the log, reads the settings, prepares
     the Qt application (name, icon, Windows and Linux identifiers, fonts,
     Turquoise theme, language), opens the main window, then waits until the
     user closes it.
"""

import ctypes
import logging
import sys

from PySide6.QtCore import QCoreApplication, QLocale
from PySide6.QtWidgets import QApplication, QMessageBox

from runecast import about
from runecast.core.languages import resolve_language
from runecast.core.logs import log_startup, log_uncaught_exceptions, setup_logging
from runecast.core.paths import resolve_paths
from runecast.core.settings import load_settings, save_settings
from runecast.ui.fonts import load_fonts
from runecast.ui.i18n import LanguageManager, keep_left_to_right
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
    load_fonts(app)
    apply_turquoise_theme(app)
    return app


def run(argv: list[str] | None = None, portable: bool = False) -> int:
    """Lance RuneCast avec sa fenêtre / Start RuneCast with its window.

    FR : « portable=True » correspond à l'option « --portable ». Renvoie le
         code de sortie de Qt (0 = tout va bien).
    EN : "portable=True" matches the "--portable" option. Returns Qt's exit
         code (0 = all good).
    """
    # FR : 1. Dossiers, journal et réglages. EN : 1. Folders, log and settings.
    paths = resolve_paths(force_portable=portable)
    paths.create()
    setup_logging(paths.log_dir)
    log_uncaught_exceptions()
    log_startup(paths)
    settings = load_settings(paths.settings_file)
    # FR : on enregistre tout de suite : le fichier existe dès le 1er lancement.
    # EN : save right away so the file exists from the first launch.
    save_settings(settings, paths.settings_file)

    # FR : 2. Interface. EN : 2. Interface.
    app = create_application(argv)
    languages = LanguageManager(app)
    languages.apply(resolve_language(settings.interface_language, QLocale.system().name()))
    window = MainWindow(paths, settings, languages)
    window.show()
    if paths.unavailable_custom_root is not None:
        # FR : le dossier choisi est introuvable (ex. disque débranché) : on prévient.
        # EN : the chosen folder is missing (e.g. unplugged drive): warn the user.
        QMessageBox.warning(
            window,
            QCoreApplication.translate("App", "Dossier introuvable"),
            QCoreApplication.translate(
                "App",
                "Le dossier choisi pour les données est introuvable :\n{folder}\n\n"
                "RuneCast utilise l'emplacement standard pour cette fois. "
                "Rebranche le disque puis relance RuneCast.",
            ).format(folder=keep_left_to_right(paths.unavailable_custom_root)),
        )
    exit_code = app.exec()
    logging.getLogger("runecast").info("Fermeture / Exit (code %s)", exit_code)
    return exit_code
