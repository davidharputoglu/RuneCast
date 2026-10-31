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

"""Modèle étendu NLLB-200 (local, optionnel) / NLLB-200 extended model (local, optional).

FR : NLLB-200 (« No Language Left Behind », de Meta) traduit directement
     entre 200 langues, dont le kazakh, l'ouzbek, le turkmène, le tatar et
     l'ouïghour, que les modèles Argos ne couvrent pas. RuneCast utilise la
     version « distillée 600M » convertie pour CTranslate2 en int8 (environ
     630 Mo sur le disque, 1 à 1,5 Go de mémoire pendant la traduction).
     Licence CC-BY-NC 4.0 : usage NON COMMERCIAL seulement ; Meta le présente
     comme un modèle de recherche. Il n'est donc téléchargé qu'après
     acceptation explicite de cette licence par l'utilisateur.
     Les fichiers viennent d'une version précise (« révision ») d'un dépôt
     Hugging Face, et chaque fichier est vérifié par son empreinte SHA-256.

EN : NLLB-200 ("No Language Left Behind", by Meta) translates directly
     between 200 languages, including Kazakh, Uzbek, Turkmen, Tatar and
     Uyghur, which Argos models do not cover. RuneCast uses the "distilled
     600M" version converted for CTranslate2 in int8 (about 630 MB on disk,
     1 to 1.5 GB of memory while translating). CC-BY-NC 4.0 license:
     NON-COMMERCIAL use only; Meta presents it as a research model. It is
     therefore downloaded only after the user explicitly accepts this
     license. Files come from one precise version ("revision") of a Hugging
     Face repository, and each file is checked by its SHA-256 fingerprint.

     Ce module ne dépend pas de Qt. / This module does not depend on Qt.
"""

import json
import logging
import shutil
import threading
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from runecast.engines.argos import NO_SPACE_LANGUAGES, default_threads, detokenize, split_sentences
from runecast.engines.base import Engine, EngineUnavailable
from runecast.engines.models import (
    CatalogEntry,
    ModelError,
    ModelStore,
    Progress,
    file_sha256,
)
from runecast.resources import resource_path

logger = logging.getLogger(__name__)

# FR : Fichiers indispensables du modèle. EN : Required model files.
MODEL_FILE = "model.bin"
TOKENIZER_FILE = "sentencepiece.bpe.model"
INSTALL_FILE = "runecast-install.json"
FOLDER_NAME = "nllb-200-distilled-600M"

# FR : Codes NLLB (FLORES-200) des langues proposées. Les 15 langues de
#      l'interface y sont, plus les langues de jeux les plus courantes.
# EN : NLLB (FLORES-200) codes of the offered languages: the 15 interface
#      languages, plus the most common game languages.
NLLB_CODES = {
    "en": "eng_Latn",
    "fr": "fra_Latn",
    "es": "spa_Latn",
    "pt": "por_Latn",
    "pt-BR": "por_Latn",
    "it": "ita_Latn",
    "de": "deu_Latn",
    "nl": "nld_Latn",
    "pl": "pol_Latn",
    "cs": "ces_Latn",
    "ro": "ron_Latn",
    "hu": "hun_Latn",
    "sv": "swe_Latn",
    "da": "dan_Latn",
    "fi": "fin_Latn",
    "el": "ell_Grek",
    "ru": "rus_Cyrl",
    "uk": "ukr_Cyrl",
    "bg": "bul_Cyrl",
    "ar": "arb_Arab",
    "fa": "pes_Arab",
    "he": "heb_Hebr",
    "hi": "hin_Deva",
    "id": "ind_Latn",
    "ms": "zsm_Latn",
    "vi": "vie_Latn",
    "th": "tha_Thai",
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "zh": "zho_Hans",
    "zh-Hant": "zho_Hant",
    "tr": "tur_Latn",
    "az": "azj_Latn",
    "uz": "uzn_Latn",
    "kk": "kaz_Cyrl",
    "tk": "tuk_Latn",
    "ky": "kir_Cyrl",
    "tt": "tat_Cyrl",
    "ug": "uig_Arab",
}


@dataclass(frozen=True)
class NllbFile:
    """Un fichier du modèle / One model file."""

    name: str
    size: int | None
    sha256: str | None


@dataclass(frozen=True)
class NllbCatalog:
    """Où trouver le modèle / Where to find the model."""

    name: str
    license: str
    license_url: str
    source: str
    repository: str
    revision: str
    files: tuple[NllbFile, ...]

    def url(self, file: NllbFile) -> str:
        """FR : adresse figée d'un fichier (révision précise). EN : pinned file address."""
        return f"{self.repository}/resolve/{self.revision}/{file.name}"

    @property
    def total_size(self) -> int:
        return sum(file.size or 0 for file in self.files)


def load_nllb_catalog(path: Path | None = None) -> NllbCatalog:
    """FR : lit la fiche du modèle NLLB. EN : read the NLLB model sheet."""
    data = json.loads(
        (path or resource_path("models", "nllb-catalog.json")).read_text(encoding="utf-8")
    )
    return NllbCatalog(
        name=data["name"],
        license=data["license"],
        license_url=data["license_url"],
        source=data["source"],
        repository=data["repository"],
        revision=data["revision"],
        files=tuple(NllbFile(f["name"], f.get("size"), f.get("sha256")) for f in data["files"]),
    )


def nllb_folder(data_dir: Path) -> Path:
    """FR : dossier du modèle NLLB. EN : NLLB model folder."""
    return data_dir / "models" / FOLDER_NAME


class NllbStore:
    """Installation du modèle NLLB / NLLB model installation."""

    def __init__(self, folder: Path, download_folder: Path, catalog: NllbCatalog | None = None):
        self.folder = folder
        self.download_folder = download_folder
        self.catalog = catalog or load_nllb_catalog()

    def installed(self) -> bool:
        """FR : le modèle est-il installé et complet ? EN : is the model installed and complete?"""
        return (self.folder / INSTALL_FILE).is_file() and all(
            (self.folder / file.name).is_file() for file in self.catalog.files
        )

    def size(self) -> int:
        """FR : place occupée sur le disque. EN : space used on disk."""
        if not self.folder.is_dir():
            return 0
        return sum(item.stat().st_size for item in self.folder.iterdir() if item.is_file())

    def install(
        self,
        progress: Progress | None = None,
        should_cancel: Callable[[], bool] | None = None,
        client=None,
    ) -> None:
        """Télécharge et installe le modèle / Download and install the model.

        FR : Chaque fichier est téléchargé (avec reprise) et vérifié. Le modèle
             n'est mis en place que lorsque tous les fichiers sont bons.
        EN : Each file is downloaded (with resume) and checked. The model is
             put in place only when all files are good.
        """
        store = ModelStore(self.folder.parent, self.download_folder / FOLDER_NAME)
        total = self.catalog.total_size
        done_before = 0
        downloaded = []
        for file in self.catalog.files:
            entry = CatalogEntry(
                code=FOLDER_NAME,
                from_code="",
                to_code="",
                from_name="",
                to_name="",
                version=self.catalog.revision,
                url=self.catalog.url(file),
                size=file.size,
                sha256=file.sha256,
            )
            offset = done_before

            def file_progress(done: int, _total: int, offset: int = offset) -> None:
                if progress is not None:
                    progress(offset + done, total)

            downloaded.append(store.download(entry, None, file_progress, should_cancel, client))
            done_before += file.size or downloaded[-1].stat().st_size
        work = self.folder.parent / f".installation-{uuid.uuid4().hex}"
        work.mkdir(parents=True)
        try:
            for path in downloaded:
                shutil.move(str(path), work / path.name)
            (work / INSTALL_FILE).write_text(
                json.dumps(
                    {
                        "revision": self.catalog.revision,
                        "license": self.catalog.license,
                        "installed_at": datetime.now(UTC).isoformat(timespec="seconds"),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            if self.folder.exists():
                shutil.rmtree(self.folder)
            work.rename(self.folder)
        finally:
            shutil.rmtree(work, ignore_errors=True)
        logger.info("Modèle NLLB-200 installé / NLLB-200 model installed")

    def remove(self) -> None:
        """FR : supprime le modèle. EN : delete the model."""
        if self.folder.exists():
            shutil.rmtree(self.folder)
            logger.info("Modèle NLLB-200 supprimé / NLLB-200 model deleted")

    def verify(self) -> bool:
        """FR : revérifie les empreintes des fichiers installés. EN : re-check fingerprints."""
        for file in self.catalog.files:
            path = self.folder / file.name
            if not path.is_file() or (file.sha256 and file_sha256(path) != file.sha256):
                return False
        return True


class NllbEngine(Engine):
    """Moteur NLLB-200 local / Local NLLB-200 engine."""

    engine_id = "nllb"
    online = False

    def __init__(
        self,
        store: NllbStore,
        threads: int | None = None,
        beam_size: int = 2,
        translator_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.store = store
        self.threads = threads or default_threads()
        self.beam_size = beam_size
        self.translator_factory = translator_factory
        self._model: tuple[Any, Any] | None = None
        self._lock = threading.Lock()

    def supports(self, source_lang: str, target_lang: str) -> bool:
        return self.store.installed() and source_lang in NLLB_CODES and target_lang in NLLB_CODES

    def translate(self, texts: Sequence[str], source_lang: str, target_lang: str) -> list[str]:
        if not self.supports(source_lang, target_lang):
            raise EngineUnavailable(
                f"NLLB-200 : non installé ou langue absente / not installed or language "
                f"missing ({source_lang} → {target_lang})"
            )
        if source_lang == target_lang:
            return list(texts)
        source_code, target_code = NLLB_CODES[source_lang], NLLB_CODES[target_lang]
        sentences: list[str] = []
        spans: list[tuple[int, int]] = []
        for text in texts:
            parts = split_sentences(text) if text.strip() else []
            spans.append((len(sentences), len(parts)))
            sentences.extend(parts)
        translated: list[str] = []
        if sentences:
            with self._lock:
                tokenizer, translator = self._load()
                batch = [
                    [source_code, *tokenizer.encode(sentence, out_type=str), "</s>"]
                    for sentence in sentences
                ]
                results = translator.translate_batch(
                    batch,
                    target_prefix=[[target_code]] * len(batch),
                    beam_size=self.beam_size,
                    max_batch_size=16,
                    max_decoding_length=256,
                )
            for result in results:
                pieces = [piece for piece in result.hypotheses[0] if piece != target_code]
                translated.append(detokenize(pieces))
        joiner = "" if target_lang in NO_SPACE_LANGUAGES else " "
        return [
            joiner.join(translated[start : start + count]) if count else text
            for text, (start, count) in zip(texts, spans, strict=True)
        ]

    def _load(self) -> tuple[Any, Any]:
        """FR : charge le modèle à la première traduction. EN : load the model on first use."""
        if self._model is None:
            import ctranslate2
            import sentencepiece

            logger.info(
                "Chargement de NLLB-200 / Loading NLLB-200 (%s cœurs / cores)", self.threads
            )
            tokenizer = sentencepiece.SentencePieceProcessor(
                model_file=str(self.store.folder / TOKENIZER_FILE)
            )
            factory = self.translator_factory or ctranslate2.Translator
            translator = factory(
                str(self.store.folder),
                device="cpu",
                compute_type="int8",
                inter_threads=1,
                intra_threads=self.threads,
            )
            self._model = (tokenizer, translator)
        return self._model

    def unload(self) -> None:
        """FR : libère la mémoire (environ 1 Go). EN : free the memory (about 1 GB)."""
        with self._lock:
            self._model = None

    def configure(self, threads: int | None, beam_size: int) -> None:
        """FR : change les réglages de performance. EN : change performance settings."""
        new_threads = threads or default_threads()
        if (new_threads, beam_size) != (self.threads, self.beam_size):
            self.unload()
            self.threads, self.beam_size = new_threads, beam_size


def with_known_sizes(catalog: NllbCatalog, results: dict[str, dict]) -> NllbCatalog:
    """FR : fiche complétée avec les tailles et empreintes mesurées.

    EN : sheet completed with the measured sizes and fingerprints.
    """
    files = tuple(
        replace(file, size=results[file.name]["size"], sha256=results[file.name]["sha256"])
        if file.name in results
        else file
        for file in catalog.files
    )
    return replace(catalog, files=files)


__all__ = [
    "ModelError",
    "NLLB_CODES",
    "NllbCatalog",
    "NllbEngine",
    "NllbStore",
    "load_nllb_catalog",
    "nllb_folder",
]
