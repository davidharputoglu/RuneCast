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

"""Tests du repli automatique et du mode local (étape 17).

FR : Avec de faux moteurs dont on contrôle les pannes : un moteur qui tombe
     en plein travail (comme un Wi-Fi coupé) passe la main au suivant, puis
     au local, sans perdre de ligne ; en mode local, AUCUNE connexion n'est
     tentée vers un service de traduction, même si un moteur en ligne est
     fourni par erreur.
EN : With fake engines whose failures are controlled: an engine failing mid-
     job (like a Wi-Fi cut) hands over to the next one, then to local,
     without losing a line; in local mode, NO connection to a translation
     service is attempted, even if an online engine is given by mistake.
"""

import httpx
import pytest

from runecast.core.cache import TranslationCache
from runecast.core.protect import STYLE_XML
from runecast.core.secrets import KeyStore
from runecast.core.settings import Settings
from runecast.engines import chain as chain_module
from runecast.engines.base import Engine, EngineUnavailable
from runecast.engines.chain import (
    FROM_CACHE,
    MODE_LOCAL,
    MODE_ONLINE,
    EngineChain,
    build_chain,
    translate_texts,
)
from runecast.engines.online import (
    NETWORK,
    REASON_KEY,
    REASON_LIMIT,
    REASON_OFFLINE,
    OnlineError,
    allow_online_translation,
    create_engine,
)
from runecast.ui.translation_page import TranslationPage


class FakeEngine(Engine):
    """FR : faux moteur : préfixe ses traductions, tombe en panne quand on veut.

    EN : fake engine: prefixes its translations, fails when told to.
    """

    def __init__(self, engine_id, online=True, fail_after=None, reason=REASON_OFFLINE, style=None):
        self.engine_id = engine_id
        self.online = online
        self.fail_after = fail_after
        self.reason = reason
        self.calls = 0
        if style:
            self.marker_style = style

    def supports(self, source_lang, target_lang):
        return True

    def translate(self, texts, source_lang, target_lang):
        self.calls += 1
        if self.fail_after is not None and self.calls > self.fail_after:
            raise OnlineError(self.reason, f"{self.engine_id} en panne")
        return [f"{self.engine_id.upper()}:{text}" for text in texts]


LINES = [f"Line {n}." for n in range(50)]


def test_first_engine_does_everything() -> None:
    """FR : tant que le premier moteur répond, il fait tout. EN : the first engine does it all."""
    google = FakeEngine("google_free")
    chain = EngineChain([google, FakeEngine("deepl")], [FakeEngine("local", online=False)])
    results = translate_texts(LINES, "en", "fr", chain, chunk_size=10)
    assert {r.engine for r in results} == {"google_free"}
    assert results[0].text == "GOOGLE_FREE:Line 0." and all(r.ok for r in results)
    assert chain.events == []


def test_wifi_cut_mid_translation_continues_locally() -> None:
    """FR : Wi-Fi coupé au 3e paquet : la suite est traduite en local, sans perte.

    EN : Wi-Fi cut at the 3rd chunk: the rest is translated locally, nothing lost.
    """
    google = FakeEngine("google_free", fail_after=2)
    yandex = FakeEngine("yandex_free", fail_after=0)  # FR : déjà coupé aussi / EN : also cut
    local = FakeEngine("local", online=False)
    chain = EngineChain([google, yandex], [local])
    results = translate_texts(LINES, "en", "fr", chain, chunk_size=10)
    engines = [r.engine for r in results]
    assert engines[:20] == ["google_free"] * 20
    assert engines[20:] == ["local"] * 30
    assert [e.engine for e in chain.events] == ["google_free", "yandex_free"]
    assert all(e.reason == REASON_OFFLINE for e in chain.events)
    assert google.calls == 3  # FR : plus réessayé ensuite / EN : not retried afterwards


def test_each_failure_moves_to_the_next() -> None:
    """FR : limite atteinte, puis clé refusée : le 3e moteur prend le relais.

    EN : limit reached, then key refused: the 3rd engine takes over.
    """
    chain = EngineChain(
        [
            FakeEngine("yandex_free", fail_after=0, reason=REASON_LIMIT),
            FakeEngine("deepl", fail_after=0, reason=REASON_KEY),
            FakeEngine("google_free"),
        ],
        [FakeEngine("local", online=False)],
    )
    results = translate_texts(["Hi"], "en", "fr", chain)
    assert results[0].engine == "google_free"
    assert [(e.engine, e.reason) for e in chain.events] == [
        ("yandex_free", REASON_LIMIT),
        ("deepl", REASON_KEY),
    ]


def test_no_engine_left() -> None:
    """FR : plus aucun moteur : erreur claire. EN : no engine left: clear error."""
    chain = EngineChain([FakeEngine("google_free", fail_after=0)], [])
    with pytest.raises(EngineUnavailable):
        translate_texts(["Hi"], "en", "fr", chain)


def test_incomplete_answer_moves_on() -> None:
    """FR : un moteur qui « perd » des lignes est mis de côté. EN : line-losing engine set aside."""

    class Lossy(FakeEngine):
        def translate(self, texts, source_lang, target_lang):
            return ["seulement une"]

    chain = EngineChain([Lossy("google_free")], [FakeEngine("local", online=False)])
    results = translate_texts(["A", "B"], "en", "fr", chain)
    assert [r.engine for r in results] == ["local", "local"]


def test_tags_survive_the_chain() -> None:
    """FR : balises et variables protégées, quel que soit le style de repères du moteur.

    EN : tags and variables protected, whatever the engine's marker style.
    """
    line = "{b}Hello{/b}, [player]! {w}"
    for engine in (FakeEngine("google_free"), FakeEngine("deepl", style=STYLE_XML)):
        chain = EngineChain([engine], [])
        result = translate_texts([line, "{w}"], "en", "fr", chain)
        # FR : le faux moteur ajoute « NOM: » devant ; tout le reste revient intact.
        # EN : the fake engine adds "NAME:" in front; everything else comes back intact.
        assert result[0].ok and result[0].text == f"{engine.engine_id.upper()}:{line}"
        assert result[1].text == "{w}"  # FR : rien à traduire / EN : nothing to translate


def test_lost_markers_are_marked_to_check() -> None:
    """FR : un moteur qui perd une balise : ligne « à vérifier », pas mise en cache.

    EN : an engine losing a tag: line "to check", not cached.
    """

    class Careless(FakeEngine):
        def translate(self, texts, source_lang, target_lang):
            return ["Bonjour" for _text in texts]

    chain = EngineChain([Careless("google_free")], [])
    with TranslationCache(_cache_path()) as cache:
        result = translate_texts(["Hello [player]"], "en", "fr", chain, cache)
        assert not result[0].ok and "missing" in result[0].problems
        assert cache.get("Hello [player]", "en", "fr") is None


def _cache_path():
    import tempfile
    from pathlib import Path

    return Path(tempfile.mkdtemp()) / "cache.sqlite3"


def test_cache_and_duplicates(tmp_path) -> None:
    """FR : lignes en double traduites une fois ; la 2e fois, tout vient du cache.

    EN : duplicate lines translated once; the 2nd time, everything comes from the cache.
    """
    google = FakeEngine("google_free")
    with TranslationCache(tmp_path / "c.sqlite3") as cache:
        first = translate_texts(["A", "B", "A"], "en", "fr", EngineChain([google], []), cache)
        assert google.calls == 1 and [r.text for r in first] == [
            "GOOGLE_FREE:A",
            "GOOGLE_FREE:B",
            "GOOGLE_FREE:A",
        ]
        second = translate_texts(["B", "A"], "en", "fr", EngineChain([google], []), cache)
        assert google.calls == 1
        assert {r.engine for r in second} == {FROM_CACHE}


def test_cancel_keeps_what_is_done() -> None:
    """FR : arrêt en cours : les lignes faites sont gardées, les autres valent None.

    EN : stopped mid-way: done lines are kept, the others are None.
    """
    calls = []
    chain = EngineChain([FakeEngine("google_free")], [])
    results = translate_texts(
        LINES,
        "en",
        "fr",
        chain,
        chunk_size=10,
        should_cancel=lambda: calls.append(1) or len(calls) > 2,
    )
    assert sum(r is not None for r in results) == 20
    assert results[-1] is None


# ----------------------------------------------------------------------
# FR : Mode local : aucune connexion / EN : Local mode: no connection
# ----------------------------------------------------------------------
def _recording_client():
    requests: list[httpx.Request] = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=[[["X", "Y"]]])

    return (lambda: httpx.Client(transport=httpx.MockTransport(handler))), requests


def test_local_mode_never_connects() -> None:
    """FR : mode local : même un moteur en ligne fourni par erreur n'est jamais appelé.

    EN : local mode: even an online engine given by mistake is never called.
    """
    factory, requests = _recording_client()
    google = create_engine("google_free", client_factory=factory)
    local = FakeEngine("local", online=False)
    chain = EngineChain([google], [local], MODE_LOCAL)
    results = translate_texts(LINES, "en", "fr", chain)
    assert {r.engine for r in results} == {"local"}
    assert requests == []


def test_network_lock_blocks_online_engines() -> None:
    """FR : verrou fermé : un moteur en ligne refuse de se connecter.

    EN : lock closed: an online engine refuses to connect.
    """
    factory, requests = _recording_client()
    google = create_engine("google_free", client_factory=factory)
    allow_online_translation(False)
    with pytest.raises(OnlineError) as caught:
        google.translate(["Hi"], "en", "fr")
    assert caught.value.reason == REASON_OFFLINE and requests == []
    allow_online_translation(True)
    assert google.translate(["Hi"], "en", "fr") == ["X"]
    assert len(requests) == 1


def test_build_chain_from_settings(custom_paths) -> None:
    """FR : la chaîne suit les réglages : moteurs cochés dans l'ordre, puis le local.

    EN : the chain follows the settings: checked engines in order, then local.
    """
    KeyStore(custom_paths.config_dir).set("deepl", "cle:fx")
    settings = Settings(engines_enabled=["deepl", "google_free"])
    chain = build_chain(settings, custom_paths)
    assert [e.engine_id for e in chain.engines] == ["google_free", "deepl", "local", "nllb"]
    assert chain.engines[1].key == "cle:fx"
    assert NETWORK.allowed

    local_chain = build_chain(Settings(translation_mode=MODE_LOCAL), custom_paths)
    assert [e.engine_id for e in local_chain.engines] == ["local", "nllb"]
    assert not NETWORK.allowed


# ----------------------------------------------------------------------
# FR : Page « Traduction » / EN : "Translation" page
# ----------------------------------------------------------------------
@pytest.fixture
def page(qtbot, custom_paths) -> TranslationPage:
    widget = TranslationPage(custom_paths)
    qtbot.addWidget(widget)
    widget.load(Settings())
    yield widget
    widget.shutdown()


def test_page_mode_and_order(page: TranslationPage) -> None:
    """FR : mode affiché et ordre réellement utilisé. EN : mode shown and order really used."""
    assert page.online_radio.isChecked()
    assert (
        page.order_label.text()
        == "Ordre utilisé : Yandex → Google → Local (Argos) → Local (NLLB-200)"
    )
    page.local_radio.setChecked(True)
    assert page.order_label.text() == "Ordre utilisé : Local (Argos) → Local (NLLB-200)"
    settings = Settings()
    page.store(settings)
    assert settings.translation_mode == MODE_LOCAL


def test_page_test_shows_engines_and_fallback(page, qtbot, monkeypatch) -> None:
    """FR : l'essai montre le moteur de chaque ligne et les relais.

    EN : the test shows each line's engine and the hand-overs.
    """
    chain = EngineChain(
        [FakeEngine("google_free", fail_after=1)], [FakeEngine("local", online=False)]
    )
    monkeypatch.setattr(chain_module, "build_chain", lambda *a: chain)
    monkeypatch.setattr("runecast.ui.translation_page.build_chain", lambda *a: chain)
    page.lines_edit.setPlainText("\n".join(f"Line {n}" for n in range(30)))
    page.translate_button.click()
    qtbot.waitUntil(lambda: page.task is None, timeout=10_000)
    assert page.results.rowCount() == 30
    assert page.results.item(0, 2).text() == "Google"
    assert page.results.item(29, 2).text() == "Local (Argos)"
    assert "Google mis de côté (pas de connexion à internet)" in page.summary.text()
    assert MODE_ONLINE == "online"
