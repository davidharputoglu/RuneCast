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

"""Banc d'essai du moteur local / Local engine benchmark.

FR : Mesure, sur le PC de l'utilisateur, la vitesse de traduction locale
     (phrases par seconde) et la mémoire utilisée, pour plusieurs réglages :
       - le nombre de cœurs du processeur utilisés ;
       - la « largeur de recherche » (beam) : 1 = le plus rapide,
         2 = équilibré, 4 = un peu plus précis mais plus lent.
     Il vérifie aussi que la mémoire reste stable quand on traduit plusieurs
     fois de suite (pas de fuite), puis conseille les meilleurs réglages.
     Les phrases d'essai ressemblent à celles d'un visual novel (écrites pour
     RuneCast, libres de droits).

EN : Measures, on the user's PC, local translation speed (sentences per
     second) and memory used, for several settings: number of processor
     cores used; "search width" (beam): 1 = fastest, 2 = balanced, 4 = a bit
     more accurate but slower. It also checks that memory stays stable when
     translating several times in a row (no leak), then recommends the best
     settings. Test sentences look like a visual novel's (written for
     RuneCast, copyright-free).

     Ce module ne dépend pas de Qt. / This module does not depend on Qt.
"""

import os
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass

from runecast.engines.argos import LocalEngine

# FR : Phrases d'essai, écrites pour RuneCast. EN : Test sentences, written for RuneCast.
SAMPLE_LINES = (
    "Good morning! Did you sleep well?",
    "I can't believe it's already the last day of summer.",
    "Wait for me at the station after class, okay?",
    "The library closes at six, so we should hurry.",
    "Are you sure this is the right way to the old lighthouse?",
    "My grandmother used to tell me stories about this forest.",
    "Hey, don't look at me like that. I'm just being honest.",
    "If we leave now, we can still catch the last train home.",
    "Thank you. I really mean it.",
    "This letter was hidden behind the painting for years.",
    "Why didn't you tell me the truth from the beginning?",
    "The festival starts tonight, and the whole town will be there.",
    "Let's split up. You check the kitchen, and I'll look upstairs.",
    "I'm not angry. I'm just tired of waiting.",
    "Do you remember the promise we made under the cherry tree?",
    "The rain stopped, but the streets are still flooded.",
    "Maybe tomorrow will be different.",
    "She smiled, but her eyes were full of tears.",
    "You should rest. We have a long journey ahead of us.",
    "Nobody knows what happened to the captain after the storm.",
    "Can you hear that? Someone is playing the piano downstairs.",
    "I made too much dinner again. Do you want to stay?",
    "The key must be somewhere in this room.",
    "Please, just listen to me for one minute.",
    "We won the match! I still can't believe it!",
    "The old man pointed at the map and said nothing.",
    "It's dangerous to go out alone at night.",
    "I've been practicing every day since we last met.",
    "What would you like to drink? Tea or coffee?",
    "The door was locked from the inside.",
    "Your answer will change everything.",
    "Let's meet again next spring, when the flowers bloom.",
)

# FR : Largeurs de recherche essayées. EN : Search widths tried.
BEAM_SIZES = (1, 2, 4)


@dataclass(frozen=True)
class BenchmarkResult:
    """Résultat d'un essai / Result of one trial."""

    threads: int
    beam_size: int
    sentences: int
    seconds: float
    memory_mb: float  # FR : mémoire au plus haut pendant l'essai / EN : peak memory

    @property
    def sentences_per_second(self) -> float:
        return self.sentences / self.seconds if self.seconds > 0 else 0.0

    def as_dict(self) -> dict:
        return {**asdict(self), "sentences_per_second": round(self.sentences_per_second, 2)}


@dataclass(frozen=True)
class Recommendation:
    """Réglages conseillés / Recommended settings."""

    threads: int
    beam_size: int
    memory_stable: bool
    memory_growth_mb: float


def physical_cores() -> int:
    """FR : cœurs physiques du processeur. EN : physical processor cores."""
    import psutil

    return psutil.cpu_count(logical=False) or max(1, (os.cpu_count() or 2) // 2)


def thread_options() -> list[int]:
    """FR : nombres de cœurs à essayer (1, 2, 4… jusqu'aux cœurs physiques).

    EN : core counts to try (1, 2, 4… up to the physical cores).
    """
    cores = physical_cores()
    options = [count for count in (1, 2, 4, 6, 8) if count < cores]
    return [*options, cores]


def process_memory_mb() -> float:
    """FR : mémoire utilisée par RuneCast, en Mo. EN : memory used by RuneCast, in MB."""
    import psutil

    return psutil.Process().memory_info().rss / (1024 * 1024)


class _PeakMemory:
    """FR : relève la mémoire au plus haut pendant un essai. EN : record peak memory."""

    def __init__(self) -> None:
        self.peak = process_memory_mb()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._watch, daemon=True)

    def _watch(self) -> None:
        while not self._stop.wait(0.05):
            self.peak = max(self.peak, process_memory_mb())

    def __enter__(self) -> "_PeakMemory":
        self._thread.start()
        return self

    def __exit__(self, *_exc) -> None:
        self._stop.set()
        self._thread.join()
        self.peak = max(self.peak, process_memory_mb())


def run_benchmark(
    make_engine: Callable[[int, int], LocalEngine],
    source_lang: str,
    target_lang: str,
    threads: Sequence[int] | None = None,
    beams: Sequence[int] = BEAM_SIZES,
    lines: Sequence[str] = SAMPLE_LINES,
    progress: Callable[[int, int], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> list[BenchmarkResult]:
    """Essaie chaque réglage / Try each setting.

    FR : « make_engine(cœurs, beam) » fabrique un moteur local. Chaque essai
         commence par une phrase d'échauffement (chargement du modèle), non
         comptée.
    EN : "make_engine(cores, beam)" builds a local engine. Each trial starts
         with a warm-up sentence (model loading), not counted.
    """
    threads = list(threads or thread_options())
    trials = [(count, beam) for count in threads for beam in beams]
    results = []
    for index, (count, beam) in enumerate(trials):
        if should_cancel is not None and should_cancel():
            break
        engine = make_engine(count, beam)
        engine.translate([lines[0]], source_lang, target_lang)
        with _PeakMemory() as memory:
            start = time.perf_counter()
            engine.translate(list(lines), source_lang, target_lang)
            seconds = time.perf_counter() - start
        engine.unload()
        results.append(BenchmarkResult(count, beam, len(lines), seconds, round(memory.peak, 1)))
        if progress is not None:
            progress(index + 1, len(trials))
    return results


def memory_growth(
    engine: LocalEngine,
    source_lang: str,
    target_lang: str,
    rounds: int = 3,
    lines: Sequence[str] = SAMPLE_LINES,
) -> float:
    """FR : croissance de la mémoire (Mo) entre le 1er et le dernier tour.

         Si elle reste faible, la mémoire est stable : pas de fuite.
    EN : memory growth (MB) between the first and last round. If it stays
         small, memory is stable: no leak.
    """
    measures = []
    for _round in range(rounds):
        engine.translate(list(lines), source_lang, target_lang)
        measures.append(process_memory_mb())
    return round(measures[-1] - measures[0], 1)


def recommend(results: Sequence[BenchmarkResult], growth_mb: float = 0.0) -> Recommendation:
    """Choisit les réglages conseillés / Choose the recommended settings.

    FR : Largeur 2 (bon équilibre qualité/vitesse) si elle traduit au moins
         4 phrases par seconde, sinon 1. Puis le plus petit nombre de cœurs
         qui donne au moins 90 % de la meilleure vitesse : inutile d'occuper
         tout le processeur pour presque rien. Mémoire stable si elle grandit
         de moins de 50 Mo en trois tours.
    EN : Width 2 (good quality/speed balance) if it translates at least 4
         sentences per second, otherwise 1. Then the smallest core count
         giving at least 90 % of the best speed: no point occupying the whole
         processor for almost nothing. Memory stable if it grows by less than
         50 MB over three rounds.
    """
    if not results:
        raise ValueError("aucun résultat / no result")
    beam = 2 if any(r.beam_size == 2 and r.sentences_per_second >= 4 for r in results) else 1
    candidates = [r for r in results if r.beam_size == beam] or list(results)
    best = max(r.sentences_per_second for r in candidates)
    good = [r for r in candidates if r.sentences_per_second >= 0.9 * best]
    threads = min(r.threads for r in good)
    return Recommendation(threads, beam, growth_mb < 50, growth_mb)
