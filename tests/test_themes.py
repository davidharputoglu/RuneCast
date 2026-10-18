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

"""Tests des thèmes / Theme tests.

FR : Vérifie les 4 thèmes intégrés (complets, lisibles selon la norme WCAG),
     la détection des fichiers de thème incorrects, et le changement de thème
     en direct depuis le menu Affichage.
EN : Checks the 4 built-in themes (complete, readable per the WCAG standard),
     detection of incorrect theme files, and live theme switching from the
     View menu.
"""

import json
from pathlib import Path

import pytest
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication

from runecast.core import themes
from runecast.core.settings import Settings
from runecast.ui import main_window
from runecast.ui.theme import THEME_PROPERTY, apply_theme

BUILTIN = themes.builtin_themes()


@pytest.fixture
def back_to_turquoise(qapp: QApplication):
    """FR : remet le thème Turquoise après le test. EN : restore Turquoise after the test."""
    yield
    apply_theme(qapp, BUILTIN[themes.DEFAULT_THEME])


def test_the_four_builtin_themes_exist() -> None:
    """FR : Turquoise, Noir, Sombre et Clair, dans cet ordre. EN : the 4 themes, in order."""
    assert list(BUILTIN) == ["turquoise", "noir", "sombre", "clair"]
    assert themes.DEFAULT_THEME == "turquoise"
    assert all(theme.builtin for theme in BUILTIN.values())
    assert not BUILTIN["clair"].dark
    assert BUILTIN["turquoise"].dark and BUILTIN["noir"].dark and BUILTIN["sombre"].dark


@pytest.mark.parametrize("theme_id", themes.BUILTIN_THEME_IDS)
def test_builtin_themes_are_readable(theme_id: str) -> None:
    """FR : texte, liens et sélection sont bien lisibles (contraste ≥ 4,5).

    EN : text, links and selection are easily readable (contrast ≥ 4.5).
    """
    colors = BUILTIN[theme_id].colors
    for foreground, background in (
        ("text", "window"),
        ("text", "base"),
        ("text", "surface"),
        ("link", "base"),
        ("link", "window"),
        ("highlighted_text", "highlight"),
        ("placeholder", "base"),
    ):
        ratio = themes.contrast_ratio(colors[foreground], colors[background])
        assert ratio >= 4.5, (theme_id, foreground, background, round(ratio, 2))


def test_contrast_ratio_reference_values() -> None:
    """FR : valeurs de référence de la norme. EN : reference values of the standard."""
    assert themes.contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21.0)
    assert themes.contrast_ratio("#777777", "#777777") == pytest.approx(1.0)


def _valid_data() -> dict:
    """FR : contenu d'un thème correct. EN : content of a valid theme."""
    turquoise = BUILTIN["turquoise"]
    return {
        "format": themes.THEME_FORMAT,
        "id": "mon-theme",
        "name": "Mon thème",
        "dark": True,
        "colors": dict(turquoise.colors),
    }


def test_valid_theme_file_is_read(tmp_path: Path) -> None:
    """FR : un thème correct est lu. EN : a valid theme is read."""
    path = tmp_path / "mon-theme.json"
    path.write_text(json.dumps(_valid_data()), encoding="utf-8")
    theme = themes.load_theme_file(path)
    assert theme.id == "mon-theme" and theme.name == "Mon thème" and not theme.builtin


@pytest.mark.parametrize(
    "broken",
    [
        {"format": 99},
        {"id": "Pas Valide"},
        {"name": ""},
        {"dark": "oui"},
        {"colors": "rouge"},
    ],
)
def test_wrong_theme_is_refused(broken: dict) -> None:
    """FR : un thème incorrect est refusé avec une explication. EN : refused with a reason."""
    data = _valid_data() | broken
    with pytest.raises(themes.ThemeError):
        themes.theme_from_dict(data)


def test_theme_with_bad_colour_is_refused() -> None:
    """FR : une couleur mal écrite est refusée. EN : a badly written colour is refused."""
    data = _valid_data()
    data["colors"]["text"] = "blanc"
    with pytest.raises(themes.ThemeError, match="text"):
        themes.theme_from_dict(data)


def test_unknown_theme_falls_back_to_turquoise() -> None:
    """FR : thème inconnu : Turquoise. EN : unknown theme: Turquoise."""
    assert themes.find_theme("n-existe-pas", BUILTIN).id == "turquoise"


@pytest.mark.parametrize("theme_id", themes.BUILTIN_THEME_IDS)
def test_menu_switches_theme_live_and_saves_it(
    qtbot, custom_paths, qapp, back_to_turquoise, theme_id: str
) -> None:
    """FR : le menu Affichage → Thème change le thème aussitôt et l'enregistre.

    EN : the View → Theme menu switches the theme immediately and saves it.
    """
    window = main_window.MainWindow(custom_paths, Settings())
    qtbot.addWidget(window)
    window.theme_actions[theme_id].trigger()

    expected = BUILTIN[theme_id].colors["window"].lower()
    assert qapp.palette().color(QPalette.ColorRole.Window).name() == expected
    assert qapp.property(THEME_PROPERTY) == theme_id
    saved = json.loads(custom_paths.settings_file.read_text(encoding="utf-8"))
    assert saved["theme"] == theme_id
    assert window.theme_actions[theme_id].isChecked()


def test_theme_menu_names_are_translated(qtbot, custom_paths) -> None:
    """FR : les noms des thèmes s'affichent (en français par défaut).

    EN : theme names are displayed (in French by default).
    """
    window = main_window.MainWindow(custom_paths, Settings())
    qtbot.addWidget(window)
    names = [window.theme_actions[t].text() for t in themes.BUILTIN_THEME_IDS]
    assert names == ["Turquoise", "Noir", "Sombre", "Clair"]
    assert window.theme_actions["turquoise"].isChecked()
