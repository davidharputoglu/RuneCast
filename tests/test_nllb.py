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

"""Tests du modèle étendu NLLB-200 (étape 15).

FR : Le vrai modèle (630 Mo) est essayé par GitHub (test « Modèles » :
     anglais → kazakh, ouzbek, turkmène, tatar, ouïghour). Ici, on vérifie
     avec des fichiers factices : fiche figée, téléchargement vérifié,
     installation complète ou rien, format des phrases envoyées au modèle,
     et surtout que rien n'est téléchargé sans acceptation de la licence.
EN : The real model (630 MB) is tried by GitHub ("Models" check). Here, fake
     files are used: pinned sheet, checked download, complete-or-nothing
     installation, shape of the sentences sent to the model, and above all
     that nothing is downloaded without the license being accepted.
"""

import hashlib
import re
import shutil
from dataclasses import replace
from pathlib import Path

import httpx
import pytest
from PySide6.QtWidgets import QLabel, QMessageBox

from runecast.core.settings import Settings, load_settings
from runecast.engines.base import EngineUnavailable
from runecast.engines.models import ChecksumError
from runecast.engines.nllb import (
    NLLB_CODES,
    NllbEngine,
    NllbFile,
    NllbStore,
    load_nllb_catalog,
)
from runecast.ui import main_window
from runecast.ui.i18n import LanguageManager
from runecast.ui.license_dialog import NllbLicenseDialog
from runecast.ui.models_page import ModelsPage


def test_catalog_is_pinned() -> None:
    """FR : fiche figée sur une révision précise, avec licence. EN : pinned sheet, license."""
    catalog = load_nllb_catalog()
    assert re.fullmatch(r"[0-9a-f]{40}", catalog.revision)
    assert catalog.license == "CC-BY-NC-4.0"
    assert {file.name for file in catalog.files} == {
        "config.json",
        "shared_vocabulary.txt",
        "sentencepiece.bpe.model",
        "model.bin",
    }
    url = catalog.url(catalog.files[0])
    assert url.startswith("https://huggingface.co/") and catalog.revision in url


def test_turkic_languages_are_covered() -> None:
    """FR : les 8 langues turciques et les 15 langues de l'interface sont là.

    EN : the 8 Turkic languages and the 15 interface languages are there.
    """
    for code in (
        "tr",
        "az",
        "uz",
        "kk",
        "tk",
        "ky",
        "tt",
        "ug",
        "ar",
        "fr",
        "en",
        "es",
        "pt",
        "it",
    ):
        assert code in NLLB_CODES, code
    assert NLLB_CODES["kk"] == "kaz_Cyrl" and NLLB_CODES["ug"] == "uig_Arab"


@pytest.fixture
def files(tmp_path: Path, tokenizer_file: Path) -> dict[str, bytes]:
    """FR : contenu des 4 fichiers factices. EN : content of the 4 fake files."""
    return {
        "config.json": b"{}",
        "shared_vocabulary.txt": b"a\nb\n",
        "sentencepiece.bpe.model": tokenizer_file.read_bytes(),
        "model.bin": b"poids" * 1000,
    }


def _store(tmp_path: Path, files: dict[str, bytes], wrong: str | None = None) -> NllbStore:
    """FR : modèle factice dont la fiche connaît les vraies empreintes.

    EN : fake model whose sheet knows the real fingerprints.
    """
    catalog = load_nllb_catalog()
    sheet = replace(
        catalog,
        files=tuple(
            NllbFile(
                name,
                len(content),
                "0" * 64 if name == wrong else hashlib.sha256(content).hexdigest(),
            )
            for name, content in files.items()
        ),
    )
    return NllbStore(tmp_path / "models" / "nllb", tmp_path / "downloads", sheet)


def _server(files: dict[str, bytes]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=files[request.url.path.rsplit("/", 1)[-1]])

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_install_and_remove(tmp_path, files) -> None:
    """FR : les 4 fichiers sont téléchargés, vérifiés, puis installés ensemble.

    EN : the 4 files are downloaded, checked, then installed together.
    """
    store = _store(tmp_path, files)
    steps: list[tuple[int, int]] = []
    store.install(progress=lambda d, t: steps.append((d, t)), client=_server(files))
    assert store.installed() and store.verify()
    assert steps[-1] == (sum(map(len, files.values())), sum(map(len, files.values())))
    assert store.size() > sum(map(len, files.values()))  # FR : + fiche d'installation
    store.remove()
    assert not store.installed()


def test_bad_file_installs_nothing(tmp_path, files) -> None:
    """FR : un fichier à l'empreinte fausse : rien n'est installé. EN : nothing installed."""
    store = _store(tmp_path, files, wrong="model.bin")
    with pytest.raises(ChecksumError):
        store.install(client=_server(files))
    assert not store.installed()
    assert not store.folder.exists()


class Seq2Seq:
    """FR : faux CTranslate2 imitant NLLB. EN : fake CTranslate2 imitating NLLB."""

    batches: list = []

    def __init__(self, path, **options):
        pass

    def translate_batch(self, batch, target_prefix=None, **options):
        Seq2Seq.batches.append((batch, target_prefix))

        class Result:
            def __init__(self, tokens):
                self.hypotheses = [tokens]

        # FR : renvoie le préfixe de langue puis les morceaux, sans le code
        #      source ni « </s ». EN : returns the language prefix then the
        #      pieces, without the source code nor "</s>".
        return [
            Result(prefix + tokens[1:-1])
            for prefix, tokens in zip(target_prefix, batch, strict=True)
        ]


@pytest.fixture
def installed(tmp_path, files) -> NllbStore:
    store = _store(tmp_path, files)
    store.install(client=_server(files))
    return store


def test_engine_translates(installed: NllbStore) -> None:
    """FR : phrases envoyées au bon format, préfixe retiré. EN : right format, prefix removed."""
    Seq2Seq.batches = []
    engine = NllbEngine(installed, translator_factory=Seq2Seq)
    assert engine.supports("en", "kk") and not engine.supports("en", "xx")
    texts = ["Hello, how are you today? The quick brown fox.", ""]
    assert engine.translate(texts, "en", "kk") == texts
    batch, prefix = Seq2Seq.batches[0]
    assert batch[0][0] == "eng_Latn" and batch[0][-1] == "</s>"
    assert prefix == [["kaz_Cyrl"], ["kaz_Cyrl"]]
    engine.unload()
    assert engine._model is None


def test_engine_without_model(tmp_path) -> None:
    """FR : pas de modèle : moteur indisponible. EN : no model: engine unavailable."""
    engine = NllbEngine(NllbStore(tmp_path / "rien", tmp_path / "dl"))
    assert not engine.supports("en", "kk")
    with pytest.raises(EngineUnavailable):
        engine.translate(["Hello"], "en", "kk")


# ----------------------------------------------------------------------
# FR : Licence et page des Paramètres / EN : License and Settings page
# ----------------------------------------------------------------------
def test_license_dialog_needs_the_box_checked(qtbot) -> None:
    """FR : « Accepter et télécharger » reste grisé tant que la case n'est pas cochée.

    EN : "Accept and download" stays greyed until the box is checked.
    """
    dialog = NllbLicenseDialog(load_nllb_catalog())
    qtbot.addWidget(dialog)
    assert not dialog.ok_button.isEnabled()
    dialog.accept_check.setChecked(True)
    assert dialog.ok_button.isEnabled()
    texts = " ".join(label.text() for label in dialog.findChildren(QLabel))
    assert "NON COMMERCIALE" in texts and "creativecommons.org" in texts


@pytest.fixture
def page(qtbot, custom_paths) -> ModelsPage:
    widget = ModelsPage(custom_paths)
    qtbot.addWidget(widget)
    yield widget
    widget.shutdown()


def _fake_install(page: ModelsPage, files: dict[str, bytes]):
    def install(progress=None, should_cancel=None, client=None):
        page.nllb.folder.mkdir(parents=True)
        for name, content in files.items():
            (page.nllb.folder / name).write_bytes(content)
        (page.nllb.folder / "runecast-install.json").write_text("{}")

    return install


def test_no_download_without_license(page, monkeypatch, files) -> None:
    """FR : licence refusée : rien n'est téléchargé. EN : license refused: nothing downloaded."""
    started = []
    monkeypatch.setattr(page.nllb, "install", lambda *a, **k: started.append(1))
    monkeypatch.setattr(
        NllbLicenseDialog, "exec", lambda dialog: NllbLicenseDialog.DialogCode.Rejected
    )
    page.install_nllb()
    assert started == [] and page.task is None and page.license_date == ""


def test_download_after_license(page, qtbot, monkeypatch, files) -> None:
    """FR : licence acceptée : date notée, modèle installé, plus de question ensuite.

    EN : license accepted: date recorded, model installed, no more question afterwards.
    """
    asked = []
    monkeypatch.setattr(page.nllb, "install", _fake_install(page, files))
    monkeypatch.setattr(
        NllbLicenseDialog,
        "exec",
        lambda dialog: asked.append(1) or NllbLicenseDialog.DialogCode.Accepted,
    )
    with qtbot.waitSignal(page.nllb_license_accepted) as signal:
        page.install_nllb()
    assert re.match(r"\d{4}-\d{2}-\d{2}T", signal.args[0])
    qtbot.waitUntil(lambda: page.task is None, timeout=10_000)
    assert page.nllb.installed()
    assert page.nllb_status.text().startswith("Installé")
    assert page.try_from.findData("kk") >= 0  # FR : langues NLLB dans « Essayer »
    shutil.rmtree(page.nllb.folder)
    page.refresh()
    page.install_nllb()
    qtbot.waitUntil(lambda: page.task is None, timeout=10_000)
    assert asked == [1]  # FR : une seule question / EN : asked only once


def test_try_uses_nllb_when_argos_cannot(page, qtbot, monkeypatch, files) -> None:
    """FR : « Essayer » anglais → kazakh passe par NLLB-200 (Argos ne l'a pas).

    EN : "Try" English → Kazakh goes through NLLB-200 (Argos does not have it).
    """
    _fake_install(page, files)()
    page.refresh()
    monkeypatch.setattr(page.nllb_engine, "translate", lambda texts, s, t: ["Сәлем"])
    page.try_from.setCurrentIndex(page.try_from.findData("en"))
    page.try_to.setCurrentIndex(page.try_to.findData("kk"))
    page.try_text.setText("Hello")
    page.try_button.click()
    qtbot.waitUntil(lambda: page.task is None, timeout=10_000)
    assert page.try_result.text() == "Сәлем"


def test_remove_after_confirmation(page, monkeypatch, files) -> None:
    """FR : suppression de NLLB-200 après confirmation. EN : deletion after confirmation."""
    _fake_install(page, files)()
    page.refresh()
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.No)
    page.remove_nllb()
    assert page.nllb.installed()
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    page.remove_nllb()
    assert not page.nllb.installed()


def test_license_acceptance_is_saved(qtbot, custom_paths, qapp, monkeypatch) -> None:
    """FR : l'acceptation est enregistrée tout de suite dans les réglages.

    EN : the acceptance is saved at once in the settings.
    """
    window = main_window.MainWindow(custom_paths, Settings(), LanguageManager(qapp))
    qtbot.addWidget(window)
    dialog = window.create_settings_dialog()
    qtbot.addWidget(dialog)
    dialog.models_page.nllb_license_accepted.emit("2026-10-31T12:00:00+00:00")
    assert load_settings(custom_paths.settings_file).nllb_license_accepted.startswith("2026-10-31")
    dialog.done(0)
