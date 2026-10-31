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

"""Moteur local : modèles Argos / Local engine: Argos models.

FR : Traduit sur le PC, sans internet, avec les modèles libres du projet
     Argos Translate. RuneCast n'utilise pas la bibliothèque argostranslate
     (trop lourde : elle entraîne PyTorch) mais lit directement ses fichiers
     de modèles avec deux petites bibliothèques :
       - CTranslate2 : fait tourner le modèle sur le processeur, en « int8 »
         (nombres compacts : moins de mémoire, plus rapide, pas de GPU) ;
       - SentencePiece : découpe le texte en morceaux que le modèle comprend.
     Chaque modèle traduit dans UN sens (anglais → français, par exemple).
     S'il n'existe pas de modèle direct, RuneCast passe par l'anglais
     (français → anglais → turc). Au plus deux modèles sont gardés en mémoire
     en même temps, pour rester léger sur un PC de 8 Go.

EN : Translates on the PC, without internet, with the free models of the
     Argos Translate project. RuneCast does not use the argostranslate
     library (too heavy: it pulls PyTorch) but reads its model files
     directly with two small libraries: CTranslate2 runs the model on the
     processor in "int8" (compact numbers: less memory, faster, no GPU);
     SentencePiece cuts the text into pieces the model understands. Each
     model translates ONE way (English → French, for instance). When no
     direct model exists, RuneCast goes through English (French → English →
     Turkish). At most two models are kept in memory at the same time, to
     stay light on an 8 GB PC.
"""

import json
import logging
import os
import re
import threading
from collections import OrderedDict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runecast.engines.base import Engine, EngineUnavailable, TranslationError

logger = logging.getLogger(__name__)

# FR : Langue de passage quand il n'y a pas de modèle direct.
# EN : Go-between language when there is no direct model.
PIVOT_LANGUAGE = "en"

# FR : Fichiers d'un modèle Argos. EN : Files of an Argos model.
METADATA_FILE = "metadata.json"
MODEL_FOLDER = "model"
MODEL_WEIGHTS = "model.bin"
SENTENCEPIECE_FILE = "sentencepiece.model"

# FR : Codes de langue d'Argos qui diffèrent de ceux de RuneCast.
# EN : Argos language codes that differ from RuneCast's.
ARGOS_CODES = {"pt-BR": "pb", "zh-Hant": "zt"}
RUNECAST_CODES = {argos: runecast for runecast, argos in ARGOS_CODES.items()}

# FR : Langues écrites sans espace entre les phrases. EN : Languages without spaces.
NO_SPACE_LANGUAGES = frozenset({"ja", "zh", "zh-Hant", "th"})

# FR : Fin de phrase : . ! ? … (et leurs versions chinoises/japonaises).
# EN : End of sentence: . ! ? … (and their Chinese/Japanese versions).
_SENTENCE_END = re.compile(r"(?<=[.!?…。！？])\s+")


class ModelFormatError(TranslationError):
    """FR : fichiers de modèle incomplets ou d'un format inconnu.

    EN : model files incomplete or of an unknown format.
    """


def to_argos(code: str) -> str:
    """FR : code RuneCast → code Argos (« pt-BR » → « pb »). EN : RuneCast → Argos code."""
    return ARGOS_CODES.get(code, code)


def from_argos(code: str) -> str:
    """FR : code Argos → code RuneCast (« pb » → « pt-BR »). EN : Argos → RuneCast code."""
    return RUNECAST_CODES.get(code, code)


@dataclass(frozen=True)
class ArgosPackage:
    """Un modèle Argos installé / An installed Argos model."""

    folder: Path
    from_code: str  # FR : code RuneCast / EN : RuneCast code
    to_code: str
    version: str
    target_prefix: str = ""

    @classmethod
    def read(cls, folder: Path) -> "ArgosPackage":
        """FR : lit et vérifie un dossier de modèle. EN : read and check a model folder."""
        try:
            metadata: dict[str, Any] = json.loads(
                (folder / METADATA_FILE).read_text(encoding="utf-8")
            )
        except (OSError, ValueError) as error:
            raise ModelFormatError(f"{folder}: {METADATA_FILE} illisible / unreadable") from error
        for required in (folder / MODEL_FOLDER / MODEL_WEIGHTS, folder / SENTENCEPIECE_FILE):
            if not required.is_file():
                raise ModelFormatError(f"{folder}: fichier manquant / missing file {required.name}")
        try:
            return cls(
                folder=folder,
                from_code=from_argos(str(metadata["from_code"])),
                to_code=from_argos(str(metadata["to_code"])),
                version=str(metadata.get("package_version", "")),
                target_prefix=str(metadata.get("target_prefix") or ""),
            )
        except KeyError as error:
            raise ModelFormatError(f"{folder}: {METADATA_FILE} incomplet / incomplete") from error


def default_threads() -> int:
    """Nombre de cœurs utilisés / Number of cores used.

    FR : La moitié des cœurs logiques (environ les cœurs physiques), entre 1
         et 4 : RuneCast traduit vite sans figer le reste du PC. Réglé
         finement à l'étape 14 (banc d'essai).
    EN : Half of the logical cores (about the physical cores), between 1 and
         4: RuneCast translates fast without freezing the rest of the PC.
         Fine-tuned in step 14 (benchmark).
    """
    return max(1, min(4, (os.cpu_count() or 2) // 2))


def detokenize(pieces: Sequence[str]) -> str:
    """Recolle les morceaux traduits / Join the translated pieces.

    FR : Le modèle renvoie des morceaux où « ▁ » marque un début de mot :
         ["▁Bonjour", ",", "▁comment"] → « Bonjour, comment ». On recolle à
         la main (comme Argos) : le découpeur de la langue d'origine ne
         connaît pas forcément les morceaux de la langue traduite.
    EN : The model returns pieces where "▁" marks the start of a word:
         ["▁Bonjour", ",", "▁comment"] → "Bonjour, comment". They are joined
         by hand (as Argos does): the source language's splitter does not
         necessarily know the translated language's pieces.
    """
    return "".join(pieces).replace("▁", " ").strip()


def split_sentences(text: str) -> list[str]:
    """FR : découpe un texte en phrases. EN : split a text into sentences."""
    parts = [part for part in _SENTENCE_END.split(text.strip()) if part]
    return parts or [text]


class ArgosTranslator:
    """Un modèle chargé en mémoire / A model loaded in memory."""

    def __init__(
        self,
        package: ArgosPackage,
        threads: int,
        beam_size: int,
        translator_factory: Callable[..., Any] | None = None,
    ) -> None:
        import ctranslate2
        import sentencepiece

        self.package = package
        self.beam_size = beam_size
        self.tokenizer = sentencepiece.SentencePieceProcessor(
            model_file=str(package.folder / SENTENCEPIECE_FILE)
        )
        factory = translator_factory or ctranslate2.Translator
        self.translator = factory(
            str(package.folder / MODEL_FOLDER),
            device="cpu",
            compute_type="int8",
            inter_threads=1,
            intra_threads=threads,
        )

    def translate(self, texts: Sequence[str]) -> list[str]:
        """FR : traduit des textes (découpés en phrases). EN : translate texts (by sentence)."""
        sentences: list[str] = []
        spans: list[tuple[int, int]] = []
        for text in texts:
            parts = split_sentences(text) if text.strip() else []
            spans.append((len(sentences), len(parts)))
            sentences.extend(parts)
        translated: list[str] = []
        if sentences:
            tokens = [self.tokenizer.encode(sentence, out_type=str) for sentence in sentences]
            prefix = self.package.target_prefix
            results = self.translator.translate_batch(
                tokens,
                target_prefix=[[prefix]] * len(tokens) if prefix else None,
                beam_size=self.beam_size,
                max_batch_size=32,
                replace_unknowns=True,
                max_decoding_length=256,
            )
            for result in results:
                hypothesis = list(result.hypotheses[0])
                if prefix and hypothesis[:1] == [prefix]:
                    hypothesis = hypothesis[1:]
                translated.append(detokenize(hypothesis))
        joiner = "" if self.package.to_code in NO_SPACE_LANGUAGES else " "
        return [
            joiner.join(translated[start : start + count]) if count else text
            for text, (start, count) in zip(texts, spans, strict=True)
        ]


class LocalEngine(Engine):
    """Moteur de traduction locale / Local translation engine."""

    engine_id = "local"
    online = False

    def __init__(
        self,
        packages: Callable[[], dict[tuple[str, str], ArgosPackage]],
        threads: int | None = None,
        beam_size: int = 2,
        max_loaded: int = 2,
        translator_factory: Callable[..., Any] | None = None,
    ) -> None:
        # FR : « packages » donne les modèles installés (relu à chaque fois :
        #      un modèle peut être installé pendant que RuneCast tourne).
        # EN : "packages" gives the installed models (read every time: a
        #      model can be installed while RuneCast is running).
        self.packages = packages
        self.threads = threads or default_threads()
        self.beam_size = beam_size
        self.max_loaded = max_loaded
        self.translator_factory = translator_factory
        self._loaded: OrderedDict[Path, ArgosTranslator] = OrderedDict()
        self._lock = threading.Lock()

    def route(self, source_lang: str, target_lang: str) -> list[ArgosPackage] | None:
        """FR : modèles à enchaîner (direct, ou par l'anglais), ou None.

        EN : models to chain (direct, or through English), or None.
        """
        installed = self.packages()
        direct = installed.get((source_lang, target_lang))
        if direct is not None:
            return [direct]
        first = installed.get((source_lang, PIVOT_LANGUAGE))
        second = installed.get((PIVOT_LANGUAGE, target_lang))
        if first is not None and second is not None:
            return [first, second]
        return None

    def supports(self, source_lang: str, target_lang: str) -> bool:
        return source_lang == target_lang or self.route(source_lang, target_lang) is not None

    def translate(self, texts: Sequence[str], source_lang: str, target_lang: str) -> list[str]:
        if source_lang == target_lang:
            return list(texts)
        route = self.route(source_lang, target_lang)
        if route is None:
            raise EngineUnavailable(
                f"aucun modèle local pour / no local model for {source_lang} → {target_lang}"
            )
        results = list(texts)
        with self._lock:
            for package in route:
                results = self._translator(package).translate(results)
        return results

    def _translator(self, package: ArgosPackage) -> ArgosTranslator:
        """FR : modèle chargé (au plus « max_loaded » en mémoire).

        EN : loaded model (at most "max_loaded" in memory).
        """
        if package.folder in self._loaded:
            self._loaded.move_to_end(package.folder)
            return self._loaded[package.folder]
        while len(self._loaded) >= self.max_loaded:
            folder, _translator = self._loaded.popitem(last=False)
            logger.info("Modèle libéré / Model unloaded: %s", folder.name)
        logger.info(
            "Chargement du modèle / Loading model %s → %s (%s cœurs / cores)",
            package.from_code,
            package.to_code,
            self.threads,
        )
        try:
            translator = ArgosTranslator(
                package, self.threads, self.beam_size, self.translator_factory
            )
        except (OSError, RuntimeError, ValueError) as error:
            raise ModelFormatError(f"{package.folder}: {error}") from error
        self._loaded[package.folder] = translator
        return translator

    def unload(self) -> None:
        """FR : libère la mémoire des modèles chargés. EN : free the loaded models' memory."""
        with self._lock:
            self._loaded.clear()

    def configure(self, threads: int | None, beam_size: int) -> None:
        """FR : change les réglages (cœurs, largeur de recherche) ; les modèles
             chargés sont libérés pour être rechargés avec ces réglages.
        EN : change the settings (cores, search width); loaded models are
             freed to be reloaded with these settings.
        """
        new_threads = threads or default_threads()
        if (new_threads, beam_size) != (self.threads, self.beam_size):
            self.unload()
            self.threads, self.beam_size = new_threads, beam_size
