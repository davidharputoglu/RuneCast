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

"""Tests du moteur local et du gestionnaire de modèles (étape 13).

FR : Les vrais modèles (60 à 160 Mo chacun) sont essayés par GitHub (fichier
     .github/workflows/models.yml). Ici, on utilise de petits modèles
     factices : un vrai découpeur SentencePiece entraîné en une seconde, et
     un faux CTranslate2 qui renvoie ce qu'on lui donne. On vérifie :
     catalogue, installation sûre, empreintes, téléchargement avec reprise et
     annulation, pack hors-ligne, passage par l'anglais, mémoire limitée, et
     la page « Modèles de traduction » des Paramètres.
EN : Real models (60 to 160 MB each) are tried by GitHub. Here, small fake
     models are used: a real SentencePiece splitter trained in one second,
     and a fake CTranslate2 returning what it is given. Checked: catalogue,
     safe installation, fingerprints, download with resume and cancel,
     offline pack, going through English, limited memory, and the
     "Translation models" Settings page.
"""

import hashlib
import json
import zipfile
from dataclasses import replace
from pathlib import Path

import httpx
import pytest
from PySide6.QtWidgets import QFileDialog, QMessageBox

from runecast.engines import argos
from runecast.engines.argos import (
    ArgosPackage,
    LocalEngine,
    detokenize,
    from_argos,
    split_sentences,
    to_argos,
)
from runecast.engines.base import EngineUnavailable
from runecast.engines.models import (
    INSTALL_FILE,
    CatalogEntry,
    ChecksumError,
    DownloadCancelled,
    ModelError,
    ModelStore,
    file_sha256,
    load_catalog,
)
from runecast.ui import models_page as models_page_module
from runecast.ui.i18n import keep_left_to_right
from runecast.ui.models_page import ModelsPage, model_store


# ----------------------------------------------------------------------
# FR : Petits modèles factices / EN : Small fake models
# ----------------------------------------------------------------------
def make_archive(
    folder: Path,
    tokenizer_file: Path,
    from_code: str = "en",
    to_code: str = "fr",
    extra: dict | None = None,
    weights: bytes = b"poids",
) -> Path:
    """FR : fabrique un fichier .argosmodel factice. EN : build a fake .argosmodel file."""
    name = f"translate-{from_code}_{to_code}-1_9"
    archive = folder / f"{name}.argosmodel"
    metadata = {
        "from_code": from_code,
        "to_code": to_code,
        "package_version": "1.9",
        **(extra or {}),
    }
    with zipfile.ZipFile(archive, "w") as content:
        content.writestr(f"{name}/metadata.json", json.dumps(metadata))
        content.writestr(f"{name}/model/model.bin", weights)
        content.write(tokenizer_file, f"{name}/sentencepiece.model")
        content.writestr(f"{name}/README.md", "Modèle factice / fake model")
    return archive


@pytest.fixture
def store(tmp_path: Path) -> ModelStore:
    """FR : un dossier de modèles vide. EN : an empty models folder."""
    return ModelStore(tmp_path / "models", tmp_path / "downloads")


class Result:
    def __init__(self, tokens):
        self.hypotheses = [tokens]


class EchoTranslator:
    """FR : faux CTranslate2 : renvoie les morceaux reçus. EN : fake CTranslate2: echoes pieces."""

    loads = 0

    def __init__(self, path, **options):
        EchoTranslator.loads += 1
        self.options = options

    def translate_batch(self, batch, target_prefix=None, **options):
        if target_prefix:
            return [
                Result(prefix + list(tokens))
                for prefix, tokens in zip(target_prefix, batch, strict=True)
            ]
        return [Result(list(tokens)) for tokens in batch]


# ----------------------------------------------------------------------
# FR : Catalogue / EN : Catalogue
# ----------------------------------------------------------------------
def test_bundled_catalogue() -> None:
    """FR : le catalogue livré est complet : adresse, taille et empreinte de chaque modèle.

    EN : the shipped catalogue is complete: address, size and fingerprint of each model.
    """
    catalog = load_catalog()
    assert len(catalog) >= 80
    assert all(entry.url.startswith("https://") for entry in catalog)
    assert all(entry.size and len(entry.sha256 or "") == 64 for entry in catalog)
    directions = {(entry.from_code, entry.to_code) for entry in catalog}
    for target in ("fr", "es", "pt", "pt-BR", "it", "ar", "tr", "az", "ky", "ru"):
        assert ("en", target) in directions, target
    assert all(entry.supported for entry in catalog)
    everything = load_catalog(include_unsupported=True)
    assert len(everything) > len(catalog)
    assert all(not entry.supported for entry in everything if entry not in catalog)


def test_language_codes() -> None:
    """FR : codes Argos ↔ codes RuneCast. EN : Argos codes ↔ RuneCast codes."""
    assert to_argos("pt-BR") == "pb" and from_argos("pb") == "pt-BR"
    assert to_argos("zh-Hant") == "zt" and from_argos("zt") == "zh-Hant"
    assert to_argos("fr") == "fr" and from_argos("tr") == "tr"


# ----------------------------------------------------------------------
# FR : Installation / EN : Installation
# ----------------------------------------------------------------------
def test_install_archive(store: ModelStore, tmp_path: Path, tokenizer_file: Path) -> None:
    """FR : un modèle s'installe et apparaît dans la liste. EN : a model installs and is listed."""
    archive = make_archive(tmp_path, tokenizer_file)
    model = store.install_archive(archive, file_sha256(archive))
    assert model.key == ("en", "fr")
    assert model.sha256 == file_sha256(archive)
    assert (store.folder / "en_fr" / INSTALL_FILE).is_file()
    assert set(store.installed()) == {("en", "fr")}
    assert archive.is_file()  # FR : le fichier d'origine reste / EN : the original stays
    assert not [p for p in store.folder.iterdir() if p.name.startswith(".")]


def test_reinstall_replaces_model(store: ModelStore, tmp_path: Path, tokenizer_file: Path) -> None:
    """FR : réinstaller remplace l'ancien modèle. EN : reinstalling replaces the old model."""
    store.install_archive(make_archive(tmp_path, tokenizer_file, weights=b"ancien"))
    second = make_archive(tmp_path / "..", tokenizer_file, weights=b"nouveau")
    store.install_archive(second)
    assert (store.folder / "en_fr" / "model" / "model.bin").read_bytes() == b"nouveau"
    assert len(store.installed()) == 1


def test_wrong_fingerprint_is_refused(store: ModelStore, tmp_path: Path, tokenizer_file) -> None:
    """FR : empreinte incorrecte : rien d'installé. EN : wrong fingerprint: nothing installed."""
    archive = make_archive(tmp_path, tokenizer_file)
    with pytest.raises(ChecksumError):
        store.install_archive(archive, "0" * 64)
    assert store.installed() == {}


def test_incomplete_model_is_refused(store: ModelStore, tmp_path: Path) -> None:
    """FR : un modèle incomplet est refusé, sans laisser de fichiers. EN : refused, no leftovers."""
    archive = tmp_path / "incomplet.argosmodel"
    with zipfile.ZipFile(archive, "w") as content:
        content.writestr("x/metadata.json", json.dumps({"from_code": "en", "to_code": "fr"}))
    with pytest.raises(argos.ModelFormatError):
        store.install_archive(archive)
    assert store.installed() == {}
    assert list(store.folder.iterdir()) == []


@pytest.mark.parametrize("bad_name", ["../evil.txt", "/etc/evil", "C:/evil.txt", "a/../../evil"])
def test_trapped_archive_is_refused(store: ModelStore, tmp_path: Path, bad_name: str) -> None:
    """FR : une archive piégée (chemins qui sortent du dossier) est refusée.

    EN : a booby-trapped archive (paths leaving the folder) is refused.
    """
    archive = tmp_path / "piege.argosmodel"
    with zipfile.ZipFile(archive, "w") as content:
        content.writestr(bad_name, "malveillant")
    with pytest.raises(ModelError):
        store.install_archive(archive)
    assert not (tmp_path / "evil.txt").exists()


def test_not_an_archive(store: ModelStore, tmp_path: Path) -> None:
    """FR : un fichier qui n'est pas un modèle est refusé. EN : a non-model file is refused."""
    fake = tmp_path / "faux.argosmodel"
    fake.write_text("pas un zip", encoding="utf-8")
    with pytest.raises(ModelError):
        store.install_archive(fake)


def test_remove(store: ModelStore, tmp_path: Path, tokenizer_file: Path) -> None:
    """FR : suppression d'un modèle. EN : deleting a model."""
    store.install_archive(make_archive(tmp_path, tokenizer_file))
    store.remove("en", "fr")
    assert store.installed() == {}
    store.remove("en", "fr")  # FR : sans erreur s'il n'existe plus / EN : no error if gone


def test_damaged_install_is_skipped(store: ModelStore, tmp_path: Path, tokenizer_file) -> None:
    """FR : un modèle installé abîmé est ignoré, sans planter. EN : a damaged one is skipped."""
    store.install_archive(make_archive(tmp_path, tokenizer_file))
    (store.folder / "en_fr" / "sentencepiece.model").unlink()
    assert store.installed() == {}


# ----------------------------------------------------------------------
# FR : Téléchargement (faux serveur) / EN : Download (fake server)
# ----------------------------------------------------------------------
def _entry(archive: Path, sha256: str | None = "auto") -> CatalogEntry:
    return CatalogEntry(
        code="translate-en_fr",
        from_code="en",
        to_code="fr",
        from_name="English",
        to_name="French",
        version="1.9",
        url=f"https://exemple.invalid/v1/{archive.name}",
        size=archive.stat().st_size,
        sha256=file_sha256(archive) if sha256 == "auto" else sha256,
        tokenizer="sentencepiece",
    )


def _server(content: bytes, honour_range: bool = True, status: int = 200, requests=None):
    """FR : faux serveur web. EN : fake web server."""

    def handler(request: httpx.Request) -> httpx.Response:
        if requests is not None:
            requests.append(request)
        if status != 200:
            return httpx.Response(status)
        wanted = request.headers.get("Range")
        if wanted and honour_range:
            start = int(wanted.removeprefix("bytes=").rstrip("-"))
            return httpx.Response(206, content=content[start:])
        return httpx.Response(200, content=content)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_download(store: ModelStore, tmp_path: Path, tokenizer_file: Path) -> None:
    """FR : téléchargement avec progression et empreinte vérifiée. EN : download with progress."""
    archive = make_archive(tmp_path, tokenizer_file)
    steps: list[tuple[int, int]] = []
    path = store.download(
        _entry(archive),
        progress=lambda d, t: steps.append((d, t)),
        client=_server(archive.read_bytes()),
    )
    assert path.read_bytes() == archive.read_bytes()
    assert steps[-1] == (archive.stat().st_size, archive.stat().st_size)
    assert not list(store.download_folder.glob("*.part"))


def test_download_resumes(store: ModelStore, tmp_path: Path, tokenizer_file: Path) -> None:
    """FR : un téléchargement coupé reprend où il s'était arrêté. EN : resumes where it stopped."""
    archive = make_archive(tmp_path, tokenizer_file)
    content = archive.read_bytes()
    store.download_folder.mkdir(parents=True)
    (store.download_folder / (archive.name + ".part")).write_bytes(content[:100])
    requests: list[httpx.Request] = []
    path = store.download(_entry(archive), client=_server(content, requests=requests))
    assert requests[0].headers["Range"] == "bytes=100-"
    assert path.read_bytes() == content


def test_download_restarts_if_server_ignores_resume(store, tmp_path, tokenizer_file) -> None:
    """FR : si le serveur ne sait pas reprendre, on recommence au début.

    EN : if the server cannot resume, start again from the beginning.
    """
    archive = make_archive(tmp_path, tokenizer_file)
    content = archive.read_bytes()
    store.download_folder.mkdir(parents=True)
    (store.download_folder / (archive.name + ".part")).write_bytes(b"debut abime")
    path = store.download(_entry(archive), client=_server(content, honour_range=False))
    assert path.read_bytes() == content


def test_download_with_wrong_fingerprint(store, tmp_path, tokenizer_file) -> None:
    """FR : fichier modifié en route : refusé. EN : file altered on the way: refused."""
    archive = make_archive(tmp_path, tokenizer_file)
    with pytest.raises(ChecksumError):
        store.download(_entry(archive, "f" * 64), client=_server(archive.read_bytes()))
    assert not list(store.download_folder.iterdir())


def test_download_cancel_keeps_partial_file(store, tmp_path, tokenizer_file) -> None:
    """FR : annuler garde le début, pour reprendre plus tard. EN : cancel keeps the start."""
    archive = make_archive(tmp_path, tokenizer_file)
    with pytest.raises(DownloadCancelled):
        store.download(
            _entry(archive), client=_server(archive.read_bytes()), should_cancel=lambda: True
        )
    assert list(store.download_folder.glob("*.part"))


def test_download_server_error(store, tmp_path, tokenizer_file) -> None:
    """FR : erreur du serveur : message clair. EN : server error: clear message."""
    archive = make_archive(tmp_path, tokenizer_file)
    with pytest.raises(ModelError, match="404"):
        store.download(_entry(archive), client=_server(b"", status=404))


def test_download_and_install(store, tmp_path, tokenizer_file) -> None:
    """FR : télécharger et installer ; le fichier téléchargé est ensuite effacé.

    EN : download and install; the downloaded file is then erased.
    """
    archive = make_archive(tmp_path, tokenizer_file)
    model = store.download_and_install(_entry(archive), client=_server(archive.read_bytes()))
    assert model.key == ("en", "fr")
    assert not list(store.download_folder.iterdir())


def test_offline_pack_import(store, tmp_path, tokenizer_file) -> None:
    """FR : pack hors-ligne : fichiers vérifiés avec le catalogue, originaux intacts.

    EN : offline pack: files checked against the catalogue, originals intact.
    """
    good = make_archive(tmp_path, tokenizer_file)
    other_dir = tmp_path / "autre"
    other_dir.mkdir()
    unknown = make_archive(other_dir, tokenizer_file, "fr", "en")
    before = good.read_bytes()
    models = store.import_files([good, unknown], [_entry(good)])
    assert {model.key for model in models} == {("en", "fr"), ("fr", "en")}
    assert good.read_bytes() == before
    with pytest.raises(ChecksumError):
        store.import_files([good], [_entry(good, "a" * 64)])


# ----------------------------------------------------------------------
# FR : Moteur local / EN : Local engine
# ----------------------------------------------------------------------
@pytest.fixture
def installed(store, tmp_path, tokenizer_file) -> ModelStore:
    """FR : modèles en→fr, fr→en et en→tr installés. EN : three installed models."""
    for index, (source, target) in enumerate((("en", "fr"), ("fr", "en"), ("en", "tr"))):
        folder = tmp_path / f"a{index}"
        folder.mkdir()
        store.install_archive(make_archive(folder, tokenizer_file, source, target))
    return store


def test_route(installed: ModelStore) -> None:
    """FR : modèle direct, ou passage par l'anglais. EN : direct model, or through English."""
    engine = LocalEngine(installed.packages, translator_factory=EchoTranslator)
    assert [p.to_code for p in engine.route("en", "fr")] == ["fr"]
    assert [(p.from_code, p.to_code) for p in engine.route("fr", "tr")] == [
        ("fr", "en"),
        ("en", "tr"),
    ]
    assert engine.route("tr", "fr") is None
    assert engine.supports("fr", "tr") and engine.supports("ja", "ja")
    assert not engine.supports("tr", "fr")
    with pytest.raises(EngineUnavailable):
        engine.translate(["Hello"], "tr", "fr")


def test_translate_with_real_tokenizer(installed: ModelStore) -> None:
    """FR : texte découpé, traduit (ici recopié) puis recollé, phrase par phrase.

    EN : text split, translated (here copied) then joined back, sentence by sentence.
    """
    engine = LocalEngine(installed.packages, translator_factory=EchoTranslator)
    texts = ["Hello, how are you today? The quick brown fox jumps.", "", "  ", "Bonjour."]
    assert engine.translate(texts, "en", "fr") == texts
    assert engine.translate(["Hello."], "fr", "tr") == ["Hello."]  # FR : par l'anglais
    assert engine.translate(["Same"], "fr", "fr") == ["Same"]


def test_models_kept_in_memory_are_limited(installed: ModelStore) -> None:
    """FR : au plus deux modèles en mémoire (PC de 8 Go). EN : at most two models in memory."""
    EchoTranslator.loads = 0
    engine = LocalEngine(installed.packages, max_loaded=2, translator_factory=EchoTranslator)
    engine.translate(["Hello."], "en", "fr")
    engine.translate(["Hello."], "en", "fr")
    assert EchoTranslator.loads == 1  # FR : chargé une seule fois / EN : loaded once
    engine.translate(["Hello."], "fr", "tr")  # FR : 2 modèles de plus / EN : 2 more models
    assert len(engine._loaded) == 2
    engine.unload()
    assert len(engine._loaded) == 0


def test_target_prefix(tmp_path, store, tokenizer_file) -> None:
    """FR : modèles à « préfixe de langue » : le préfixe est retiré du résultat.

    EN : models with a "language prefix": the prefix is removed from the result.
    """
    store.install_archive(make_archive(tmp_path, tokenizer_file, extra={"target_prefix": "__fr__"}))
    engine = LocalEngine(store.packages, translator_factory=EchoTranslator)
    assert engine.translate(["Hello."], "en", "fr") == ["Hello."]


def test_detokenize_and_sentences() -> None:
    """FR : recollage des morceaux et découpage en phrases. EN : joining pieces and sentences."""
    assert (
        detokenize(["▁Bonjour", ",", "▁comment", "▁allez-vous", "▁?"])
        == "Bonjour, comment allez-vous ?"
    )
    assert detokenize(["▁你好", ",", "你今天好吗", "?"]) == "你好,你今天好吗?"
    assert split_sentences("Hi! How are you? Fine.") == ["Hi!", "How are you?", "Fine."]
    assert split_sentences("Wait... what") == ["Wait...", "what"]
    assert split_sentences("No end") == ["No end"]
    assert split_sentences("こんにちは。元気？") == ["こんにちは。元気？"]


def test_package_read_errors(tmp_path: Path) -> None:
    """FR : dossier de modèle incomplet : erreur claire. EN : incomplete folder: clear error."""
    with pytest.raises(argos.ModelFormatError):
        ArgosPackage.read(tmp_path)


# ----------------------------------------------------------------------
# FR : Page « Modèles de traduction » / EN : "Translation models" page
# ----------------------------------------------------------------------
@pytest.fixture(autouse=True)
def no_blocking_dialogs(monkeypatch) -> list[str]:
    """FR : aucune fenêtre de message ne bloque les tests : elles sont notées.

    EN : no message window blocks the tests: they are recorded instead.
    """
    shown: list[str] = []
    for name in ("warning", "information", "critical"):
        monkeypatch.setattr(QMessageBox, name, lambda _p, title, *a, **k: shown.append(title))
    return shown


@pytest.fixture
def page(qtbot, custom_paths) -> ModelsPage:
    widget = ModelsPage(custom_paths)
    qtbot.addWidget(widget)
    yield widget
    widget.shutdown()


def _wait(qtbot, page: ModelsPage) -> None:
    """FR : attend la fin du travail en arrière-plan. EN : wait for the background job."""
    qtbot.waitUntil(lambda: page.task is None, timeout=10_000)


def test_page_lists_catalogue(page: ModelsPage) -> None:
    """FR : la page liste les modèles, avec les noms des langues. EN : the page lists the models."""
    assert page.table.rowCount() == len(load_catalog())
    page.search_edit.setText("türk")
    visible = [
        page.table.item(row, 0).text()
        for row in range(page.table.rowCount())
        if not page.table.isRowHidden(row)
    ]
    assert visible and all("Türkçe" in text for text in visible)
    assert keep_left_to_right("English → Türkçe") in visible
    assert not page.install_button.isEnabled()  # FR : rien de choisi / EN : nothing chosen
    assert page.try_result.text() == "Installe d'abord un modèle."


def test_page_install_try_and_remove(page, qtbot, monkeypatch, tmp_path, tokenizer_file) -> None:
    """FR : installer, essayer, puis supprimer un modèle depuis la page.

    EN : install, try, then delete a model from the page.
    """
    archive = make_archive(tmp_path, tokenizer_file)

    def fake_download_and_install(entry, progress=None, should_cancel=None, client=None):
        progress(50, 100)
        return page.models.install_archive(archive)

    monkeypatch.setattr(page.models, "download_and_install", fake_download_and_install)
    page.select("en", "fr")
    assert page.install_button.isEnabled()
    page.install_button.click()
    _wait(qtbot, page)
    row = next(
        r
        for r in range(page.table.rowCount())
        if page.table.item(r, 0).text() == keep_left_to_right("English → Français")
    )
    assert page.table.item(row, 2).text() == "Installé"
    assert page.remove_button.isEnabled() and not page.install_button.isEnabled()

    page.engine.translator_factory = EchoTranslator
    page.try_text.setText("Hello, how are you today?")
    page.try_button.click()
    _wait(qtbot, page)
    assert page.try_result.text() == "Hello, how are you today?"

    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    page.remove_button.click()
    assert page.models.installed() == {}


def test_page_import_and_export(page, qtbot, monkeypatch, tmp_path, tokenizer_file) -> None:
    """FR : pack hors-ligne depuis la page : enregistrer pour un autre PC, puis importer.

    EN : offline pack from the page: save for another PC, then import.
    """
    archive = make_archive(tmp_path, tokenizer_file)
    usb = tmp_path / "cle-usb"
    usb.mkdir()
    shown: list[str] = []
    monkeypatch.setattr(QMessageBox, "information", lambda _p, title, *a, **k: shown.append(title))
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *a, **k: str(usb))

    # FR : nom inconnu du catalogue (sinon son empreinte, factice, serait refusée).
    # EN : name unknown to the catalogue (otherwise its fake fingerprint is refused).
    saved_name = "modele-factice.argosmodel"

    def fake_download(entry, destination=None, progress=None, should_cancel=None, client=None):
        target = destination / saved_name
        target.write_bytes(archive.read_bytes())
        return target

    monkeypatch.setattr(page.models, "download", fake_download)
    page.select("en", "fr")
    page.export_button.click()
    _wait(qtbot, page)
    assert (usb / saved_name).is_file()
    assert shown == ["Modèle enregistré"]

    monkeypatch.setattr(
        QFileDialog, "getOpenFileNames", lambda *a, **k: ([str(usb / saved_name)], "")
    )
    page.import_button.click()
    _wait(qtbot, page)
    assert ("en", "fr") in page.models.installed()
    assert shown[-1] == "Modèles importés"


def test_page_refuses_altered_catalogue_file(
    page, qtbot, monkeypatch, tmp_path, tokenizer_file, no_blocking_dialogs
) -> None:
    """FR : un fichier qui porte le nom d'un modèle du catalogue mais dont le
         contenu diffère est refusé à l'import (empreinte vérifiée).
    EN : a file named like a catalogue model but with different content is
         refused on import (fingerprint checked).
    """
    archive = make_archive(tmp_path, tokenizer_file)  # FR : nom réel / EN : real name
    monkeypatch.setattr(QFileDialog, "getOpenFileNames", lambda *a, **k: ([str(archive)], ""))
    page.import_button.click()
    _wait(qtbot, page)
    assert page.models.installed() == {}
    assert no_blocking_dialogs == ["Modèles de traduction"]


def test_page_reports_bad_download(page, qtbot, monkeypatch) -> None:
    """FR : un fichier abîmé est signalé clairement. EN : a damaged file is clearly reported."""
    shown: list[str] = []
    monkeypatch.setattr(QMessageBox, "warning", lambda _p, _t, text, *a, **k: shown.append(text))

    def broken(*args, **kwargs):
        raise ChecksumError("faux")

    monkeypatch.setattr(page.models, "download_and_install", broken)
    page.select("en", "tr")
    page.install_button.click()
    _wait(qtbot, page)
    assert shown and "abîmé" in shown[0]


def test_page_cancel(page, qtbot, monkeypatch) -> None:
    """FR : « Annuler » arrête le téléchargement, sans message d'erreur.

    EN : "Cancel" stops the download, without an error message.
    """
    shown: list[str] = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: shown.append("warning"))

    def slow(entry, progress=None, should_cancel=None, client=None):
        while not should_cancel():
            progress(1, 10)
        raise DownloadCancelled(entry.file_name)

    monkeypatch.setattr(page.models, "download_and_install", slow)
    page.select("en", "es")
    page.install_button.click()
    assert page.cancel_button.isVisible() or page.task is not None
    page.cancel_button.click()
    _wait(qtbot, page)
    assert shown == []


def test_page_model_store_follows_data_folder(custom_paths) -> None:
    """FR : modèles rangés dans le dossier des données. EN : models live in the data folder."""
    store = model_store(custom_paths)
    assert store.folder == custom_paths.data_dir / "models" / "argos"
    assert models_page_module.LocalEngine is LocalEngine


def test_entry_helpers(tmp_path, tokenizer_file) -> None:
    """FR : nom du fichier d'un modèle du catalogue. EN : catalogue model file name."""
    archive = make_archive(tmp_path, tokenizer_file)
    entry = _entry(archive)
    assert entry.file_name == archive.name
    assert replace(entry, tokenizer="bpe").supported is False
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == entry.sha256
