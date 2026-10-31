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

"""Cache et historique des traductions / Translation cache and history.

FR : Une base de données SQLite (fichier translations.sqlite3 du dossier des
     données) garde :
       - le CACHE : chaque phrase déjà traduite, par moteur et par paire de
         langues. Une phrase identique n'est jamais retraduite : la
         traduction est reprise du cache (plus rapide, et gratuit avec les
         moteurs payants). Le journal indique combien de phrases viennent du
         cache ;
       - l'HISTORIQUE : ce qui a été traduit, quand, par quel moteur, pour
         quel jeu, et d'où vient la traduction (moteur, cache, correction à
         la main…).
     Sécurité : le fichier porte un numéro de version (migrations sans
     perte) ; un fichier abîmé est mis de côté (jamais effacé) et un nouveau
     est créé. Plusieurs traductions peuvent l'utiliser en même temps.

EN : A SQLite database (translations.sqlite3 file in the data folder) keeps:
       - the CACHE: every sentence already translated, per engine and per
         language pair. An identical sentence is never translated again: the
         translation comes from the cache (faster, and free with paid
         engines). The log says how many sentences came from the cache;
       - the HISTORY: what was translated, when, by which engine, for which
         game, and where the translation comes from (engine, cache, manual
         fix…).
     Safety: the file carries a version number (lossless migrations); a
     damaged file is set aside (never deleted) and a new one is created.
     Several translations may use it at the same time.

     Ce module ne dépend pas de Qt. / This module does not depend on Qt.
"""

import logging
import sqlite3
import threading
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# FR : Nom du fichier de la base. EN : Database file name.
CACHE_FILE_NAME = "translations.sqlite3"

# FR : Version du format de la base. EN : Database format version.
SCHEMA_VERSION = 1

# FR : D'où vient une traduction (colonne « origin » de l'historique).
# EN : Where a translation comes from ("origin" column of the history).
ORIGIN_ENGINE = "engine"  # FR : traduite par un moteur / EN : translated by an engine
ORIGIN_CACHE = "cache"  # FR : reprise du cache / EN : taken from the cache
ORIGIN_MANUAL = "manual"  # FR : écrite ou corrigée à la main / EN : written or fixed by hand

_SCHEMA = """
CREATE TABLE IF NOT EXISTS translations (
    engine TEXT NOT NULL,
    source_lang TEXT NOT NULL,
    target_lang TEXT NOT NULL,
    source TEXT NOT NULL,
    translation TEXT NOT NULL,
    created_at TEXT NOT NULL,
    used_at TEXT NOT NULL,
    use_count INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (engine, source_lang, target_lang, source)
);
CREATE INDEX IF NOT EXISTS translations_by_text
    ON translations (source_lang, target_lang, source);
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    game TEXT NOT NULL DEFAULT '',
    engine TEXT NOT NULL,
    source_lang TEXT NOT NULL,
    target_lang TEXT NOT NULL,
    source TEXT NOT NULL,
    translation TEXT NOT NULL,
    origin TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS history_by_game ON history (game, created_at);
"""

# FR : Conversions d'un ancien format vers le suivant (vide pour l'instant).
# EN : Conversions from an old format to the next one (empty for now).
MIGRATIONS: dict[int, str] = {}


def cache_file(data_dir: Path) -> Path:
    """FR : emplacement de la base. EN : location of the database."""
    return data_dir / CACHE_FILE_NAME


def _now() -> str:
    """FR : date et heure (UTC, format ISO). EN : date and time (UTC, ISO format)."""
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass(frozen=True)
class HistoryEntry:
    """Une ligne de l'historique / One history line."""

    created_at: str
    game: str
    engine: str
    source_lang: str
    target_lang: str
    source: str
    translation: str
    origin: str


@dataclass(frozen=True)
class CacheStats:
    """Chiffres du cache / Cache figures."""

    translations: int  # FR : phrases en cache / EN : sentences in the cache
    history: int  # FR : lignes d'historique / EN : history lines
    size_bytes: int  # FR : taille du fichier / EN : file size


class TranslationCache:
    """Cache et historique / Cache and history.

    FR : S'utilise avec « with » pour être sûr de fermer le fichier :
             with TranslationCache(chemin) as cache: ...
    EN : Use it with "with" to be sure the file is closed (see above).
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._connection = self._open()
        except sqlite3.DatabaseError as error:
            # FR : fichier abîmé : mis de côté, jamais effacé, puis on repart à neuf.
            # EN : damaged file: set aside, never deleted, then start afresh.
            damaged = path.with_name(f"{path.name}.abime-{datetime.now():%Y%m%d-%H%M%S}")
            path.replace(damaged)
            logger.error(
                "Cache illisible, mis de côté / Unreadable cache, set aside: %s (%s)",
                damaged,
                error,
            )
            self._connection = self._open()

    def _open(self) -> sqlite3.Connection:
        """FR : ouvre la base et la met au bon format. EN : open the base and update its format."""
        connection = sqlite3.connect(self.path, check_same_thread=False, timeout=30)
        try:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version > SCHEMA_VERSION:
                # FR : écrit par une version plus récente : on lit sans rien convertir.
                # EN : written by a newer version: read it without converting anything.
                logger.warning(
                    "Cache écrit par une version plus récente / Cache written by a newer "
                    "version (format %s)",
                    version,
                )
            else:
                # FR : tables créées si besoin, puis conversions d'un ancien format.
                # EN : tables created if needed, then conversions from an old format.
                connection.executescript(_SCHEMA)
                while 1 <= version < SCHEMA_VERSION:
                    connection.executescript(MIGRATIONS[version])
                    version += 1
                connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
                connection.commit()
            connection.execute("SELECT count(*) FROM translations").fetchone()
        except sqlite3.DatabaseError:
            connection.close()
            raise
        return connection

    # ------------------------------------------------------------------
    # FR : Ouverture et fermeture / EN : Opening and closing
    # ------------------------------------------------------------------
    def close(self) -> None:
        """FR : ferme le fichier. EN : close the file."""
        with self._lock:
            self._connection.close()

    def __enter__(self) -> "TranslationCache":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        """FR : une écriture à la fois, tout ou rien. EN : one write at a time, all or nothing."""
        with self._lock, self._connection:
            yield self._connection

    # ------------------------------------------------------------------
    # FR : Cache / EN : Cache
    # ------------------------------------------------------------------
    def get(
        self, source: str, source_lang: str, target_lang: str, engine: str | None = None
    ) -> str | None:
        """Cherche une traduction déjà faite / Look up an existing translation.

        FR : Avec « engine » : seulement celle de ce moteur. Sans : la plus
             récente, quel que soit le moteur. Renvoie None si rien n'est trouvé.
        EN : With "engine": only that engine's. Without: the most recent one,
             whatever the engine. Returns None when nothing is found.
        """
        return self.get_many([source], source_lang, target_lang, engine).get(source)

    def get_many(
        self,
        sources: Sequence[str],
        source_lang: str,
        target_lang: str,
        engine: str | None = None,
    ) -> dict[str, str]:
        """FR : comme get(), pour plusieurs phrases d'un coup. EN : like get(), for many."""
        found: dict[str, str] = {}
        unique = list(dict.fromkeys(sources))
        query = (
            "SELECT source, translation FROM translations "
            "WHERE source_lang = ? AND target_lang = ? AND source = ?"
        )
        if engine is not None:
            query += " AND engine = ?"
        query += " ORDER BY used_at DESC LIMIT 1"
        now = _now()
        with self._transaction() as connection:
            for source in unique:
                parameters = [source_lang, target_lang, source]
                if engine is not None:
                    parameters.append(engine)
                row = connection.execute(query, parameters).fetchone()
                if row is None:
                    continue
                found[source] = row[1]
                connection.execute(
                    "UPDATE translations SET used_at = ?, use_count = use_count + 1 "
                    "WHERE source_lang = ? AND target_lang = ? AND source = ?",
                    (now, source_lang, target_lang, source),
                )
        return found

    def put(
        self,
        source: str,
        translation: str,
        source_lang: str,
        target_lang: str,
        engine: str,
    ) -> None:
        """FR : garde une traduction. EN : keep a translation."""
        self.put_many({source: translation}, source_lang, target_lang, engine)

    def put_many(
        self, pairs: dict[str, str], source_lang: str, target_lang: str, engine: str
    ) -> None:
        """FR : garde plusieurs traductions d'un coup. EN : keep many translations at once."""
        now = _now()
        with self._transaction() as connection:
            connection.executemany(
                "INSERT INTO translations "
                "(engine, source_lang, target_lang, source, translation, created_at, used_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT (engine, source_lang, target_lang, source) DO UPDATE SET "
                "translation = excluded.translation, used_at = excluded.used_at",
                [
                    (engine, source_lang, target_lang, source, translation, now, now)
                    for source, translation in pairs.items()
                ],
            )

    def clear_cache(self) -> None:
        """FR : vide le cache (l'historique est gardé). EN : empty the cache (history kept)."""
        with self._transaction() as connection:
            connection.execute("DELETE FROM translations")
        self._vacuum()
        logger.info("Cache des traductions vidé / Translation cache emptied")

    # ------------------------------------------------------------------
    # FR : Historique / EN : History
    # ------------------------------------------------------------------
    def record(
        self,
        source: str,
        translation: str,
        source_lang: str,
        target_lang: str,
        engine: str,
        origin: str,
        game: str = "",
    ) -> None:
        """FR : ajoute une ligne à l'historique. EN : add a line to the history."""
        self.record_many([(source, translation)], source_lang, target_lang, engine, origin, game)

    def record_many(
        self,
        pairs: Sequence[tuple[str, str]],
        source_lang: str,
        target_lang: str,
        engine: str,
        origin: str,
        game: str = "",
    ) -> None:
        """FR : ajoute plusieurs lignes à l'historique. EN : add many history lines."""
        now = _now()
        with self._transaction() as connection:
            connection.executemany(
                "INSERT INTO history (created_at, game, engine, source_lang, target_lang, "
                "source, translation, origin) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (now, game, engine, source_lang, target_lang, source, translation, origin)
                    for source, translation in pairs
                ],
            )

    def history(self, game: str | None = None, limit: int = 1000) -> list[HistoryEntry]:
        """FR : dernières lignes de l'historique (les plus récentes d'abord).

        EN : last history lines (most recent first).
        """
        query = (
            "SELECT created_at, game, engine, source_lang, target_lang, source, translation, "
            "origin FROM history"
        )
        parameters: list[object] = []
        if game is not None:
            query += " WHERE game = ?"
            parameters.append(game)
        query += " ORDER BY id DESC LIMIT ?"
        parameters.append(limit)
        with self._lock:
            rows = self._connection.execute(query, parameters).fetchall()
        return [HistoryEntry(*row) for row in rows]

    def clear_history(self) -> None:
        """FR : vide l'historique (le cache est gardé). EN : empty the history (cache kept)."""
        with self._transaction() as connection:
            connection.execute("DELETE FROM history")
        self._vacuum()
        logger.info("Historique des traductions vidé / Translation history emptied")

    # ------------------------------------------------------------------
    # FR : Chiffres / EN : Figures
    # ------------------------------------------------------------------
    def stats(self) -> CacheStats:
        """FR : nombre de phrases, de lignes d'historique, taille. EN : counts and size."""
        with self._lock:
            translations = self._connection.execute("SELECT count(*) FROM translations").fetchone()
            history = self._connection.execute("SELECT count(*) FROM history").fetchone()
        size = self.path.stat().st_size if self.path.exists() else 0
        return CacheStats(translations[0], history[0], size)

    def _vacuum(self) -> None:
        """FR : rend au disque la place libérée. EN : give freed space back to the disk."""
        with self._lock:
            self._connection.execute("VACUUM")


def translate_with_cache(
    cache: TranslationCache,
    sources: Sequence[str],
    source_lang: str,
    target_lang: str,
    engine: str,
    translate: Callable[[list[str]], list[str]],
    game: str = "",
) -> list[str]:
    """Traduit en réutilisant le cache / Translate reusing the cache.

    FR : Seules les phrases absentes du cache sont envoyées au moteur
         (« translate »), et chacune une seule fois même si elle apparaît
         plusieurs fois. Le journal dit combien viennent du cache. Les
         traductions sont gardées dans le cache et notées dans l'historique.
    EN : Only sentences missing from the cache are sent to the engine
         ("translate"), each only once even if it appears several times. The
         log says how many came from the cache. Translations are kept in the
         cache and written to the history.
    """
    known = cache.get_many(sources, source_lang, target_lang)
    missing = [source for source in dict.fromkeys(sources) if source not in known]
    new: dict[str, str] = {}
    if missing:
        results = translate(missing)
        if len(results) != len(missing):
            raise ValueError(
                "le moteur n'a pas renvoyé autant de traductions que de phrases / "
                "the engine did not return as many translations as sentences"
            )
        new = dict(zip(missing, results, strict=True))
        cache.put_many(new, source_lang, target_lang, engine)
    from_cache = sum(1 for source in sources if source in known)
    logger.info(
        "%s phrase(s) : %s depuis le cache, %s traduite(s) par %s / "
        "%s sentence(s): %s from the cache, %s translated by %s",
        len(sources),
        from_cache,
        len(missing),
        engine,
        len(sources),
        from_cache,
        len(missing),
        engine,
    )
    cache.record_many(
        [(source, known[source]) for source in dict.fromkeys(sources) if source in known],
        source_lang,
        target_lang,
        engine,
        ORIGIN_CACHE,
        game,
    )
    cache.record_many(list(new.items()), source_lang, target_lang, engine, ORIGIN_ENGINE, game)
    translations = {**known, **new}
    return [translations[source] for source in sources]
