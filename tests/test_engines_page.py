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

"""Tests de la page « Moteurs en ligne » (étape 16).

FR : Ordre et choix des moteurs, clés rangées dans le trousseau (seulement
     avec « OK » ou « Appliquer »), champs adaptés à chaque moteur, prix
     indicatif, et bouton « Tester » (avec un faux moteur).
EN : Engine order and choice, keys stored in the keyring (only with "OK" or
     "Apply"), fields suited to each engine, indicative price, and "Test"
     button (with a fake engine).
"""

import pytest
from PySide6.QtCore import QLocale, Qt

from runecast.core.settings import Settings, load_settings
from runecast.engines.online import REASON_OFFLINE, OnlineError
from runecast.ui import engines_page as engines_page_module
from runecast.ui import main_window
from runecast.ui.engines_page import OnlineEnginesPage, normalized_order
from runecast.ui.i18n import LanguageManager


@pytest.fixture
def page(qtbot, custom_paths) -> OnlineEnginesPage:
    widget = OnlineEnginesPage(custom_paths)
    qtbot.addWidget(widget)
    widget.load(Settings())
    yield widget
    widget.shutdown()


def _select(page: OnlineEnginesPage, engine_id: str) -> None:
    page.engine_list.setCurrentRow(page.order().index(engine_id))


def test_default_list(page: OnlineEnginesPage) -> None:
    """FR : ordre par défaut, Yandex et Google gratuits cochés. EN : default order and checks."""
    assert page.order()[:3] == ["yandex_key", "yandex_free", "google_free"]
    assert page.enabled() == ["yandex_free", "google_free"]
    assert page.engine_list.item(1).text() == "Yandex (gratuit, non officiel)"
    assert page.engine_list.item(0).text() == "Yandex Cloud (clé)"


def test_move_engines(page: OnlineEnginesPage) -> None:
    """FR : « Monter » et « Descendre » changent l'ordre. EN : "Up" and "Down" change the order."""
    _select(page, "google_free")
    page.up_button.click()
    page.up_button.click()
    assert page.order()[:3] == ["google_free", "yandex_key", "yandex_free"]
    assert not page.up_button.isEnabled()
    page.down_button.click()
    assert page.order()[1] == "google_free"


def test_fields_follow_the_engine(page: OnlineEnginesPage) -> None:
    """FR : seuls les champs utiles au moteur sont affichés. EN : only useful fields are shown."""
    _select(page, "yandex_key")
    assert not page.key_edit.isHidden() and not page.option_edits["folder_id"].isHidden()
    assert page.option_edits["region"].isHidden()
    _select(page, "google_free")
    assert page.key_edit.isHidden() and page.option_edits["folder_id"].isHidden()
    assert "NON OFFICIEL" in page.description.text()
    _select(page, "microsoft")
    assert not page.option_edits["region"].isHidden()
    _select(page, "deepl")
    text = page.description.text()
    assert f"{QLocale().toString(25.0, 'f', 2)} $" in text
    assert QLocale().toString(500_000) in text


def test_keys_saved_only_on_apply(page: OnlineEnginesPage, memory_keyring) -> None:
    """FR : la clé n'est rangée qu'avec OK/Appliquer, dans le trousseau, pas dans les réglages.

    EN : the key is stored only with OK/Apply, in the keyring, not in the settings.
    """
    _select(page, "deepl")
    page.key_edit.setText("abc:fx")
    page.key_edit.textEdited.emit("abc:fx")
    assert memory_keyring.passwords == {}
    page.engine_list.item(page.order().index("deepl")).setCheckState(Qt.CheckState.Checked)
    settings = Settings()
    page.store(settings)
    assert memory_keyring.passwords == {("RuneCast", "deepl"): "abc:fx"}
    assert "deepl" in settings.engines_enabled
    assert "abc:fx" not in str(settings.to_dict())


def test_options_saved(page: OnlineEnginesPage) -> None:
    """FR : réglages non secrets enregistrés avec les réglages. EN : non-secret options saved."""
    _select(page, "libretranslate")
    page.option_edits["url"].setText("https://lt.exemple.org")
    page.option_edits["url"].textEdited.emit("https://lt.exemple.org")
    settings = Settings()
    page.store(settings)
    assert settings.engine_options == {"libretranslate": {"url": "https://lt.exemple.org"}}


class FakeEngine:
    def __init__(self, result=None, error=None):
        self.result, self.error = result, error

    def translate(self, texts, source, target):
        if self.error:
            raise self.error
        return [self.result]

    def close(self):
        pass


@pytest.mark.parametrize(
    ("engine", "expected"),
    [
        (FakeEngine(result="Bonjour"), "Ça marche : « Bonjour »"),
        (FakeEngine(error=OnlineError(REASON_OFFLINE, "x")), "Échec : pas de connexion à internet"),
    ],
)
def test_test_button(page, qtbot, monkeypatch, engine, expected) -> None:
    """FR : « Tester » affiche la traduction ou la raison. EN : shows the result or the reason."""
    monkeypatch.setattr(engines_page_module, "create_engine", lambda *a, **k: engine)
    _select(page, "google_free")
    page.test_button.click()
    qtbot.waitUntil(lambda: page.task is None, timeout=10_000)
    assert page.test_result.text() == expected


def test_order_completed_with_new_engines() -> None:
    """FR : un moteur ajouté plus tard apparaît à la fin. EN : a later engine shows at the end."""
    assert normalized_order(["google_free", "inconnu"])[0] == "google_free"
    assert len(normalized_order(["google_free"])) == 7


def test_saved_through_settings_window(qtbot, custom_paths, qapp) -> None:
    """FR : « OK » enregistre l'ordre et les moteurs cochés. EN : "OK" saves order and checks."""
    window = main_window.MainWindow(custom_paths, Settings(), LanguageManager(qapp))
    qtbot.addWidget(window)
    dialog = window.create_settings_dialog()
    qtbot.addWidget(dialog)
    page = dialog.engines_page
    _select(page, "google_free")
    page.up_button.click()
    dialog.accept()
    saved = load_settings(custom_paths.settings_file)
    assert saved.engine_order[:2] == ["yandex_key", "google_free"]
    assert saved.engines_enabled == ["google_free", "yandex_free"]
