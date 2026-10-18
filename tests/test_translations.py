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

"""Tests des langues de l'interface / Interface language tests.

FR : Vérifie que chaque langue est traduite à 100 %, que les traductions sont
     à jour par rapport au code (un texte ajouté sans traduction fait échouer
     les tests), que les {variables} sont gardées, et que l'interface change
     de langue en direct, y compris de droite à gauche pour l'arabe.
EN : Checks that every language is 100 % translated, that translations are up
     to date with the code (a text added without translation makes the tests
     fail), that {variables} are kept, and that the interface switches
     language live, including right-to-left for Arabic.
"""

import importlib.util
import json
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from types import ModuleType

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from runecast.core.languages import (
    LANGUAGES,
    SOURCE_LANGUAGE,
    SYSTEM_LANGUAGE,
    resolve_language,
    translated_languages,
)
from runecast.core.settings import Settings
from runecast.resources import resource_path
from runecast.ui import fonts, main_window
from runecast.ui.i18n import LanguageManager

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER = re.compile(r"\{[a-z_]+\}")


def _load_tool() -> ModuleType:
    """FR : charge tools/update_translations.py. EN : load the translation tool."""
    path = PROJECT_ROOT / "tools" / "update_translations.py"
    spec = importlib.util.spec_from_file_location("update_translations", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tool = _load_tool()


def _messages(ts_path: Path) -> list[tuple[str, str, ET.Element]]:
    """FR : (contexte, texte source, traduction) de chaque message d'un .ts.

    EN : (context, source text, translation) of every message of a .ts file.
    """
    root = ET.parse(ts_path).getroot()
    result = []
    for context in root.findall("context"):
        name = context.findtext("name", "")
        for message in context.findall("message"):
            result.append((name, message.findtext("source", ""), message.find("translation")))
    return result


@pytest.fixture
def languages(qapp: QApplication):
    """FR : gestionnaire de langues, remis en français après le test.

    EN : language manager, put back to French after the test.
    """
    manager = LanguageManager(qapp)
    yield manager
    manager.apply(SOURCE_LANGUAGE)


@pytest.mark.parametrize("code", translated_languages())
def test_every_language_has_its_files(code: str) -> None:
    """FR : chaque langue a son .ts et son .qm. EN : each language has .ts and .qm."""
    assert tool.ts_file(code).is_file()
    assert Path(tool.qm_file(code)).is_file()


@pytest.mark.parametrize("code", translated_languages())
def test_every_text_is_translated(code: str) -> None:
    """FR : aucune traduction manquante. EN : no missing translation."""
    for context, source, translation in _messages(tool.ts_file(code)):
        assert translation is not None
        assert translation.get("type") != "unfinished", (context, source)
        assert (translation.text or "").strip(), (context, source)


@pytest.mark.parametrize("code", translated_languages())
def test_variables_are_kept(code: str) -> None:
    """FR : les {variables} sont identiques dans la traduction.

    EN : {variables} are identical in the translation.
    """
    for context, source, translation in _messages(tool.ts_file(code)):
        assert set(PLACEHOLDER.findall(source)) == set(PLACEHOLDER.findall(translation.text)), (
            context,
            source,
        )


def test_translations_match_the_code(tmp_path: Path) -> None:
    """FR : tout texte du code est dans les .ts, déjà traduit.

         Si ce test échoue : lancer « uv run python tools/update_translations.py »,
         puis traduire les nouveaux textes.
    EN : every text of the code is in the .ts files, already translated. If
         this test fails: run the tool above, then translate the new texts.
    """
    for code in translated_languages():
        shutil.copy(tool.ts_file(code), tool.ts_file(code, tmp_path))
    tool.run_lupdate(ts_dir=tmp_path)
    for code in translated_languages():
        fresh = _messages(tool.ts_file(code, tmp_path))
        committed = _messages(tool.ts_file(code))
        assert [(c, s) for c, s, _ in fresh] == [(c, s) for c, s, _ in committed]
        for context, source, translation in fresh:
            assert translation.get("type") != "unfinished", (code, context, source)


def test_compiled_files_are_up_to_date(tmp_path: Path) -> None:
    """FR : les .qm correspondent aux .ts. EN : .qm files match the .ts files."""
    tool.run_lrelease(qm_dir=tmp_path)
    for code in translated_languages():
        assert tool.qm_file(code, tmp_path).read_bytes() == tool.qm_file(code).read_bytes()


@pytest.mark.parametrize(
    ("setting", "system", "expected"),
    [
        ("en", "fr_FR", "en"),  # FR : choix de l'utilisateur / EN : user's choice
        (SYSTEM_LANGUAGE, "fr_FR", "fr"),  # FR : langue du système / EN : system language
        (SYSTEM_LANGUAGE, "ar_SA", "ar"),
        (SYSTEM_LANGUAGE, "ja_JP", "en"),  # FR : non disponible : anglais / EN : fallback
        ("xx", "de-DE", "en"),
    ],
)
def test_language_choice(setting: str, system: str, expected: str) -> None:
    """FR : choix de la langue affichée. EN : choice of the displayed language."""
    assert resolve_language(setting, system) == expected


def test_interface_switches_language_live(qtbot, custom_paths, languages) -> None:
    """FR : l'interface change de langue tout de suite, sans redémarrer.

    EN : the interface switches language immediately, without restarting.
    """
    window = main_window.MainWindow(custom_paths, Settings(), languages)
    qtbot.addWidget(window)
    assert window.file_menu.title() == "&Fichier"

    languages.apply("en")
    assert window.file_menu.title() == "&File"
    assert "Welcome to RuneCast" in window.welcome_title.text()
    assert QApplication.layoutDirection() == Qt.LayoutDirection.LeftToRight

    languages.apply("ar")
    assert window.file_menu.title() == "&ملف"
    assert QApplication.layoutDirection() == Qt.LayoutDirection.RightToLeft

    languages.apply("fr")
    assert window.file_menu.title() == "&Fichier"
    assert QApplication.layoutDirection() == Qt.LayoutDirection.LeftToRight


def test_language_choice_is_saved(qtbot, custom_paths, languages) -> None:
    """FR : le choix de langue est enregistré. EN : the language choice is saved."""
    window = main_window.MainWindow(custom_paths, Settings(), languages)
    qtbot.addWidget(window)
    window.language_actions["en"].trigger()
    saved = json.loads(custom_paths.settings_file.read_text(encoding="utf-8"))
    assert saved["interface_language"] == "en"
    assert window.language_actions["en"].isChecked()


def test_language_menu_uses_native_names(qtbot, custom_paths, languages) -> None:
    """FR : chaque langue est écrite dans sa propre langue. EN : native names."""
    window = main_window.MainWindow(custom_paths, Settings(), languages)
    qtbot.addWidget(window)
    for code, language in LANGUAGES.items():
        assert window.language_actions[code].text() == language.native_name
    assert window.language_actions[SYSTEM_LANGUAGE].isChecked()


def test_fonts_are_bundled_and_loaded(qapp: QApplication) -> None:
    """FR : les polices Noto sont embarquées, avec leur licence, et chargées.

    EN : the Noto fonts are bundled, with their license, and loaded.
    """
    for name in fonts.FONT_FILES:
        assert resource_path("fonts", name).is_file()
    assert resource_path("fonts", "OFL-NotoSans.txt").is_file()
    assert resource_path("fonts", "OFL-NotoSansArabic.txt").is_file()
    families = fonts.load_fonts(qapp)
    assert "Noto Sans" in families
    assert "Noto Sans Arabic" in families


def test_paths_stay_readable_in_right_to_left_text() -> None:
    """FR : un chemin inséré dans une phrase arabe est « isolé » de gauche à droite.

    EN : a path inserted into an Arabic sentence is "isolated" left-to-right.
    """
    from runecast.ui.i18n import keep_left_to_right

    assert keep_left_to_right("D:/Jeux") == "\u2066D:/Jeux\u2069"
