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

"""Tests des moteurs en ligne et du rangement des clés (étape 16).

FR : Ici, un faux serveur répond à la place de Yandex, Google, DeepL… : on
     vérifie que chaque moteur envoie la bonne demande, lit bien la réponse,
     et transforme chaque panne en raison claire. Les vrais Yandex et Google
     gratuits sont essayés par GitHub (test « Moteurs en ligne »).
EN : Here, a fake server answers instead of Yandex, Google, DeepL…: each
     engine must send the right request, read the answer correctly, and turn
     every failure into a clear reason. The real free Yandex and Google are
     tried by GitHub ("Online engines" check).
"""

import json
import os
from pathlib import Path

import httpx
import pytest

from runecast.core.protect import STYLE_XML, protect, restore
from runecast.core.secrets import KeyStore
from runecast.engines.online import (
    DEFAULT_ENABLED,
    DEFAULT_ORDER,
    ENGINE_CLASSES,
    REASON_KEY,
    REASON_LIMIT,
    REASON_OFFLINE,
    REASON_SERVICE,
    OnlineError,
    create_engine,
    escape_outside_markers,
    estimate_cost,
)


def fake(handler):
    """FR : client relié à un faux serveur. EN : client connected to a fake server."""
    requests: list[httpx.Request] = []

    def recorder(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    return (lambda: httpx.Client(transport=httpx.MockTransport(recorder))), requests


def test_default_order_and_enabled() -> None:
    """FR : Yandex à clé avant Yandex gratuit ; Yandex et Google gratuits activés.

    EN : Yandex key before Yandex free; free Yandex and Google enabled.
    """
    assert DEFAULT_ORDER[:3] == ("yandex_key", "yandex_free", "google_free")
    assert DEFAULT_ENABLED == ("yandex_free", "google_free")
    assert set(DEFAULT_ORDER) == set(ENGINE_CLASSES) and len(DEFAULT_ORDER) == 7
    assert all(ENGINE_CLASSES[e].info.unofficial for e in DEFAULT_ENABLED)


def test_yandex_free() -> None:
    """FR : Yandex gratuit : identifiant lu dans le widget, textes échappés en HTML.

    EN : Yandex free: id read from the widget, texts HTML-escaped.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        if "widget.js" in str(request.url):
            return httpx.Response(200, text="var x={sid: 'abc123.def456', other: 1}")
        body = request.content.decode()
        assert request.url.params["id"] == "abc123.def456-0-0"
        assert request.url.params["lang"] == "en-fr"
        if "Tom" not in body:
            return httpx.Response(200, json={"code": 200, "text": ["Salut"]})
        assert "text=Tom+%26amp%3B+Jerry" in body and "text=Hi" in body
        return httpx.Response(200, json={"code": 200, "text": ["Tom &amp; Jerry FR", "Salut"]})

    factory, requests = fake(handler)
    engine = create_engine("yandex_free", client_factory=factory)
    assert engine.translate(["Tom & Jerry", "Hi", ""], "en", "fr") == [
        "Tom & Jerry FR",
        "Salut",
        "",
    ]
    engine.translate(["Hi"], "en", "fr")
    assert sum("widget.js" in str(r.url) for r in requests) == 1  # FR : identifiant gardé


def test_yandex_free_refreshes_expired_id() -> None:
    """FR : identifiant périmé (403) : on en redemande un, une seule fois.

    EN : expired id (403): a new one is asked for, only once.
    """
    calls = {"translate": 0, "widget": 0}

    def handler(request):
        if "widget.js" in str(request.url):
            calls["widget"] += 1
            return httpx.Response(200, text=f"sid: '{calls['widget']}aa'")
        calls["translate"] += 1
        if request.url.params["id"].startswith("1aa"):
            return httpx.Response(403)
        return httpx.Response(200, json={"code": 200, "text": ["Salut"]})

    factory, _requests = fake(handler)
    engine = create_engine("yandex_free", client_factory=factory)
    assert engine.translate(["Hi"], "en", "fr") == ["Salut"]
    assert calls == {"translate": 2, "widget": 2}


def test_yandex_widget_changed() -> None:
    """FR : widget modifié par Yandex : raison claire. EN : widget changed: clear reason."""
    factory, _r = fake(lambda request: httpx.Response(200, text="nothing here"))
    with pytest.raises(OnlineError) as caught:
        create_engine("yandex_free", client_factory=factory).translate(["Hi"], "en", "fr")
    assert caught.value.reason == REASON_SERVICE


def test_yandex_cloud() -> None:
    """FR : Yandex Cloud : clé API et dossier. EN : Yandex Cloud: API key and folder."""

    def handler(request):
        assert request.headers["Authorization"] == "Api-Key secret"
        body = json.loads(request.content)
        assert body["folderId"] == "b1g" and body["targetLanguageCode"] == "kk"
        return httpx.Response(200, json={"translations": [{"text": "Сәлем"}]})

    factory, _r = fake(handler)
    engine = create_engine("yandex_key", "secret", {"folder_id": "b1g"}, factory)
    assert engine.translate(["Hello"], "en", "kk") == ["Сәлем"]


def test_google_free() -> None:
    """FR : Google gratuit : morceaux recollés ; portugais du Portugal = « pt-PT ».

    EN : Google free: pieces joined; Portugal Portuguese = "pt-PT".
    """

    def handler(request):
        assert request.url.params["client"] == "gtx"
        assert request.url.params["tl"] == "pt-PT"
        return httpx.Response(
            200, json=[[["Olá. ", "Hello. "], ["Tudo bem?", "All good?"]], None, "en"]
        )

    factory, requests = fake(handler)
    engine = create_engine("google_free", client_factory=factory)
    assert engine.translate(["Hello. All good?", "Second"], "en", "pt") == [
        "Olá. Tudo bem?",
        "Olá. Tudo bem?",
    ]
    assert len(requests) == 2  # FR : un texte par requête / EN : one text per request


def test_deepl_free_key_and_xml_markers() -> None:
    """FR : DeepL : clé « :fx » = API gratuite ; repères XML gardés tels quels.

    EN : DeepL: ":fx" key = free API; XML markers kept as they are.
    """
    protected = protect("{b}Tom & Jerry{/b} [player]", style=STYLE_XML)

    def handler(request):
        assert request.url.host == "api-free.deepl.com"
        assert request.headers["Authorization"] == "DeepL-Auth-Key k:fx"
        body = json.loads(request.content)
        assert body["text"] == ['<x id="0"/>Tom &amp; Jerry<x id="1"/> <x id="2"/>']
        assert body["target_lang"] == "PT-PT" and body["tag_handling"] == "xml"
        return httpx.Response(
            200,
            json={
                "translations": [{"text": '<x id="0"/>Tom &amp; Jerry PT<x id="1"/> <x id="2"/>'}]
            },
        )

    factory, _r = fake(handler)
    engine = create_engine("deepl", "k:fx", client_factory=factory)
    result = restore(engine.translate([protected.masked], "en", "pt")[0], protected)
    assert result.ok and result.text == "{b}Tom & Jerry PT{/b} [player]"
    assert create_engine("deepl", "pro-key").url == "https://api.deepl.com/v2"


def test_google_cloud_microsoft_libretranslate() -> None:
    """FR : les trois autres moteurs à clé. EN : the three other key engines."""

    def handler(request):
        host = request.url.host
        if host == "translation.googleapis.com":
            assert request.url.params["key"] == "g"
            return httpx.Response(200, json={"data": {"translations": [{"translatedText": "G"}]}})
        if host == "api.cognitive.microsofttranslator.com":
            assert request.headers["Ocp-Apim-Subscription-Region"] == "westeurope"
            assert request.url.params["to"] == "zh-Hans"
            return httpx.Response(200, json=[{"translations": [{"text": "M"}]}])
        body = json.loads(request.content)
        assert str(request.url).startswith("https://lt.exemple.org/translate")
        assert body["api_key"] == "l" and body["target"] == "pb"
        return httpx.Response(200, json={"translatedText": ["L"]})

    factory, _r = fake(handler)
    assert create_engine("google_cloud", "g", client_factory=factory).translate(
        ["x"], "en", "fr"
    ) == ["G"]
    microsoft = create_engine("microsoft", "m", {"region": "westeurope"}, factory)
    assert microsoft.translate(["x"], "en", "zh") == ["M"]
    libre = create_engine("libretranslate", "l", {"url": "https://lt.exemple.org/"}, factory)
    assert libre.translate(["x"], "en", "pt-BR") == ["L"]


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        (401, REASON_KEY),
        (403, REASON_KEY),
        (429, REASON_LIMIT),
        (456, REASON_LIMIT),
        (503, REASON_SERVICE),
        (400, REASON_SERVICE),
    ],
)
def test_errors_become_clear_reasons(status: int, reason: str) -> None:
    """FR : chaque panne devient une raison claire. EN : every failure becomes a clear reason."""
    factory, _r = fake(lambda request: httpx.Response(status))
    with pytest.raises(OnlineError) as caught:
        create_engine("google_cloud", "k", client_factory=factory).translate(["x"], "en", "fr")
    assert caught.value.reason == reason


def test_no_internet() -> None:
    """FR : pas d'internet : raison « offline ». EN : no internet: "offline" reason."""

    def handler(request):
        raise httpx.ConnectError("réseau coupé", request=request)

    factory, _r = fake(handler)
    with pytest.raises(OnlineError) as caught:
        create_engine("google_free", client_factory=factory).translate(["x"], "en", "fr")
    assert caught.value.reason == REASON_OFFLINE


def test_missing_key() -> None:
    """FR : moteur payant sans clé : rien envoyé. EN : paid engine without key: nothing sent."""
    factory, requests = fake(lambda request: httpx.Response(200))
    with pytest.raises(OnlineError) as caught:
        create_engine("deepl", client_factory=factory).translate(["x"], "en", "fr")
    assert caught.value.reason == REASON_KEY and requests == []


def test_batches_respect_limits() -> None:
    """FR : les lots respectent le nombre de textes et de caractères. EN : batch limits."""
    sizes: list[int] = []

    def handler(request):
        texts = json.loads(request.content)["q"]
        sizes.append(len(texts))
        return httpx.Response(
            200, json={"data": {"translations": [{"translatedText": t} for t in texts]}}
        )

    factory, _r = fake(handler)
    engine = create_engine("google_cloud", "k", client_factory=factory)
    engine.max_texts, engine.max_chars = 3, 20
    texts = [f"phrase {n}" for n in range(8)]
    assert engine.translate(texts, "en", "fr") == texts
    assert sizes == [2, 2, 2, 2]  # FR : 20 caractères au plus / EN : at most 20 characters
    engine.max_chars = 1000
    sizes.clear()
    engine.translate(texts, "en", "fr")
    assert sizes == [3, 3, 2]  # FR : 3 textes au plus / EN : at most 3 texts


def test_escape_and_cost() -> None:
    """FR : échappement hors repères ; coût estimé. EN : escaping outside markers; cost."""
    assert escape_outside_markers('a < b <x id="0"/> & c') == 'a &lt; b <x id="0"/> &amp; c'
    deepl = ENGINE_CLASSES["deepl"].info
    assert estimate_cost(deepl, 1_000_000) == 25.0
    assert estimate_cost(ENGINE_CLASSES["google_free"].info, 1_000_000) == 0.0


# ----------------------------------------------------------------------
# FR : Rangement des clés / EN : Key storage
# ----------------------------------------------------------------------
def test_keys_in_system_keyring(tmp_path: Path, memory_keyring) -> None:
    """FR : les clés vont dans le trousseau, jamais dans un fichier. EN : keys go to the keyring."""
    store = KeyStore(tmp_path)
    assert store.secure
    store.set("deepl", " ma-cle ")
    assert store.get("deepl") == "ma-cle"
    assert memory_keyring.passwords == {("RuneCast", "deepl"): "ma-cle"}
    assert not list(tmp_path.iterdir())
    store.set("deepl", "")
    assert store.get("deepl") == "" and memory_keyring.passwords == {}


def test_keys_in_portable_mode(tmp_path: Path, memory_keyring) -> None:
    """FR : mode portable : clés dans le dossier portable, lisibles par toi seul.

    EN : portable mode: keys in the portable folder, readable by you only.
    """
    store = KeyStore(tmp_path, portable=True)
    assert not store.secure
    store.set("google_cloud", "g")
    assert KeyStore(tmp_path, portable=True).get("google_cloud") == "g"
    assert memory_keyring.passwords == {}
    if os.name != "nt":
        assert (tmp_path / "cles.json").stat().st_mode & 0o777 == 0o600


def test_keys_without_system_keyring(tmp_path: Path, monkeypatch) -> None:
    """FR : pas de trousseau sur ce système : fichier de repli. EN : no keyring: fallback file."""
    from runecast.core import secrets

    monkeypatch.setattr(secrets, "_system_keyring", lambda: None)
    store = KeyStore(tmp_path)
    assert not store.secure
    store.set("microsoft", "m")
    assert store.get("microsoft") == "m"
    store.set("microsoft", "")
    assert json.loads((tmp_path / "cles.json").read_text(encoding="utf-8")) == {}
