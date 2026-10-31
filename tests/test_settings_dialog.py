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

"""Tests de la fenêtre principale complète et des Paramètres (étape 10).

FR : Vérifie qu'aucun menu n'est factice, que la fenêtre « Paramètres »
     affiche les réglages en cours, applique (OK, Appliquer) ou abandonne
     (Annuler) les changements, et que chaque réglage a un vrai effet :
     langue, thème, fenêtre mémorisée, journal détaillé. Vérifie aussi le
     plein écran, l'ouverture du journal et « Signaler un problème ».
EN : Checks that no menu is a dummy, that the "Settings" window shows the
     current settings, applies (OK, Apply) or drops (Cancel) the changes, and
     that every setting has a real effect: language, theme, remembered
     window, detailed log. Also checks full screen, opening the log and
     "Report a problem".
"""

import json
import logging

import pytest
from PySide6.QtCore import SIGNAL, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox

from runecast import about
from runecast.core import themes
from runecast.core.languages import SOURCE_LANGUAGE, SYSTEM_LANGUAGE
from runecast.core.logs import ROOT_LOGGER_NAME, set_detailed_log
from runecast.core.settings import Settings, load_settings, save_settings
from runecast.ui import main_window
from runecast.ui.folders_dialog import FoldersDialog
from runecast.ui.i18n import LanguageManager
from runecast.ui.settings_dialog import SettingsDialog
from runecast.ui.theme import THEME_PROPERTY, apply_theme
from runecast.ui.theme_editor import ThemeEditorDialog


@pytest.fixture
def languages(qapp: QApplication):
    """FR : gestionnaire de langues ; après chaque test : Turquoise, français,
         journal normal.
    EN : language manager; after each test: Turquoise, French, normal log.
    """
    manager = LanguageManager(qapp)
    yield manager
    apply_theme(qapp, themes.builtin_themes()[themes.DEFAULT_THEME])
    manager.apply(SOURCE_LANGUAGE)
    set_detailed_log(False)


@pytest.fixture
def window(qtbot, custom_paths, languages) -> main_window.MainWindow:
    """FR : fenêtre principale avec des dossiers de test. EN : main window with test folders."""
    win = main_window.MainWindow(custom_paths, Settings(), languages)
    qtbot.addWidget(win)
    return win


@pytest.fixture
def dialog(qtbot, window) -> SettingsDialog:
    """FR : fenêtre « Paramètres » reliée à la fenêtre principale, comme dans RuneCast.

    EN : "Settings" window connected to the main window, as in RuneCast.
    """
    settings_dialog = window.create_settings_dialog()
    qtbot.addWidget(settings_dialog)
    return settings_dialog


def _saved(paths) -> dict:
    """FR : contenu du fichier des réglages. EN : content of the settings file."""
    return json.loads(paths.settings_file.read_text(encoding="utf-8"))


def test_no_dummy_menu_entry(window) -> None:
    """FR : chaque entrée de menu fait vraiment quelque chose (cahier des charges).

    EN : every menu entry really does something (specification).
    """
    checked = 0
    for menu in window.findChildren(QMenu):
        for action in menu.actions():
            if action.isSeparator() or action.menu() is not None:
                continue
            connections = action.receivers(SIGNAL("triggered(bool)")) + action.receivers(
                SIGNAL("toggled(bool)")
            )
            assert connections > 0, action.text()
            checked += 1
    assert checked >= 15


def test_main_menus(window) -> None:
    """FR : les menus attendus sont là. EN : the expected menus are there."""
    assert window.settings_action in window.file_menu.actions()
    assert window.full_screen_action in window.view_menu.actions()
    for action in (window.open_log_action, window.report_problem_action, window.about_action):
        assert action in window.help_menu.actions()
    assert window.settings_action.shortcut().toString() == "Ctrl+,"
    assert window.full_screen_action.shortcut().toString() == "F11"


def test_settings_action_opens_the_window(window, monkeypatch) -> None:
    """FR : Fichier → Paramètres ouvre la fenêtre « Paramètres ». EN : opens the window."""
    opened: list[SettingsDialog] = []
    monkeypatch.setattr(SettingsDialog, "exec", lambda dialog: opened.append(dialog) or 0)
    window.settings_action.trigger()
    assert len(opened) == 1
    assert opened[0].windowTitle() == "Paramètres"
    assert [opened[0].page_list.item(i).text() for i in range(7)] == [
        "Général",
        "Traduction",
        "Moteurs en ligne",
        "Modèles de traduction",
        "Cache des traductions",
        "Fenêtre",
        "Dossiers et journal",
    ]


def test_dialog_shows_current_settings(dialog) -> None:
    """FR : la fenêtre affiche les réglages en cours. EN : the window shows the current settings."""
    assert dialog.general_page.language_combo.currentData() == SYSTEM_LANGUAGE
    assert dialog.general_page.theme_combo.currentData() == "turquoise"
    assert dialog.general_page.theme_combo.currentText() == "Turquoise"
    assert dialog.window_page.remember_check.isChecked()
    assert not dialog.folders_page.detailed_log_check.isChecked()
    assert (
        str(dialog.folders_page.paths.config_dir)
        in dialog.folders_page.settings_folder_label.text()
    )


def test_apply_changes_theme_and_keeps_dialog_open(dialog, window, qapp, custom_paths) -> None:
    """FR : « Appliquer » change le thème tout de suite et l'enregistre.

    EN : "Apply" changes the theme at once and saves it.
    """
    combo = dialog.general_page.theme_combo
    combo.setCurrentIndex(combo.findData("clair"))
    dialog.apply_button.click()
    assert qapp.property(THEME_PROPERTY) == "clair"
    assert window.theme_actions["clair"].isChecked()
    assert _saved(custom_paths)["theme"] == "clair"
    assert dialog.result() == 0  # FR : toujours ouverte / EN : still open


def test_cancel_changes_nothing(dialog, window, qapp, custom_paths) -> None:
    """FR : « Annuler » ne change rien. EN : "Cancel" changes nothing."""
    combo = dialog.general_page.theme_combo
    combo.setCurrentIndex(combo.findData("noir"))
    dialog.window_page.remember_check.setChecked(False)
    dialog.reject()
    assert qapp.property(THEME_PROPERTY) == "turquoise"
    assert window.settings.remember_window
    assert not custom_paths.settings_file.exists()


def test_ok_changes_language_live(dialog, window, custom_paths) -> None:
    """FR : « OK » avec l'anglais : l'interface passe en anglais tout de suite.

    EN : "OK" with English: the interface switches to English at once.
    """
    combo = dialog.general_page.language_combo
    combo.setCurrentIndex(combo.findData("en"))
    dialog.apply_button.click()
    assert window.file_menu.title() == "&File"
    assert dialog.windowTitle() == "Settings"
    assert dialog.page_list.item(0).text() == "General"
    assert window.language_actions["en"].isChecked()
    dialog.accept()
    assert _saved(custom_paths)["interface_language"] == "en"


def test_detailed_log_takes_effect(dialog, window, custom_paths) -> None:
    """FR : le journal détaillé note aussi les messages techniques, aussitôt.

    EN : the detailed log also records technical messages, at once.
    """
    root = logging.getLogger(ROOT_LOGGER_NAME)
    dialog.folders_page.detailed_log_check.setChecked(True)
    dialog.accept()
    assert root.level == logging.DEBUG
    assert _saved(custom_paths)["detailed_log"] is True


def test_window_position_can_be_forgotten(qtbot, custom_paths, languages) -> None:
    """FR : réglage décoché : la taille et la place ne sont plus mémorisées.

    EN : setting unchecked: size and position are no longer remembered.
    """
    first = main_window.MainWindow(custom_paths, Settings(), languages)
    qtbot.addWidget(first)
    first.resize(800, 520)
    first.close()
    assert load_settings(custom_paths.settings_file).window_geometry

    settings = load_settings(custom_paths.settings_file)
    settings.remember_window = False
    second = main_window.MainWindow(custom_paths, settings, languages)
    qtbot.addWidget(second)
    assert second.size().width() == main_window.DEFAULT_SIZE[0]
    second.close()
    assert load_settings(custom_paths.settings_file).window_geometry == ""


def test_new_settings_have_defaults_in_old_files(tmp_path) -> None:
    """FR : un fichier de réglages d'avant l'étape 10 se lit sans problème.

    EN : a settings file from before step 10 is read without trouble.
    """
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"schema_version": 1, "theme": "noir"}), encoding="utf-8")
    settings = load_settings(path)
    assert settings.theme == "noir"
    assert settings.remember_window is True and settings.detailed_log is False
    save_settings(settings, path)
    assert json.loads(path.read_text(encoding="utf-8"))["remember_window"] is True


def test_full_screen(window) -> None:
    """FR : Affichage → Plein écran, puis retour. EN : View → Full screen, then back."""
    window.show()
    window.full_screen_action.trigger()
    assert window.isFullScreen()
    window.full_screen_action.trigger()
    assert not window.isFullScreen()


def test_open_log_folder(window, monkeypatch) -> None:
    """FR : Aide → Ouvrir le dossier du journal. EN : Help → Open the log folder."""
    opened: list[QUrl] = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened.append(url) or True)
    window.open_log_action.trigger()
    assert opened == [QUrl.fromLocalFile(str(window.paths.log_dir))]
    assert window.paths.log_dir.is_dir()


def test_report_problem_opens_github(window, monkeypatch) -> None:
    """FR : Aide → Signaler un problème ouvre la page GitHub. EN : opens the GitHub page."""
    opened: list[QUrl] = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened.append(url) or True)
    window.report_problem_action.trigger()
    assert opened == [QUrl(about.ISSUES_URL)]
    assert about.ISSUES_URL == "https://github.com/davidharputoglu/RuneCast/issues"


def test_open_failure_is_reported(window, monkeypatch) -> None:
    """FR : si le système refuse d'ouvrir, un message le dit. EN : a message says so."""
    shown: list[str] = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: False)
    monkeypatch.setattr(QMessageBox, "warning", lambda _p, title, *a, **k: shown.append(title))
    window.report_problem_action.trigger()
    assert shown == ["Ouverture impossible"]


def test_manage_themes_from_settings(dialog, window, monkeypatch, qapp) -> None:
    """FR : « Gérer les thèmes… » ouvre l'éditeur ; un nouveau thème apparaît
         ensuite dans la liste des Paramètres.
    EN : "Manage themes…" opens the editor; a new theme then shows in the
         Settings list.
    """
    parents = []

    def actions(editor: ThemeEditorDialog) -> int:
        parents.append(editor.parent())
        editor.duplicate()
        editor.use_current()
        return 0

    monkeypatch.setattr(ThemeEditorDialog, "exec", actions)
    dialog.general_page.manage_themes_button.click()
    assert parents == [dialog]
    combo = dialog.general_page.theme_combo
    assert combo.findData("turquoise-copie") >= 0
    assert combo.currentData() == "turquoise-copie"
    assert qapp.property(THEME_PROPERTY) == "turquoise-copie"


def test_manage_folders_from_settings(dialog, monkeypatch) -> None:
    """FR : « Gérer les dossiers… » ouvre la fenêtre des dossiers. EN : opens the folders window."""
    parents = []
    monkeypatch.setattr(FoldersDialog, "exec", lambda folders: parents.append(folders.parent()))
    dialog.folders_page.manage_folders_button.click()
    assert parents == [dialog]
