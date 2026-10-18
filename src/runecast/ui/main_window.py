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

"""Fenêtre principale de RuneCast / RuneCast main window.

FR : Fenêtre principale : titre, icône, menus « Fichier » et « Aide », et un
     écran d'accueil. Elle se rouvre à la même taille et à la même place
     qu'à la dernière fermeture. Règle du cahier des charges : aucun élément
     factice. Chaque menu présent fait donc vraiment quelque chose ; les
     autres menus arriveront avec leurs fonctions.

EN : Main window: title, icon, "File" and "Help" menus, and a welcome screen.
     It reopens with the same size and position as when it was last closed.
     Rule from the specification: no dummy element. Every menu shown therefore
     really does something; the other menus will come together with their
     features.
"""

import logging
from html import escape

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

from runecast import about
from runecast.core.paths import AppPaths
from runecast.core.settings import Settings, load_settings, save_settings
from runecast.ui.about_dialog import AboutDialog
from runecast.ui.folders_dialog import FoldersDialog
from runecast.ui.icons import app_icon

logger = logging.getLogger(__name__)

# FR : Taille de la fenêtre à l'ouverture, et taille minimale (en pixels).
# EN : Window size when opened, and minimum size (in pixels).
DEFAULT_SIZE = (1000, 650)
MINIMUM_SIZE = (800, 500)


class MainWindow(QMainWindow):
    """Fenêtre principale / Main window."""

    def __init__(self, paths: AppPaths, settings: Settings) -> None:
        super().__init__()
        # FR : dossiers et réglages de RuneCast. EN : RuneCast folders and settings.
        self.paths = paths
        self.settings = settings
        self.setObjectName("mainWindow")
        self.setWindowTitle(f"{about.APP_NAME} {about.APP_VERSION}")
        self.setWindowIcon(app_icon())
        self.resize(*DEFAULT_SIZE)
        self.setMinimumSize(*MINIMUM_SIZE)

        self._create_actions()
        self._create_menus()
        self.setCentralWidget(self._create_welcome_screen())
        self._restore_geometry()

    # ------------------------------------------------------------------
    # FR : Actions (ce que font les menus) / EN : Actions (what menus do)
    # ------------------------------------------------------------------
    def _create_actions(self) -> None:
        # FR : Quitter l'application (Ctrl+Q sur Windows comme sur Linux).
        # EN : Quit the application (Ctrl+Q on Windows and Linux alike).
        self.quit_action = QAction(self.tr("&Quitter"), self)
        self.quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        self.quit_action.triggered.connect(self.close)

        # FR : Ouvrir la fenêtre « Dossiers de RuneCast ».
        # EN : Open the "RuneCast folders" window.
        self.folders_action = QAction(self.tr("&Dossiers de RuneCast…"), self)
        self.folders_action.triggered.connect(self.show_folders)

        # FR : Ouvrir la fenêtre « À propos de RuneCast ».
        # EN : Open the "About RuneCast" window.
        self.about_action = QAction(self.tr("À &propos de RuneCast…"), self)
        self.about_action.triggered.connect(self.show_about)

        # FR : Fenêtre officielle de Qt : informe l'utilisateur que RuneCast
        #      utilise Qt (licence LGPL), comme la licence de Qt le demande.
        # EN : Official Qt window: tells the user that RuneCast uses Qt (LGPL
        #      license), as the Qt license asks.
        self.about_qt_action = QAction(self.tr("À propos de &Qt…"), self)
        self.about_qt_action.triggered.connect(QApplication.aboutQt)

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu(self.tr("&Fichier"))
        file_menu.setObjectName("fileMenu")
        file_menu.addAction(self.quit_action)

        help_menu = self.menuBar().addMenu(self.tr("&Aide"))
        help_menu.setObjectName("helpMenu")
        help_menu.addAction(self.folders_action)
        help_menu.addSeparator()
        help_menu.addAction(self.about_action)
        help_menu.addAction(self.about_qt_action)

    # ------------------------------------------------------------------
    # FR : Écran d'accueil / EN : Welcome screen
    # ------------------------------------------------------------------
    def _create_welcome_screen(self) -> QWidget:
        logo = QLabel()
        logo.setPixmap(app_icon().pixmap(128, 128))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel(f"<h1>{escape(self.tr('Bienvenue dans RuneCast'))}</h1>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # FR : Textes simples (sans mise en forme) : affichés tels quels.
        # EN : Plain texts (no formatting): displayed as they are.
        version = QLabel(self.tr("Version {version}").format(version=about.APP_VERSION))
        version.setTextFormat(Qt.TextFormat.PlainText)
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)

        message = QLabel(
            self.tr(
                "La fenêtre principale est prête. L'ouverture des jeux et "
                "la traduction arriveront dans les prochaines étapes."
            )
        )
        message.setTextFormat(Qt.TextFormat.PlainText)
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setWordWrap(True)

        screen = QWidget()
        screen.setObjectName("welcomeScreen")
        layout = QVBoxLayout(screen)
        layout.addStretch()
        for widget in (logo, title, version, message):
            layout.addWidget(widget)
        layout.addStretch()
        return screen

    def show_about(self) -> None:
        """Ouvre la fenêtre « À propos » / Open the "About" window."""
        AboutDialog(self).exec()

    def show_folders(self) -> None:
        """Ouvre la fenêtre « Dossiers » / Open the "Folders" window."""
        dialog = FoldersDialog(self.paths, self)
        dialog.paths_changed.connect(self.use_paths)
        dialog.exec()

    def use_paths(self, paths: AppPaths) -> None:
        """FR : les données ont changé de dossier : on suit le nouveau dossier.

             Les réglages sont relus depuis le nouvel emplacement, pour ne
             jamais écraser des données déjà présentes là-bas.
        EN : the data moved to another folder: follow the new folder. Settings
             are re-read from the new location so that data already there is
             never overwritten.
        """
        self.paths = paths
        if paths.settings_file.is_file():
            self.settings = load_settings(paths.settings_file)

    # ------------------------------------------------------------------
    # FR : Taille et position mémorisées / EN : Remembered size and position
    # ------------------------------------------------------------------
    def _restore_geometry(self) -> None:
        """FR : remet la fenêtre à sa dernière taille et place.

        EN : put the window back to its last size and position.
        """
        if not self.settings.window_geometry:
            return
        geometry = QByteArray.fromBase64(self.settings.window_geometry.encode("ascii"))
        if not self.restoreGeometry(geometry):
            logger.warning("Position de fenêtre illisible / Unreadable window position")

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (nom imposé par Qt)
        """FR : à la fermeture, mémorise la taille et la place, puis enregistre.

        EN : on close, remember the size and position, then save.
        """
        self.settings.window_geometry = bytes(self.saveGeometry().toBase64()).decode("ascii")
        try:
            save_settings(self.settings, self.paths.settings_file)
        except OSError:
            logger.exception("Impossible d'enregistrer les réglages / Cannot save settings")
        super().closeEvent(event)
