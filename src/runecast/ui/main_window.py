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

FR : Fenêtre principale : titre, icône, menus « Fichier » (Paramètres,
     Quitter), « Affichage » (langue, thème, plein écran) et « Aide »
     (dossiers, journal, signaler un problème, À propos), et un écran
     d'accueil. Elle se rouvre à la même taille et à la même place qu'à la
     dernière fermeture (réglable), et change aussitôt de langue ou de thème
     quand on le demande. Règle du cahier des charges : aucun élément
     factice. Chaque menu présent fait donc vraiment quelque chose (un test
     automatique le vérifie) ; les autres menus arriveront avec leurs
     fonctions.

EN : Main window: title, icon, "File" (Settings, Quit), "View" (language,
     theme, full screen) and "Help" (folders, log, report a problem, About)
     menus, and a welcome screen. It reopens with the same size and position
     as when it was last closed (adjustable), and switches language or theme
     immediately when asked.
     Rule from the specification: no dummy element. Every menu shown therefore
     really does something (an automatic test checks it); the other menus
     will come with their features.
"""

import logging
from html import escape

from PySide6.QtCore import QByteArray, QEvent, QLocale, Qt, QUrl
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QDesktopServices, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from runecast import about
from runecast.core.languages import LANGUAGES, SYSTEM_LANGUAGE, resolve_language
from runecast.core.logs import set_detailed_log
from runecast.core.paths import AppPaths
from runecast.core.settings import Settings, load_settings, save_settings
from runecast.core.themes import DEFAULT_THEME, Theme, all_themes, find_theme
from runecast.ui.about_dialog import AboutDialog
from runecast.ui.folders_dialog import FoldersDialog, open_folder
from runecast.ui.i18n import LanguageManager, keep_left_to_right
from runecast.ui.icons import app_icon
from runecast.ui.settings_dialog import SettingsDialog
from runecast.ui.theme import apply_theme
from runecast.ui.theme_editor import ThemeEditorDialog

logger = logging.getLogger(__name__)

# FR : Taille de la fenêtre à l'ouverture, et taille minimale (en pixels).
# EN : Window size when opened, and minimum size (in pixels).
DEFAULT_SIZE = (1000, 650)
MINIMUM_SIZE = (800, 500)


class MainWindow(QMainWindow):
    """Fenêtre principale / Main window."""

    def __init__(
        self,
        paths: AppPaths,
        settings: Settings,
        languages: LanguageManager | None = None,
    ) -> None:
        super().__init__()
        # FR : dossiers, réglages et langues de RuneCast.
        # EN : RuneCast folders, settings and languages.
        self.paths = paths
        self.settings = settings
        self.languages = languages or LanguageManager(QApplication.instance())
        # FR : thèmes disponibles : les 4 intégrés puis les thèmes personnels.
        # EN : available themes: the 4 built-in ones then the custom themes.
        self.themes: dict[str, Theme] = all_themes(paths.config_dir)
        self.setObjectName("mainWindow")
        self.setWindowTitle(f"{about.APP_NAME} {about.APP_VERSION}")
        self.setWindowIcon(app_icon())
        self.resize(*DEFAULT_SIZE)
        self.setMinimumSize(*MINIMUM_SIZE)

        self._create_actions()
        self._create_menus()
        self.setCentralWidget(self._create_welcome_screen())
        self.retranslate()
        self._restore_geometry()

    # ------------------------------------------------------------------
    # FR : Construction (sans texte : les textes sont posés par retranslate)
    # EN : Building (no text: texts are set by retranslate)
    # ------------------------------------------------------------------
    def _create_actions(self) -> None:
        # FR : Quitter l'application (Ctrl+Q sur Windows comme sur Linux).
        # EN : Quit the application (Ctrl+Q on Windows and Linux alike).
        self.quit_action = QAction(self)
        self.quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        self.quit_action.triggered.connect(self.close)

        # FR : Ouvrir la fenêtre « Paramètres » (Ctrl+virgule).
        # EN : Open the "Settings" window (Ctrl+comma).
        self.settings_action = QAction(self)
        self.settings_action.setShortcut(QKeySequence("Ctrl+,"))
        self.settings_action.triggered.connect(self.show_settings)

        # FR : Plein écran (touche F11), et retour à la normale.
        # EN : Full screen (F11 key), and back to normal.
        self.full_screen_action = QAction(self)
        self.full_screen_action.setCheckable(True)
        self.full_screen_action.setShortcut(QKeySequence("F11"))
        self.full_screen_action.toggled.connect(self.set_full_screen)

        # FR : Ouvrir le dossier du journal (à joindre pour signaler un problème).
        # EN : Open the log folder (to attach when reporting a problem).
        self.open_log_action = QAction(self)
        self.open_log_action.triggered.connect(self.open_log_folder)

        # FR : Signaler un problème : ouvre la page GitHub du projet.
        # EN : Report a problem: opens the project's GitHub page.
        self.report_problem_action = QAction(self)
        self.report_problem_action.triggered.connect(self.report_problem)

        # FR : Ouvrir la fenêtre « Dossiers de RuneCast ».
        # EN : Open the "RuneCast folders" window.
        self.folders_action = QAction(self)
        self.folders_action.triggered.connect(self.show_folders)

        # FR : Ouvrir la fenêtre « À propos de RuneCast ».
        # EN : Open the "About RuneCast" window.
        self.about_action = QAction(self)
        self.about_action.triggered.connect(self.show_about)

        # FR : Fenêtre officielle de Qt : informe l'utilisateur que RuneCast
        #      utilise Qt (licence LGPL), comme la licence de Qt le demande.
        # EN : Official Qt window: tells the user that RuneCast uses Qt (LGPL
        #      license), as the Qt license asks.
        self.about_qt_action = QAction(self)
        self.about_qt_action.triggered.connect(QApplication.aboutQt)

        # FR : Choix de la langue : « langue du système », puis une entrée par
        #      langue disponible, écrite dans sa propre langue. Une seule peut
        #      être cochée à la fois.
        # EN : Language choice: "system language", then one entry per available
        #      language, written in its own language. Only one can be checked.
        self.language_group = QActionGroup(self)
        self.language_group.setExclusive(True)
        self.language_actions: dict[str, QAction] = {}
        for code in [SYSTEM_LANGUAGE, *LANGUAGES]:
            action = QAction(self)
            action.setCheckable(True)
            action.setData(code)
            action.triggered.connect(lambda _checked=False, c=code: self.change_language(c))
            self.language_group.addAction(action)
            self.language_actions[code] = action
        current = self.settings.interface_language
        self.language_actions.get(current, self.language_actions[SYSTEM_LANGUAGE]).setChecked(True)

        # FR : Choix du thème : une entrée par thème, une seule cochée. Les
        #      entrées sont (re)créées par _rebuild_theme_menu, car la liste
        #      change quand on crée, importe ou supprime un thème personnel.
        # EN : Theme choice: one entry per theme, only one checked. Entries are
        #      (re)created by _rebuild_theme_menu, because the list changes
        #      when a custom theme is created, imported or deleted.
        self.theme_group = QActionGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_actions: dict[str, QAction] = {}

        # FR : Ouvrir l'éditeur de thèmes personnels.
        # EN : Open the custom theme editor.
        self.manage_themes_action = QAction(self)
        self.manage_themes_action.triggered.connect(self.show_theme_editor)

    def _create_menus(self) -> None:
        self.file_menu = self.menuBar().addMenu("")
        self.file_menu.setObjectName("fileMenu")
        self.file_menu.addAction(self.settings_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.quit_action)

        self.view_menu = self.menuBar().addMenu("")
        self.view_menu.setObjectName("viewMenu")
        self.language_menu = QMenu(self)
        self.language_menu.setObjectName("languageMenu")
        system_action = self.language_actions[SYSTEM_LANGUAGE]
        self.language_menu.addAction(system_action)
        self.language_menu.addSeparator()
        for code in LANGUAGES:
            self.language_menu.addAction(self.language_actions[code])
        self.view_menu.addMenu(self.language_menu)
        self.theme_menu = QMenu(self)
        self.theme_menu.setObjectName("themeMenu")
        self._rebuild_theme_menu()
        self.view_menu.addMenu(self.theme_menu)
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.full_screen_action)

        self.help_menu = self.menuBar().addMenu("")
        self.help_menu.setObjectName("helpMenu")
        self.help_menu.addAction(self.folders_action)
        self.help_menu.addAction(self.open_log_action)
        self.help_menu.addAction(self.report_problem_action)
        self.help_menu.addSeparator()
        self.help_menu.addAction(self.about_action)
        self.help_menu.addAction(self.about_qt_action)

    def _rebuild_theme_menu(self) -> None:
        """(Re)construit le menu Thème / (Re)build the Theme menu.

        FR : Thèmes intégrés, puis thèmes personnels, puis « Gérer les thèmes… ».
        EN : Built-in themes, then custom themes, then "Manage themes…".
        """
        for action in self.theme_actions.values():
            self.theme_group.removeAction(action)
            action.deleteLater()
        self.theme_actions = {}
        self.theme_menu.clear()
        builtin = [theme for theme in self.themes.values() if theme.builtin]
        custom = [theme for theme in self.themes.values() if not theme.builtin]
        for group in (builtin, custom):
            if group and self.theme_actions:
                self.theme_menu.addSeparator()
            for theme in group:
                action = QAction(self)
                action.setCheckable(True)
                action.setData(theme.id)
                action.triggered.connect(lambda _checked=False, t=theme.id: self.change_theme(t))
                self.theme_group.addAction(action)
                self.theme_menu.addAction(action)
                self.theme_actions[theme.id] = action
        self.theme_menu.addSeparator()
        self.theme_menu.addAction(self.manage_themes_action)
        self.theme_actions[find_theme(self.settings.theme, self.themes).id].setChecked(True)
        self._retranslate_theme_menu()

    def _create_welcome_screen(self) -> QWidget:
        logo = QLabel()
        logo.setPixmap(app_icon().pixmap(128, 128))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.welcome_title = QLabel()
        self.welcome_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # FR : Textes simples (sans mise en forme) : affichés tels quels.
        # EN : Plain texts (no formatting): displayed as they are.
        self.welcome_version = QLabel()
        self.welcome_version.setTextFormat(Qt.TextFormat.PlainText)
        self.welcome_version.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.welcome_message = QLabel()
        self.welcome_message.setTextFormat(Qt.TextFormat.PlainText)
        self.welcome_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_message.setWordWrap(True)

        screen = QWidget()
        screen.setObjectName("welcomeScreen")
        layout = QVBoxLayout(screen)
        layout.addStretch()
        for widget in (logo, self.welcome_title, self.welcome_version, self.welcome_message):
            layout.addWidget(widget)
        layout.addStretch()
        return screen

    # ------------------------------------------------------------------
    # FR : Textes affichés (dans la langue choisie)
    # EN : Displayed texts (in the chosen language)
    # ------------------------------------------------------------------
    def retranslate(self) -> None:
        """FR : (re)pose tous les textes dans la langue actuelle.

        EN : (re)set every text in the current language.
        """
        self.file_menu.setTitle(self.tr("&Fichier"))
        self.view_menu.setTitle(self.tr("&Affichage"))
        self.help_menu.setTitle(self.tr("&Aide"))
        self.language_menu.setTitle(self.tr("&Langue de l'interface"))
        self.theme_menu.setTitle(self.tr("&Thème"))
        self._retranslate_theme_menu()
        self.quit_action.setText(self.tr("&Quitter"))
        self.settings_action.setText(self.tr("&Paramètres…"))
        self.full_screen_action.setText(self.tr("&Plein écran"))
        self.open_log_action.setText(self.tr("Ouvrir le dossier du &journal"))
        self.report_problem_action.setText(self.tr("&Signaler un problème…"))
        self.folders_action.setText(self.tr("&Dossiers de RuneCast…"))
        self.about_action.setText(self.tr("À &propos de RuneCast…"))
        self.about_qt_action.setText(self.tr("À propos de &Qt…"))
        self.language_actions[SYSTEM_LANGUAGE].setText(self.tr("Langue du système"))
        for code, language in LANGUAGES.items():
            # FR : chaque langue garde son propre nom (« English », « العربية »…).
            # EN : each language keeps its own name ("English", "العربية"…).
            self.language_actions[code].setText(language.native_name)

        # FR : le texte est traduit à part, puis mis en forme (titre).
        # EN : the text is translated separately, then formatted (title).
        title = self.tr("Bienvenue dans RuneCast")
        self.welcome_title.setText(f"<h1>{escape(title)}</h1>")
        self.welcome_version.setText(self.tr("Version {version}").format(version=about.APP_VERSION))
        self.welcome_message.setText(
            self.tr(
                "La fenêtre principale est prête. L'ouverture des jeux et "
                "la traduction arriveront dans les prochaines étapes."
            )
        )

    def _retranslate_theme_menu(self) -> None:
        """FR : textes du menu Thème. EN : texts of the Theme menu."""
        for theme_id, action in self.theme_actions.items():
            action.setText(self.theme_name(self.themes[theme_id]))
        self.manage_themes_action.setText(self.tr("&Gérer les thèmes…"))

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802 (nom imposé par Qt)
        """FR : Qt prévient ici quand la langue change. EN : Qt signals language changes here."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslate()
        super().changeEvent(event)

    def theme_name(self, theme: Theme) -> str:
        """FR : nom affiché d'un thème, traduit pour les thèmes intégrés.

        EN : display name of a theme, translated for built-in themes.
        """
        builtin_names = {
            "turquoise": self.tr("Turquoise"),
            "noir": self.tr("Noir"),
            "sombre": self.tr("Sombre"),
            "clair": self.tr("Clair"),
        }
        if theme.builtin and theme.id in builtin_names:
            return builtin_names[theme.id]
        return theme.name

    def save(self) -> None:
        """FR : enregistre les réglages (une erreur est notée, sans bloquer).

        EN : save the settings (an error is logged, without blocking).
        """
        try:
            save_settings(self.settings, self.paths.settings_file)
        except OSError:
            logger.exception("Impossible d'enregistrer les réglages / Cannot save settings")

    def change_theme(self, theme_id: str) -> None:
        """Change le thème / Change the theme.

        FR : Le nouveau thème s'applique tout de suite et le choix est enregistré.
        EN : The new theme applies immediately and the choice is saved.
        """
        theme = find_theme(theme_id, self.themes)
        self.settings.theme = theme.id
        apply_theme(QApplication.instance(), theme)
        self.theme_actions[theme.id].setChecked(True)
        self.save()

    def reload_themes(self) -> None:
        """Relit les thèmes / Re-read the themes.

        FR : Appelé quand un thème personnel a été créé, modifié, importé ou
             supprimé. Si le thème actif a été modifié, ses nouvelles couleurs
             s'appliquent aussitôt ; s'il a été supprimé, on revient au thème
             Turquoise.
        EN : Called when a custom theme was created, changed, imported or
             deleted. If the active theme was changed, its new colours apply
             at once; if it was deleted, the Turquoise theme comes back.
        """
        self.themes = all_themes(self.paths.config_dir)
        if self.settings.theme in self.themes:
            apply_theme(QApplication.instance(), self.themes[self.settings.theme])
        else:
            self.change_theme(DEFAULT_THEME)
        self._rebuild_theme_menu()

    def change_language(self, code: str) -> None:
        """Change la langue de l'interface / Change the interface language.

        FR : « code » vide = suivre la langue du système. Le choix est
             enregistré aussitôt.
        EN : empty "code" = follow the system language. The choice is saved
             right away.
        """
        self.settings.interface_language = code
        self.language_actions.get(code, self.language_actions[SYSTEM_LANGUAGE]).setChecked(True)
        self.languages.apply(resolve_language(code, QLocale.system().name()))
        self.save()

    def apply_settings(self, new: Settings) -> None:
        """Applique les réglages de la fenêtre « Paramètres » / Apply the Settings window.

        FR : Seul ce qui a changé est appliqué, puis tout est enregistré.
        EN : Only what changed is applied, then everything is saved.
        """
        self.settings.remember_window = new.remember_window
        if new.detailed_log != self.settings.detailed_log:
            self.settings.detailed_log = new.detailed_log
            set_detailed_log(new.detailed_log)
            logger.info("Journal détaillé / Detailed log: %s", new.detailed_log)
        if new.theme != self.settings.theme:
            self.change_theme(new.theme)
        if new.interface_language != self.settings.interface_language:
            self.change_language(new.interface_language)
        self.save()

    def set_full_screen(self, full_screen: bool) -> None:
        """FR : passe en plein écran ou revient à la normale. EN : full screen on or off."""
        if full_screen:
            self.showFullScreen()
        else:
            self.showNormal()

    def open_log_folder(self) -> None:
        """FR : ouvre le dossier du journal. EN : open the log folder."""
        if not open_folder(self.paths.log_dir):
            self._cannot_open(str(self.paths.log_dir))

    def report_problem(self) -> None:
        """FR : ouvre la page « Issues » du projet sur GitHub, dans le navigateur.

        EN : open the project's "Issues" page on GitHub, in the browser.
        """
        if not QDesktopServices.openUrl(QUrl(about.ISSUES_URL)):
            self._cannot_open(about.ISSUES_URL)

    def _cannot_open(self, target: str) -> None:
        """FR : le système n'a pas pu ouvrir un dossier ou une adresse.

        EN : the system could not open a folder or an address.
        """
        QMessageBox.warning(
            self,
            self.tr("Ouverture impossible"),
            self.tr("Le système n'a pas pu ouvrir :\n{target}").format(
                target=keep_left_to_right(target)
            ),
        )

    # ------------------------------------------------------------------
    # FR : Fenêtres secondaires / EN : Secondary windows
    # ------------------------------------------------------------------
    def show_about(self) -> None:
        """Ouvre la fenêtre « À propos » / Open the "About" window."""
        AboutDialog(self).exec()

    def show_folders(self, parent: QWidget | None = None) -> None:
        """Ouvre la fenêtre « Dossiers » / Open the "Folders" window."""
        dialog = FoldersDialog(self.paths, parent or self)
        dialog.paths_changed.connect(self.use_paths)
        dialog.exec()

    def show_settings(self) -> None:
        """Ouvre la fenêtre « Paramètres » / Open the "Settings" window."""
        self.create_settings_dialog().exec()

    def create_settings_dialog(self) -> SettingsDialog:
        """FR : prépare la fenêtre « Paramètres », reliée à cette fenêtre.

        EN : prepare the "Settings" window, connected to this window.
        """
        dialog = SettingsDialog(self.settings, self.themes, self.paths, self.theme_name, self)
        dialog.applied.connect(self.apply_settings)
        dialog.general_page.manage_themes_button.clicked.connect(
            lambda: self._manage_themes_from(dialog)
        )
        dialog.folders_page.manage_folders_button.clicked.connect(
            lambda: self._manage_folders_from(dialog)
        )
        dialog.folders_page.open_log_button.clicked.connect(self.open_log_folder)
        return dialog

    def _manage_themes_from(self, dialog: SettingsDialog) -> None:
        """FR : « Gérer les thèmes… » depuis les Paramètres. EN : from the Settings."""
        self.show_theme_editor(parent=dialog)
        dialog.general_page.set_themes(self.themes, self.settings.theme)

    def _manage_folders_from(self, dialog: SettingsDialog) -> None:
        """FR : « Gérer les dossiers… » depuis les Paramètres. EN : from the Settings."""
        self.show_folders(parent=dialog)
        dialog.folders_page.show_paths(self.paths)
        dialog.load(self.settings)

    def show_theme_editor(self, parent: QWidget | None = None) -> None:
        """Ouvre l'éditeur de thèmes / Open the theme editor."""
        dialog = ThemeEditorDialog(self.paths.config_dir, self.settings.theme, parent or self)
        dialog.themes_changed.connect(self.reload_themes)
        dialog.theme_chosen.connect(self._use_chosen_theme)
        dialog.exec()

    def _use_chosen_theme(self, theme_id: str) -> None:
        """FR : « Utiliser ce thème » dans l'éditeur. EN : "Use this theme" in the editor."""
        self.change_theme(theme_id)

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
        # FR : les thèmes personnels sont rangés avec les réglages.
        # EN : custom themes are stored with the settings.
        self.reload_themes()

    # ------------------------------------------------------------------
    # FR : Taille et position mémorisées / EN : Remembered size and position
    # ------------------------------------------------------------------
    def _restore_geometry(self) -> None:
        """FR : remet la fenêtre à sa dernière taille et place.

        EN : put the window back to its last size and position.
        """
        if not self.settings.remember_window or not self.settings.window_geometry:
            return
        geometry = QByteArray.fromBase64(self.settings.window_geometry.encode("ascii"))
        if not self.restoreGeometry(geometry):
            logger.warning("Position de fenêtre illisible / Unreadable window position")
        self.full_screen_action.setChecked(self.isFullScreen())

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (nom imposé par Qt)
        """FR : à la fermeture, mémorise la taille et la place, puis enregistre.

        EN : on close, remember the size and position, then save.
        """
        if self.settings.remember_window:
            self.settings.window_geometry = bytes(self.saveGeometry().toBase64()).decode("ascii")
        else:
            self.settings.window_geometry = ""
        self.save()
        super().closeEvent(event)
