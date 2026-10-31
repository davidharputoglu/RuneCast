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

"""Tests du cache et de l'historique des traductions (étape 12).

FR : Vérifie qu'une phrase identique n'est jamais retraduite (et que le
     journal le dit), que l'historique note l'origine de chaque traduction,
     que la base résiste aux fichiers abîmés et aux accès simultanés, et que
     la page « Cache des traductions » des Paramètres affiche les bons
     chiffres et ne vide rien sans confirmation.
EN : Checks that an identical sentence is never translated again (and that
     the log says so), that the history records where each translation
     comes from, that the base survives damaged files and simultaneous
     access, and that the "Translation cache" Settings page shows the right
     figures and empties nothing without confirmation.
"""

import logging
import sqlite3
import threading
from pathlib import Path

import pytest
from PySide6.QtWidgets import QMessageBox

from runecast.core import cache as cache_module
from runecast.core.cache import (
    ORIGIN_CACHE,
    ORIGIN_ENGINE,
    TranslationCache,
    cache_file,
    translate_with_cache,
)
from runecast.ui.i18n import LanguageManager, format_size
from runecast.ui.settings_dialog import CachePage


@pytest.fixture
def cache(tmp_path: Path):
    """FR : une base vide, fermée après le test. EN : an empty base, closed after the test."""
    with TranslationCache(tmp_path / "translations.sqlite3") as opened:
        yield opened


class FakeEngine:
    """FR : faux moteur qui note ce qu'on lui demande. EN : fake engine recording requests."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, sentences: list[str]) -> list[str]:
        self.calls.append(list(sentences))
        return [f"FR:{sentence}" for sentence in sentences]


def test_put_and_get(cache: TranslationCache) -> None:
    """FR : une traduction gardée est retrouvée. EN : a kept translation is found again."""
    assert cache.get("Hello", "en", "fr") is None
    cache.put("Hello", "Bonjour", "en", "fr", "yandex")
    assert cache.get("Hello", "en", "fr") == "Bonjour"
    assert cache.get("Hello", "en", "fr", engine="yandex") == "Bonjour"
    assert cache.get("Hello", "en", "fr", engine="google") is None
    assert cache.get("Hello", "en", "tr") is None  # FR : autre langue / EN : other language
    assert cache.get("hello", "en", "fr") is None  # FR : majuscules comptent / EN : case matters


def test_most_recent_engine_wins(cache: TranslationCache) -> None:
    """FR : sans moteur précis, la traduction la plus récente est prise.

    EN : without a specific engine, the most recent translation is taken.
    """
    cache.put("Hello", "Salut", "en", "fr", "local")
    cache.get("Hello", "en", "fr", engine="local")
    cache.put("Hello", "Bonjour", "en", "fr", "yandex")
    assert cache.get("Hello", "en", "fr") in {"Bonjour", "Salut"}
    assert cache.get("Hello", "en", "fr", engine="yandex") == "Bonjour"


def test_unicode_texts(cache: TranslationCache) -> None:
    """FR : toutes les écritures sont gardées telles quelles. EN : every script is kept as is."""
    pairs = {"Hello": "مرحبا", "Friend": "Дос", "Tree": "Ağaç", "Heart": "♥ {b}❤{/b}"}
    cache.put_many(pairs, "en", "xx", "test")
    assert cache.get_many(list(pairs), "en", "xx") == pairs


def test_identical_sentence_is_not_translated_again(
    cache: TranslationCache, caplog: pytest.LogCaptureFixture
) -> None:
    """FR : la 2e fois, rien n'est envoyé au moteur, et le journal le dit.

    EN : the 2nd time, nothing is sent to the engine, and the log says so.
    """
    engine = FakeEngine()
    caplog.set_level(logging.INFO, logger="runecast")
    first = translate_with_cache(cache, ["Hi", "Bye", "Hi"], "en", "fr", "fake", engine)
    assert first == ["FR:Hi", "FR:Bye", "FR:Hi"]
    assert engine.calls == [["Hi", "Bye"]]  # FR : « Hi » une seule fois / EN : "Hi" only once
    assert "0 depuis le cache, 2 traduite(s) par fake" in caplog.text

    caplog.clear()
    second = translate_with_cache(cache, ["Bye", "Hi", "New"], "en", "fr", "fake", engine)
    assert second == ["FR:Bye", "FR:Hi", "FR:New"]
    assert engine.calls[-1] == ["New"]
    assert "2 depuis le cache, 1 traduite(s) par fake" in caplog.text

    engine.calls.clear()
    translate_with_cache(cache, ["Hi", "Bye"], "en", "fr", "fake", engine)
    assert engine.calls == []


def test_history_records_origin(cache: TranslationCache) -> None:
    """FR : l'historique dit si la traduction vient du moteur ou du cache.

    EN : the history says whether the translation came from the engine or the cache.
    """
    engine = FakeEngine()
    translate_with_cache(cache, ["Hi"], "en", "fr", "fake", engine, game="Jeu A")
    translate_with_cache(cache, ["Hi"], "en", "fr", "fake", engine, game="Jeu B")
    entries = cache.history()
    assert [(e.game, e.origin) for e in entries] == [
        ("Jeu B", ORIGIN_CACHE),
        ("Jeu A", ORIGIN_ENGINE),
    ]
    assert entries[0].translation == "FR:Hi" and entries[0].engine == "fake"
    assert [e.game for e in cache.history(game="Jeu A")] == ["Jeu A"]
    assert len(cache.history(limit=1)) == 1


def test_wrong_engine_answer_is_refused(cache: TranslationCache) -> None:
    """FR : un moteur qui renvoie trop peu de traductions : rien n'est gardé.

    EN : an engine returning too few translations: nothing is kept.
    """
    with pytest.raises(ValueError):
        translate_with_cache(cache, ["A", "B"], "en", "fr", "bad", lambda s: ["only one"])
    assert cache.stats().translations == 0


def test_cache_survives_restart(tmp_path: Path) -> None:
    """FR : le cache est toujours là après redémarrage. EN : the cache survives a restart."""
    path = tmp_path / "translations.sqlite3"
    with TranslationCache(path) as first:
        first.put("Hello", "Bonjour", "en", "fr", "yandex")
    with TranslationCache(path) as second:
        assert second.get("Hello", "en", "fr") == "Bonjour"
    connection = sqlite3.connect(path)
    assert connection.execute("PRAGMA user_version").fetchone()[0] == cache_module.SCHEMA_VERSION
    connection.close()


def test_damaged_file_is_set_aside(tmp_path: Path) -> None:
    """FR : un fichier abîmé est mis de côté (jamais effacé) et un nouveau est créé.

    EN : a damaged file is set aside (never deleted) and a new one is created.
    """
    path = tmp_path / "translations.sqlite3"
    path.write_bytes(b"ceci n'est pas une base SQLite" * 100)
    with TranslationCache(path) as fresh:
        assert fresh.stats().translations == 0
        fresh.put("A", "B", "en", "fr", "x")
    kept = list(tmp_path.glob("translations.sqlite3.abime-*"))
    assert len(kept) == 1
    assert kept[0].read_bytes().startswith(b"ceci n'est pas")


def test_newer_format_is_read_without_change(tmp_path: Path, caplog) -> None:
    """FR : une base d'une version plus récente est lue, sans être convertie.

    EN : a base from a newer version is read, without being converted.
    """
    path = tmp_path / "translations.sqlite3"
    with TranslationCache(path) as first:
        first.put("Hello", "Bonjour", "en", "fr", "yandex")
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA user_version = 99")
    connection.commit()
    connection.close()
    with TranslationCache(path) as newer:
        assert newer.get("Hello", "en", "fr") == "Bonjour"
    assert "plus récente" in caplog.text


def test_simultaneous_translations(cache: TranslationCache) -> None:
    """FR : plusieurs traductions en même temps ne s'abîment pas.

    EN : several translations at the same time do not damage each other.
    """

    def work(worker: int) -> None:
        for number in range(50):
            cache.put(f"s{worker}-{number}", f"t{worker}-{number}", "en", "fr", "x")
            cache.get(f"s{worker}-{number}", "en", "fr")

    threads = [threading.Thread(target=work, args=(worker,)) for worker in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert cache.stats().translations == 200


def test_clear_cache_and_history_separately(cache: TranslationCache) -> None:
    """FR : vider le cache garde l'historique, et inversement.

    EN : emptying the cache keeps the history, and vice versa.
    """
    translate_with_cache(cache, ["A", "B"], "en", "fr", "fake", FakeEngine())
    assert cache.stats().translations == 2 and cache.stats().history == 2
    cache.clear_cache()
    assert cache.stats().translations == 0 and cache.stats().history == 2
    translate_with_cache(cache, ["A"], "en", "fr", "fake", FakeEngine())
    cache.clear_history()
    assert cache.stats().translations == 1 and cache.stats().history == 0


# ----------------------------------------------------------------------
# FR : Page « Cache des traductions » / EN : "Translation cache" page
# ----------------------------------------------------------------------
@pytest.fixture
def page(qtbot, custom_paths) -> CachePage:
    """FR : la page des Paramètres. EN : the Settings page."""
    widget = CachePage(custom_paths)
    qtbot.addWidget(widget)
    return widget


def test_page_with_no_cache_yet(page: CachePage, custom_paths) -> None:
    """FR : sans cache, la page affiche zéro et ne crée pas de fichier.

    EN : with no cache, the page shows zero and creates no file.
    """
    assert page.translations_label.text() == "Phrases en mémoire : 0"
    assert not page.clear_cache_button.isEnabled()
    assert not cache_file(custom_paths.data_dir).exists()


def _fill(custom_paths) -> None:
    with TranslationCache(cache_file(custom_paths.data_dir)) as filled:
        translate_with_cache(filled, ["A", "B", "C"], "en", "fr", "fake", FakeEngine())


def test_page_shows_figures(page: CachePage, custom_paths) -> None:
    """FR : la page affiche les vrais chiffres. EN : the page shows the real figures."""
    _fill(custom_paths)
    page.refresh()
    assert page.translations_label.text() == "Phrases en mémoire : 3"
    assert page.history_label.text() == "Lignes d'historique : 3"
    assert page.clear_cache_button.isEnabled() and page.clear_history_button.isEnabled()


@pytest.mark.parametrize(
    ("answer", "emptied"),
    [(QMessageBox.StandardButton.No, False), (QMessageBox.StandardButton.Yes, True)],
)
def test_page_empties_only_after_confirmation(
    page: CachePage, custom_paths, monkeypatch, answer, emptied: bool
) -> None:
    """FR : « Vider le cache… » demande d'abord confirmation. EN : asks for confirmation first."""
    _fill(custom_paths)
    page.refresh()
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: answer)
    page.clear_cache_button.click()
    with TranslationCache(cache_file(custom_paths.data_dir)) as check:
        assert (check.stats().translations == 0) is emptied
        assert check.stats().history == 3  # FR : l'historique est gardé / EN : history kept
    page.clear_history_button.click()
    with TranslationCache(cache_file(custom_paths.data_dir)) as check:
        assert (check.stats().history == 0) is emptied


def test_sizes_follow_the_language(qapp) -> None:
    """FR : les tailles s'écrivent dans la langue choisie. EN : sizes follow the language."""
    languages = LanguageManager(qapp)
    try:
        languages.apply("en")
        assert format_size(12_345_678) == "11.8 MB"
        languages.apply("fr")
        assert format_size(12_345_678) == "11,8 Mo"
    finally:
        languages.apply("fr")
