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

"""Tests de la première fenêtre / Tests for the first window.

FR : Vérifie la fenêtre principale (titre, icône, menus réels), la fenêtre
     « À propos » (mentions obligatoires) et le thème Turquoise.
EN : Checks the main window (title, icon, real menus), the "About" window
     (mandatory mentions) and the Turquoise theme.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QPalette
from PySide6.QtWidgets import QApplication, QLabel, QMenu

from runecast import __main__ as cli
from runecast import about
from runecast.core.settings import Settings
from runecast.resources import resource_path
from runecast.ui import about_dialog, app, icons, main_window, theme


def _new_window(qtbot, app_paths) -> main_window.MainWindow:
    """FR : fenêtre principale avec des dossiers temporaires.

    EN : main window with temporary folders.
    """
    window = main_window.MainWindow(app_paths, Settings())
    qtbot.addWidget(window)
    return window


def _is_connected(action: QAction) -> bool:
    """FR : l'action est-elle reliée à une vraie fonction ?

    EN : is the action wired to a real function?
    """
    meta = action.metaObject()
    signal = meta.method(meta.indexOfSignal("triggered(bool)"))
    return action.isSignalConnected(signal)


def test_runtime_icons_are_bundled() -> None:
    """FR : les icônes sont bien dans le paquet. EN : icons are bundled."""
    for size in icons.ICON_SIZES:
        assert resource_path("icons", f"runecast-{size}.png").is_file()


def test_app_icon_has_every_size(qapp: QApplication) -> None:
    """FR : l'icône contient toutes les tailles. EN : icon has every size."""
    icon = icons.app_icon()
    assert not icon.isNull()
    available = {size.width() for size in icon.availableSizes()}
    assert set(icons.ICON_SIZES) <= available


def test_main_window_title_and_icon(qtbot, custom_paths) -> None:
    """FR : titre avec la version, et icône présente. EN : title and icon."""
    window = _new_window(qtbot, custom_paths)
    assert window.windowTitle() == f"RuneCast {about.APP_VERSION}"
    assert not window.windowIcon().isNull()


def test_welcome_screen_text_is_readable(qtbot, custom_paths) -> None:
    """FR : aucun code HTML visible par erreur (ex. « &#x27; » au lieu de « ' »).

    EN : no HTML code shown by mistake (e.g. "&#x27;" instead of "'").
    """
    window = _new_window(qtbot, custom_paths)
    for label in window.centralWidget().findChildren(QLabel):
        if label.textFormat() == Qt.TextFormat.PlainText:
            assert "&#" not in label.text() and "&amp;" not in label.text()
    texts = " ".join(label.text() for label in window.centralWidget().findChildren(QLabel))
    assert "L'ouverture des jeux" in texts


def test_menus_have_no_dummy_entry(qtbot, custom_paths) -> None:
    """FR : chaque entrée de menu est active et reliée à une fonction.

    EN : every menu entry is enabled and wired to a function.
    """
    window = _new_window(qtbot, custom_paths)
    menus = window.menuBar().findChildren(QMenu)
    assert {menu.objectName() for menu in menus} >= {"fileMenu", "helpMenu"}
    for menu in menus:
        for action in menu.actions():
            if action.isSeparator():
                continue
            assert action.isEnabled(), action.text()
            assert _is_connected(action), action.text()


def test_quit_closes_the_window(qtbot, custom_paths) -> None:
    """FR : « Quitter » ferme la fenêtre. EN : "Quit" closes the window."""
    window = _new_window(qtbot, custom_paths)
    window.show()
    window.quit_action.trigger()
    assert not window.isVisible()


def test_about_menu_opens_the_about_window(qtbot, monkeypatch, custom_paths) -> None:
    """FR : le menu « À propos » ouvre la bonne fenêtre.

    EN : the "About" menu opens the right window.
    """
    opened = []
    monkeypatch.setattr(about_dialog.AboutDialog, "exec", lambda self: opened.append(self) or 0)
    window = _new_window(qtbot, custom_paths)
    window.about_action.trigger()
    assert len(opened) == 1
    assert isinstance(opened[0], about_dialog.AboutDialog)


def test_about_window_shows_every_mandatory_mention(qtbot) -> None:
    """FR : la fenêtre « À propos » affiche toutes les mentions obligatoires.

    EN : the "About" window shows every mandatory mention.
    """
    dialog = about_dialog.AboutDialog()
    qtbot.addWidget(dialog)
    text = dialog.plain_text()
    for expected in (
        about.APP_NAME,
        about.APP_VERSION,
        about.CREDIT_LINE_FR,
        about.CREDIT_LINE_EN,
        about.CONTACT_EMAIL,
        about.LICENSE_SPDX,
        about.REPOSITORY_URL,
    ):
        assert expected in text


def test_turquoise_theme_is_applied(qapp: QApplication) -> None:
    """FR : le thème Turquoise est appliqué. EN : Turquoise theme is applied."""
    app.create_application()
    assert qapp.property(theme.THEME_PROPERTY) == "turquoise"
    assert theme.TURQUOISE["accent"] in qapp.styleSheet()
    window_color = qapp.palette().color(QPalette.ColorRole.Window).name()
    assert window_color.lower() == theme.TURQUOISE["window"].lower()
    assert qapp.desktopFileName() == about.APP_ID


def test_command_line_without_option_opens_the_window(monkeypatch) -> None:
    """FR : « runecast » sans option lance l'interface.

    EN : "runecast" without an option starts the interface.
    """
    calls = []
    monkeypatch.setattr(app, "run", lambda **options: calls.append(options) or 0)
    assert cli.main([]) == 0
    assert calls == [{"portable": False}]
    assert cli.main(["--portable"]) == 0
    assert calls[-1] == {"portable": True}
