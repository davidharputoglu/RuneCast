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

"""Chaîne de traduction avec repli automatique / Translation chain with automatic fallback.

FR : C'est ici que tout se rejoint : protection des balises (étape 11),
     cache (étape 12), moteurs locaux (étapes 13 et 15) et en ligne (16).
       - MODE EN LIGNE : RuneCast essaie les moteurs cochés, dans l'ordre
         choisi. Si l'un ne répond pas (internet coupé, limite atteinte, clé
         refusée, service en panne), il est mis de côté pour la suite du
         travail et le suivant prend le relais ; en dernier recours, la
         traduction locale. Le travail avance par petits paquets : si le
         Wi-Fi est coupé en pleine traduction, seul le paquet en cours est
         repris, en local.
       - MODE LOCAL : seuls les moteurs locaux sont utilisés, et un verrou
         empêche toute connexion vers un service de traduction. (Internet
         reste utilisable pour les mises à jour et les modèles.)
     Chaque ligne indique quel moteur l'a traduite, ou « cache ». Une ligne
     dont les balises n'ont pas survécu est marquée « à vérifier ».

EN : This is where everything meets: tag protection (step 11), cache (step
     12), local engines (steps 13 and 15) and online engines (16). ONLINE
     MODE: RuneCast tries the checked engines in the chosen order. If one
     does not answer (internet cut, limit reached, key refused, service
     down), it is set aside for the rest of the job and the next one takes
     over; as a last resort, local translation. Work goes in small chunks:
     if Wi-Fi is cut mid-translation, only the current chunk is redone,
     locally. LOCAL MODE: only local engines are used, and a lock prevents
     any connection to a translation service (internet stays usable for
     updates and models). Each line says which engine translated it, or
     "cache". A line whose tags did not survive is marked "to check".

     Ce module ne dépend pas de Qt. / This module does not depend on Qt.
"""

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from runecast.core.cache import ORIGIN_CACHE, ORIGIN_ENGINE, TranslationCache
from runecast.core.paths import AppPaths
from runecast.core.protect import protect, restore
from runecast.core.secrets import KeyStore
from runecast.core.settings import Settings
from runecast.engines.argos import LocalEngine
from runecast.engines.base import Engine, EngineUnavailable, TranslationError
from runecast.engines.models import ModelStore, models_folder
from runecast.engines.nllb import NllbEngine, NllbStore, nllb_folder
from runecast.engines.online import (
    ENGINE_CLASSES,
    allow_online_translation,
    create_engine,
)

logger = logging.getLogger(__name__)

# FR : Modes de traduction. EN : Translation modes.
MODE_ONLINE = "online"
MODE_LOCAL = "local"
# FR : Taille des paquets de lignes. EN : Size of line chunks.
CHUNK_SIZE = 20
# FR : Nom donné aux traductions reprises du cache. EN : Name for cached translations.
FROM_CACHE = "cache"


@dataclass
class LineResult:
    """Résultat d'une ligne / Result of one line."""

    source: str
    text: str
    ok: bool
    engine: str  # FR : moteur utilisé, ou « cache » / EN : engine used, or "cache"
    problems: list[str] = field(default_factory=list)


@dataclass
class ChainEvent:
    """Un moteur mis de côté pendant le travail / An engine set aside during the job."""

    engine: str
    reason: str


class EngineChain:
    """Moteurs à essayer dans l'ordre / Engines to try in order."""

    def __init__(
        self,
        online_engines: Sequence[Engine],
        local_engines: Sequence[Engine],
        mode: str = MODE_ONLINE,
    ) -> None:
        self.mode = mode
        # FR : en mode local, les moteurs en ligne ne sont même pas gardés.
        # EN : in local mode, online engines are not even kept.
        online = [] if mode == MODE_LOCAL else [e for e in online_engines if e.online]
        self.engines: list[Engine] = [*online, *[e for e in local_engines if not e.online]]
        self.events: list[ChainEvent] = []
        self._down: set[str] = set()

    def candidates(self, source_lang: str, target_lang: str) -> list[Engine]:
        """FR : moteurs encore disponibles pour ces langues. EN : engines still available."""
        return [
            engine
            for engine in self.engines
            if engine.engine_id not in self._down and engine.supports(source_lang, target_lang)
        ]

    def set_aside(self, engine: Engine, reason: str) -> None:
        """FR : met un moteur de côté pour la suite du travail. EN : set an engine aside."""
        self._down.add(engine.engine_id)
        self.events.append(ChainEvent(engine.engine_id, reason))
        logger.warning(
            "Moteur %s indisponible (%s) : passage au suivant / unavailable, moving on",
            engine.engine_id,
            reason,
        )

    def translate_lines(
        self, lines: Sequence[str], source_lang: str, target_lang: str
    ) -> list[LineResult]:
        """Traduit un paquet de lignes / Translate a chunk of lines.

        FR : Essaie chaque moteur disponible jusqu'à ce que l'un réussisse.
        EN : Tries each available engine until one succeeds.
        """
        for engine in self.candidates(source_lang, target_lang):
            protected = [protect(line, engine.marker_style) for line in lines]
            to_send = [p.masked for p in protected if p.translatable]
            try:
                answer = engine.translate(to_send, source_lang, target_lang)
                if len(answer) != len(to_send):
                    raise TranslationError("réponse incomplète / incomplete answer")
            except (EngineUnavailable, TranslationError) as error:
                self.set_aside(engine, getattr(error, "reason", "") or str(error))
                continue
            translated = iter(answer)
            results = []
            for line, item in zip(lines, protected, strict=True):
                if not item.translatable:
                    results.append(LineResult(line, line, True, engine.engine_id))
                    continue
                restored = restore(next(translated), item)
                results.append(
                    LineResult(
                        line, restored.text, restored.ok, engine.engine_id, restored.problems
                    )
                )
            return results
        raise EngineUnavailable(
            f"aucun moteur disponible pour / no engine available for {source_lang} → {target_lang}"
        )


def translate_texts(
    texts: Sequence[str],
    source_lang: str,
    target_lang: str,
    chain: EngineChain,
    cache: TranslationCache | None = None,
    game: str = "",
    progress: Callable[[int, int], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
    chunk_size: int = CHUNK_SIZE,
) -> list[LineResult | None]:
    """Traduit des lignes, avec cache et repli / Translate lines, with cache and fallback.

    FR : Les lignes identiques ne sont traduites qu'une fois ; celles déjà
         dans le cache n'en sortent pas. En cas d'annulation, les lignes non
         traduites valent None. Seules les traductions sans problème entrent
         dans le cache.
    EN : Identical lines are translated once; those already in the cache are
         taken from it. If cancelled, untranslated lines are None. Only
         problem-free translations enter the cache.
    """
    unique = list(dict.fromkeys(texts))
    results: dict[str, LineResult] = {}
    if cache is not None:
        for source, text in cache.get_many(unique, source_lang, target_lang).items():
            results[source] = LineResult(source, text, True, FROM_CACHE)
        if results:
            cache.record_many(
                [(r.source, r.text) for r in results.values()],
                source_lang,
                target_lang,
                FROM_CACHE,
                ORIGIN_CACHE,
                game,
            )
    pending = [source for source in unique if source not in results]
    done = len(results)
    if progress is not None:
        progress(done, len(unique))
    for start in range(0, len(pending), chunk_size):
        if should_cancel is not None and should_cancel():
            break
        chunk = pending[start : start + chunk_size]
        for result in chain.translate_lines(chunk, source_lang, target_lang):
            results[result.source] = result
            if cache is not None and result.ok:
                cache.put(result.source, result.text, source_lang, target_lang, result.engine)
                cache.record(
                    result.source,
                    result.text,
                    source_lang,
                    target_lang,
                    result.engine,
                    ORIGIN_ENGINE,
                    game,
                )
        done += len(chunk)
        if progress is not None:
            progress(done, len(unique))
    engines = {r.engine for r in results.values()}
    logger.info(
        "%s ligne(s) traduite(s) / line(s) translated (%s), %s à vérifier / to check",
        len(results),
        ", ".join(sorted(engines)) or "-",
        sum(not r.ok for r in results.values()),
    )
    return [results.get(text) for text in texts]


def build_chain(settings: Settings, paths: AppPaths) -> EngineChain:
    """Prépare la chaîne selon les réglages / Build the chain from the settings.

    FR : Moteurs en ligne cochés (dans l'ordre), puis modèles Argos, puis
         NLLB-200. En mode local, le verrou réseau est fermé.
    EN : Checked online engines (in order), then Argos models, then NLLB-200.
         In local mode, the network lock is closed.
    """
    local_only = settings.translation_mode == MODE_LOCAL
    allow_online_translation(not local_only)
    threads, beam = settings.local_threads or None, settings.local_beam_size
    models = ModelStore(models_folder(paths.data_dir), paths.cache_dir / "downloads")
    nllb = NllbStore(nllb_folder(paths.data_dir), paths.cache_dir / "downloads")
    local = [
        LocalEngine(models.packages, threads=threads, beam_size=beam),
        NllbEngine(nllb, threads=threads, beam_size=beam),
    ]
    online: list[Engine] = []
    if not local_only:
        keys = KeyStore(paths.config_dir, portable=paths.portable)
        for engine_id in settings.engine_order:
            if engine_id not in settings.engines_enabled or engine_id not in ENGINE_CLASSES:
                continue
            key = keys.get(engine_id) if "key" in ENGINE_CLASSES[engine_id].info.fields else ""
            online.append(create_engine(engine_id, key, settings.engine_options.get(engine_id)))
    return EngineChain(online, local, settings.translation_mode)
