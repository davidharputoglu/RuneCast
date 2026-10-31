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

"""Tests de l'assistant de premier lancement (étape 19).

FR : L'assistant apparaît sur un profil vierge ; la langue et le thème
     s'appliquent aussitôt ; le mode choisi est enregistré ; le modèle
     conseillé dépend de la langue (Argos, ou NLLB-200 après acceptation de
     sa licence) ; le résumé prévient si le mode local n'a pas de modèle.
EN : The wizard appears on a blank profile; language and theme apply at
     once; the chosen mode is saved; the advised model depends on the
     language (Argos, or NLLB-200 after accepting its license); the summary
     warns when local mode has no model.
"""

import json
from dataclasses import replace

import pytest
from PySide6.QtWidgets import QApplication

from runecast.core import paths
from runecast.core.settings import Settings, load_settings
from runecast.core.themes import builtin_themes
from runecast.engines.chain import MODE_LOCAL, MODE_ONLINE
from runecast.engines.online import NETWORK
from runecast.ui import main_window
from runecast.ui.app import is_first_launch
from runecast.ui.first_run import FirstRunWizard
from runecast.ui.i18n import LanguageManager
from runecast.ui.license_dialog import NllbLicenseDialog
from runecast.ui.theme import THEME_PROPERTY, apply_theme


@pytest.fixture
def languages(qapp: QApplication):
    manager = LanguageManager(qapp)
    yield manager
    manager.apply("fr")
    apply_theme(qapp, builtin_themes()["turquoise"])


@pytest.fixture
def window(qtbot, custom_paths, languages) -> main_window.MainWindow:
    win = main_window.MainWindow(custom_paths, Settings(), languages)
    qtbot.addWidget(win)
    return win


def _wizard(window, qtbot) -> FirstRunWizard:
    wizard = FirstRunWizard(window.paths, window.settings, window.themes, window.theme_name, window)
    wizard.language_chosen.connect(window.change_language)
    wizard.theme_chosen.connect(window.change_theme)
    # FR : l'assistant appartient à la fenêtre : elle le fermera elle-même
    #      (l'inscrire aussi auprès de qtbot le ferait détruire deux fois).
    # EN : the wizard belongs to the window: it will close it itself
    #      (registering it with qtbot too would destroy it twice).
    return wizard


def test_first_launch_detection(custom_paths) -> None:
    """FR : profil vierge = pas de fichier de réglages. EN : blank profile = no settings file."""
    assert is_first_launch(custom_paths)
    custom_paths.settings_file.parent.mkdir(parents=True)
    custom_paths.settings_file.write_text("{}", encoding="utf-8")
    assert not is_first_launch(custom_paths)


def test_no_wizard_when_custom_folder_missing(tmp_path) -> None:
    """FR : disque des données débranché : ce n'est pas un premier lancement.

    EN : data drive unplugged: this is not a first launch.
    """
    fallback = replace(
        paths.single_folder_paths(tmp_path / "standard", paths.MODE_CUSTOM),
        unavailable_custom_root=tmp_path / "disque-debranche",
    )
    assert not fallback.settings_file.exists()
    assert not is_first_launch(fallback)


def test_pages(window, qtbot) -> None:
    """FR : cinq pages, dans l'ordre. EN : five pages, in order."""
    wizard = _wizard(window, qtbot)
    titles = [wizard.page(page_id).title() for page_id in wizard.pageIds()]
    assert titles == [
        "Langue de l'interface",
        "Thème",
        "Traduction en ligne ou locale ?",
        "Modèle de traduction locale",
        "C'est prêt !",
    ]


def test_language_applies_at_once(window, qtbot) -> None:
    """FR : choisir l'anglais traduit aussitôt l'assistant et la fenêtre.

    EN : choosing English translates the wizard and the window at once.
    """
    wizard = _wizard(window, qtbot)
    wizard.language_combo.setCurrentIndex(wizard.language_combo.findData("en"))
    assert window.file_menu.title() == "&File"
    # FR : l'assistant (pas encore affiché) reçoit le changement juste après.
    # EN : the wizard (not shown yet) receives the change just after.
    qtbot.waitUntil(lambda: wizard.windowTitle() == "Welcome to RuneCast", timeout=5000)
    assert wizard.language_page.title() == "Interface language"
    assert load_settings(window.paths.settings_file).interface_language == "en"


def test_theme_applies_at_once(window, qtbot, qapp) -> None:
    """FR : choisir « Clair » l'applique aussitôt. EN : choosing "Light" applies it at once."""
    wizard = _wizard(window, qtbot)
    assert wizard.theme_radios["turquoise"].isChecked()
    wizard.theme_radios["clair"].setChecked(True)
    assert qapp.property(THEME_PROPERTY) == "clair"
    assert window.theme_actions["clair"].isChecked()


@pytest.mark.parametrize("mode", [MODE_LOCAL, MODE_ONLINE])
def test_mode_saved_at_the_end(window, monkeypatch, mode) -> None:
    """FR : le mode choisi est enregistré à la fin (verrou réseau compris).

    EN : the chosen mode is saved at the end (network lock included).
    """

    def finish(wizard: FirstRunWizard):
        (wizard.local_radio if mode == MODE_LOCAL else wizard.online_radio).setChecked(True)
        return FirstRunWizard.DialogCode.Accepted

    monkeypatch.setattr(FirstRunWizard, "exec", finish)
    window.first_run_action.trigger()
    assert load_settings(window.paths.settings_file).translation_mode == mode
    assert NETWORK.allowed is (mode == MODE_ONLINE)


def _install_fake_argos(paths, target: str) -> None:
    folder = paths.data_dir / "models" / "argos" / f"en_{target}"
    (folder / "model").mkdir(parents=True)
    (folder / "model" / "model.bin").write_bytes(b"x")
    (folder / "sentencepiece.model").write_bytes(b"x")
    (folder / "metadata.json").write_text(json.dumps({"from_code": "en", "to_code": target}))
    (folder / "runecast-install.json").write_text(
        json.dumps({"size": 1, "sha256": "0" * 64, "installed_at": "2026-10-31"})
    )


def test_argos_model_download(window, qtbot, monkeypatch) -> None:
    """FR : français : modèle Argos conseillé, téléchargé depuis l'assistant.

    EN : French: Argos model advised, downloaded from the wizard.
    """
    wizard = _wizard(window, qtbot)
    assert wizard.target_combo.currentData() == "fr"
    assert wizard.model_label.text().startswith("Modèle conseillé : ⁦English → Français")

    def fake_install(entry, progress=None, should_cancel=None, client=None):
        progress(1, 2)
        _install_fake_argos(window.paths, "fr")

    monkeypatch.setattr(wizard.models, "download_and_install", fake_install)
    wizard.download_button.click()
    qtbot.waitUntil(lambda: wizard.task is None, timeout=10_000)
    assert wizard.model_label.text().startswith("Modèle déjà installé")
    assert not wizard.download_button.isEnabled()


def test_nllb_needs_license(window, qtbot, monkeypatch) -> None:
    """FR : kazakh : NLLB-200 conseillé ; rien sans acceptation de la licence.

    EN : Kazakh: NLLB-200 advised; nothing without accepting the license.
    """
    wizard = _wizard(window, qtbot)
    wizard.target_combo.setCurrentIndex(wizard.target_combo.findData("kk"))
    assert "NLLB-200" in wizard.model_label.text()
    started = []
    monkeypatch.setattr(wizard.nllb, "install", lambda *a, **k: started.append(1))
    monkeypatch.setattr(NllbLicenseDialog, "exec", lambda d: NllbLicenseDialog.DialogCode.Rejected)
    wizard.download_button.click()
    assert started == [] and wizard.task is None
    monkeypatch.setattr(NllbLicenseDialog, "exec", lambda d: NllbLicenseDialog.DialogCode.Accepted)
    with qtbot.waitSignal(wizard.nllb_license_accepted):
        wizard.download_button.click()
    qtbot.waitUntil(lambda: wizard.task is None, timeout=10_000)
    assert started == [1]


def test_summary_warns_local_without_model(window, qtbot) -> None:
    """FR : mode local sans modèle : le résumé prévient. EN : local without model: warning."""
    wizard = _wizard(window, qtbot)
    wizard.local_radio.setChecked(True)
    wizard._update_summary()
    text = wizard.summary_label.text()
    assert "Mode : 100 % local" in text and "Attention" in text
    wizard.online_radio.setChecked(True)
    wizard._update_summary()
    assert "Attention" not in wizard.summary_label.text()


def test_help_menu_entry(window) -> None:
    """FR : Aide → Assistant de premier lancement… existe. EN : the Help entry exists."""
    assert window.first_run_action in window.help_menu.actions()
    assert window.first_run_action.text() == "Assistant de premier &lancement…"
