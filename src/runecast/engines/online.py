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

"""Moteurs de traduction en ligne / Online translation engines.

FR : Sept moteurs, tous avec le même contrat (engines/base.py) :
       - Yandex gratuit : la méthode du « widget de traduction de page »
         utilisée par l'extension WordPress LocoAI. NON OFFICIELLE : Yandex
         peut la limiter ou l'arrêter à tout moment ;
       - Yandex Cloud (clé officielle, payant) : passe AVANT la méthode
         gratuite quand une clé est enregistrée ;
       - Google gratuit : comme le site Google Traduction, sans compte. NON
         OFFICIELLE également ;
       - DeepL, Google Cloud, Microsoft Translator (clé) et LibreTranslate
         (serveur au choix, clé facultative).
     Chaque erreur est traduite en une raison claire (pas d'internet, clé
     refusée, limite atteinte, service en panne) : le repli automatique de
     l'étape 17 passera alors au moteur suivant, puis au local.
     Les prix indiqués sont des ordres de grandeur relevés en octobre 2026,
     à vérifier sur le site de chaque service.

EN : Seven engines, all with the same contract: Yandex free (the "page
     translation widget" method used by the LocoAI WordPress plugin;
     UNOFFICIAL: Yandex may limit or stop it at any time); Yandex Cloud
     (official key, paid; goes BEFORE the free method when a key is stored);
     Google free (like the Google Translate website, without an account;
     UNOFFICIAL too); DeepL, Google Cloud, Microsoft Translator (key) and
     LibreTranslate (server of your choice, optional key). Every error is
     turned into a clear reason (no internet, key refused, limit reached,
     service down): step 17's automatic fallback will then move to the next
     engine, then to local. Prices shown are orders of magnitude noted in
     October 2026, to be checked on each service's website.

     Ce module ne dépend pas de Qt. / This module does not depend on Qt.
"""

import html
import logging
import re
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from runecast import about
from runecast.core.protect import STYLE_XML
from runecast.engines.base import Engine, EngineUnavailable, TranslationError

logger = logging.getLogger(__name__)

# FR : Raisons d'indisponibilité (affichées à l'utilisateur, et utiles au repli).
# EN : Unavailability reasons (shown to the user, and used by the fallback).
REASON_OFFLINE = "offline"  # FR : pas d'internet / EN : no internet
REASON_KEY = "key"  # FR : clé absente ou refusée / EN : key missing or refused
REASON_LIMIT = "limit"  # FR : quota ou limite atteinte / EN : quota or limit reached
REASON_SERVICE = "service"  # FR : service en panne / EN : service down
REASON_LANGUAGE = "language"  # FR : langue non prise en charge / EN : unsupported language

USER_AGENT = f"RuneCast/{about.APP_VERSION} (+{about.REPOSITORY_URL})"

# FR : Repères XML (moteurs qui comprennent le HTML/XML). EN : XML markers.
_XML_MARKER = re.compile(r'<x id="\d+"/>')


class OnlineError(EngineUnavailable):
    """FR : moteur en ligne indisponible, avec la raison. EN : online engine unavailable."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class EngineInfo:
    """Fiche d'un moteur / Engine sheet."""

    engine_id: str
    name: str
    needs_key: bool
    unofficial: bool = False
    # FR : champs à remplir : « key », « folder_id », « url », « region ».
    fields: tuple[str, ...] = ()
    # FR : prix indicatif en dollars par million de caractères (None = gratuit).
    price_per_million: float | None = None
    # FR : part gratuite chaque mois, en caractères. EN : free share each month.
    free_characters: int = 0
    signup_url: str = ""


def estimate_cost(info: EngineInfo, characters: int) -> float:
    """FR : coût estimé (en dollars) d'une traduction de « characters » caractères,
         sans compter la part gratuite mensuelle (déjà peut-être utilisée).
    EN : estimated cost (in dollars) of translating "characters" characters,
         not counting the monthly free share (maybe already used).
    """
    if info.price_per_million is None:
        return 0.0
    return round(info.price_per_million * characters / 1_000_000, 2)


def escape_outside_markers(text: str) -> str:
    """FR : échappe & < > sauf dans les repères XML. EN : escape & < > except in XML markers."""
    parts = _XML_MARKER.split(text)
    markers = _XML_MARKER.findall(text)
    escaped = [html.escape(part, quote=False) for part in parts]
    return "".join(piece for pair in zip(escaped, [*markers, ""], strict=True) for piece in pair)


class OnlineEngine(Engine):
    """Base des moteurs en ligne / Base of online engines."""

    online = True
    info: EngineInfo
    # FR : textes et caractères au plus par requête. EN : texts and characters per request.
    max_texts = 50
    max_chars = 4000
    # FR : langues proposées si la liste en direct n'a pas pu être lue.
    # EN : languages offered when the live list could not be read.
    default_languages: frozenset[str] = frozenset()

    def __init__(
        self,
        key: str = "",
        options: dict[str, str] | None = None,
        client_factory: Callable[[], Any] | None = None,
    ) -> None:
        self.key = key.strip()
        self.options = options or {}
        self.client_factory = client_factory
        self._client: Any = None
        self._lock = threading.Lock()
        self.languages: frozenset[str] | None = None

    @property
    def engine_id(self) -> str:  # type: ignore[override]
        return self.info.engine_id

    # ------------------------------------------------------------------
    # FR : Réseau / EN : Network
    # ------------------------------------------------------------------
    def client(self):
        """FR : connexion réutilisée (plus rapide). EN : reused connection (faster)."""
        if self._client is None:
            if self.client_factory is not None:
                self._client = self.client_factory()
            else:
                import httpx

                self._client = httpx.Client(
                    timeout=30, follow_redirects=True, headers={"User-Agent": USER_AGENT}
                )
        return self._client

    def close(self) -> None:
        """FR : ferme la connexion. EN : close the connection."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def request(self, method: str, url: str, **options):
        """Envoie une requête et traduit les erreurs / Send a request and translate errors.

        FR : Renvoie la réponse si tout va bien, sinon lève OnlineError avec une
             raison claire.
        EN : Returns the response when all is well, otherwise raises OnlineError
             with a clear reason.
        """
        import httpx

        try:
            response = self.client().request(method, url, **options)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ProxyError) as error:
            raise OnlineError(
                REASON_OFFLINE, f"{self.info.name} : pas de connexion / no connection"
            ) from error
        except httpx.TimeoutException as error:
            raise OnlineError(
                REASON_SERVICE, f"{self.info.name} : délai dépassé / timed out"
            ) from error
        except httpx.HTTPError as error:
            raise OnlineError(REASON_SERVICE, f"{self.info.name} : {error}") from error
        status = response.status_code
        if status in (401, 403):
            raise OnlineError(
                REASON_KEY, f"{self.info.name} : accès refusé / access refused ({status})"
            )
        if status in (429, 456):
            raise OnlineError(
                REASON_LIMIT, f"{self.info.name} : limite atteinte / limit reached ({status})"
            )
        if status >= 500:
            raise OnlineError(
                REASON_SERVICE, f"{self.info.name} : service en panne / service down ({status})"
            )
        if status >= 400:
            raise OnlineError(
                REASON_SERVICE, f"{self.info.name} : requête refusée / request refused ({status})"
            )
        return response

    # ------------------------------------------------------------------
    # FR : Contrat commun / EN : Common contract
    # ------------------------------------------------------------------
    def code(self, language: str) -> str:
        """FR : code de langue propre au moteur. EN : the engine's own language code."""
        return language

    def supports(self, source_lang: str, target_lang: str) -> bool:
        known = self.languages if self.languages is not None else self.default_languages
        if not known:
            return True
        return self.code(source_lang) in known and self.code(target_lang) in known

    def check_key(self) -> None:
        """FR : une clé est-elle enregistrée ? EN : is a key stored?"""
        if self.info.needs_key and not self.key:
            raise OnlineError(REASON_KEY, f"{self.info.name} : aucune clé / no key")

    def translate(self, texts: Sequence[str], source_lang: str, target_lang: str) -> list[str]:
        self.check_key()
        if source_lang == target_lang:
            return list(texts)
        results: list[str] = [""] * len(texts)
        pending = [(index, text) for index, text in enumerate(texts) if text.strip()]
        for index, text in enumerate(texts):
            if not text.strip():
                results[index] = text
        with self._lock:
            for batch in self._batches(pending):
                translated = self.translate_batch(
                    [text for _i, text in batch], source_lang, target_lang
                )
                if len(translated) != len(batch):
                    raise TranslationError(
                        f"{self.info.name} : réponse incomplète / incomplete answer"
                    )
                for (index, _text), result in zip(batch, translated, strict=True):
                    results[index] = result
        return results

    def _batches(self, items: list[tuple[int, str]]):
        """FR : regroupe les textes en lots qui respectent les limites du moteur.

        EN : group texts into batches respecting the engine's limits.
        """
        batch: list[tuple[int, str]] = []
        size = 0
        for item in items:
            length = len(item[1])
            if batch and (len(batch) >= self.max_texts or size + length > self.max_chars):
                yield batch
                batch, size = [], 0
            batch.append(item)
            size += length
        if batch:
            yield batch

    def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        raise NotImplementedError

    def fetch_languages(self) -> frozenset[str]:
        """FR : langues lues en direct auprès du moteur (si possible).

        EN : languages read live from the engine (when possible).
        """
        return self.default_languages


# FR : Langues de base communes (les 15 langues de l'interface et les plus
#      courantes). EN : Common base languages.
COMMON_LANGUAGES = frozenset(
    "en fr es pt it de nl pl cs ro hu sv da fi el ru uk bg ar fa he hi id ms vi th ja ko zh "
    "tr az uz kk ky tt".split()
)


# ----------------------------------------------------------------------
# FR : Yandex gratuit (widget) / EN : Yandex free (widget)
# ----------------------------------------------------------------------
class YandexFreeEngine(OnlineEngine):
    """Yandex gratuit, méthode du widget (non officielle) / Yandex free, widget method."""

    info = EngineInfo(
        "yandex_free",
        "Yandex",
        needs_key=False,
        unofficial=True,
        signup_url="https://translate.yandex.com/",
    )
    max_texts = 40
    max_chars = 3000
    WIDGET_URL = (
        "https://translate.yandex.net/website-widget/v1/widget.js"
        "?widgetId=ytWidget&pageLang=en&widgetTheme=light&autoMode=false"
    )
    API_URL = "https://translate.yandex.net/api/v1/tr.json"
    SID = re.compile(r"""sid\s*:\s*['"]([0-9a-fA-F.]+)['"]""")
    default_languages = COMMON_LANGUAGES | {"tk", "ba", "cv", "sah", "ug"}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.sid = ""

    def code(self, language: str) -> str:
        return {"pt-BR": "pt-BR", "zh-Hant": "zh"}.get(language, language)

    def session_id(self, refresh: bool = False) -> str:
        """FR : identifiant de session lu dans le widget. EN : session id read from the widget."""
        if refresh or not self.sid:
            script = self.request("GET", self.WIDGET_URL).text
            match = self.SID.search(script)
            if match is None:
                raise OnlineError(REASON_SERVICE, "Yandex : widget modifié / widget changed")
            self.sid = match.group(1)
        return self.sid

    def translate_batch(self, texts, source_lang, target_lang):
        for attempt in (1, 2):
            sid = self.session_id(refresh=attempt == 2)
            try:
                response = self.request(
                    "POST",
                    f"{self.API_URL}/translate",
                    params={
                        "srv": "tr-url-widget",
                        "id": f"{sid}-0-0",
                        "format": "html",
                        "lang": f"{self.code(source_lang)}-{self.code(target_lang)}",
                    },
                    data={"text": [html.escape(text, quote=False) for text in texts]},
                )
                break
            except OnlineError as error:
                # FR : identifiant périmé : on en redemande un, une fois.
                # EN : expired id: ask for a new one, once.
                if attempt == 2 or error.reason != REASON_KEY:
                    raise
        data = response.json()
        if data.get("code", 200) != 200 or "text" not in data:
            raise OnlineError(REASON_SERVICE, f"Yandex : {data.get('message', data)}")
        return [html.unescape(text) for text in data["text"]]

    def fetch_languages(self):
        response = self.request(
            "GET",
            f"{self.API_URL}/getLangs",
            params={"srv": "tr-url-widget", "id": f"{self.session_id()}-0-0", "ui": "en"},
        )
        return frozenset(response.json().get("langs", {}))


# ----------------------------------------------------------------------
# FR : Yandex Cloud (clé officielle) / EN : Yandex Cloud (official key)
# ----------------------------------------------------------------------
class YandexCloudEngine(OnlineEngine):
    """Yandex Cloud Translate v2 (clé API + identifiant de dossier)."""

    info = EngineInfo(
        "yandex_key",
        "Yandex Cloud",
        needs_key=True,
        fields=("key", "folder_id"),
        price_per_million=4.10,
        signup_url="https://yandex.cloud/en/services/translate",
    )
    max_texts = 50
    max_chars = 9000
    URL = "https://translate.api.cloud.yandex.net/translate/v2"
    default_languages = YandexFreeEngine.default_languages

    def translate_batch(self, texts, source_lang, target_lang):
        response = self.request(
            "POST",
            f"{self.URL}/translate",
            headers={"Authorization": f"Api-Key {self.key}"},
            json={
                "folderId": self.options.get("folder_id", ""),
                "texts": texts,
                "sourceLanguageCode": source_lang.split("-")[0],
                "targetLanguageCode": target_lang.split("-")[0],
                "format": "PLAIN_TEXT",
            },
        )
        return [item["text"] for item in response.json()["translations"]]


# ----------------------------------------------------------------------
# FR : Google gratuit / EN : Google free
# ----------------------------------------------------------------------
class GoogleFreeEngine(OnlineEngine):
    """Google Traduction sans compte (non officiel) / Google Translate without account."""

    info = EngineInfo(
        "google_free",
        "Google",
        needs_key=False,
        unofficial=True,
        signup_url="https://translate.google.com/",
    )
    max_texts = 1
    max_chars = 4500
    URL = "https://translate.googleapis.com/translate_a/single"
    default_languages = COMMON_LANGUAGES | {"tk", "ug", "zh-CN", "zh-TW", "pt-PT"}

    def code(self, language: str) -> str:
        return {"pt": "pt-PT", "pt-BR": "pt", "zh": "zh-CN", "zh-Hant": "zh-TW"}.get(
            language, language
        )

    def supports(self, source_lang, target_lang):
        return True  # FR : Google couvre plus de 200 langues / EN : Google covers 200+ languages

    def translate_batch(self, texts, source_lang, target_lang):
        response = self.request(
            "GET",
            self.URL,
            params={
                "client": "gtx",
                "sl": self.code(source_lang),
                "tl": self.code(target_lang),
                "dt": "t",
                "q": texts[0],
            },
        )
        data = response.json()
        try:
            return ["".join(part[0] for part in data[0] if part and part[0])]
        except (TypeError, IndexError) as error:
            raise OnlineError(
                REASON_SERVICE, "Google : réponse inattendue / unexpected answer"
            ) from error


# ----------------------------------------------------------------------
# FR : DeepL / EN : DeepL
# ----------------------------------------------------------------------
class DeepLEngine(OnlineEngine):
    """DeepL API Free ou Pro / DeepL API Free or Pro."""

    info = EngineInfo(
        "deepl",
        "DeepL",
        needs_key=True,
        fields=("key",),
        price_per_million=25.0,
        free_characters=500_000,
        signup_url="https://www.deepl.com/pro-api",
    )
    marker_style = STYLE_XML
    max_texts = 50
    max_chars = 30000
    default_languages = frozenset(
        "en fr es pt pt-BR it de nl pl cs ro hu sv da fi el ru uk bg ar he id ja ko zh zh-Hant "
        "tr lt lv et sk sl nb vi th".split()
    )

    @property
    def url(self) -> str:
        """FR : les clés gratuites finissent par « :fx ». EN : free keys end with ":fx"."""
        host = "api-free.deepl.com" if self.key.endswith(":fx") else "api.deepl.com"
        return f"https://{host}/v2"

    @staticmethod
    def source_code(language: str) -> str:
        return language.split("-")[0].upper()

    @staticmethod
    def target_code(language: str) -> str:
        special = {
            "en": "EN-GB",
            "pt": "PT-PT",
            "pt-BR": "PT-BR",
            "zh": "ZH-HANS",
            "zh-Hant": "ZH-HANT",
        }
        return special.get(language, language.upper())

    def code(self, language: str) -> str:
        return language

    def translate_batch(self, texts, source_lang, target_lang):
        response = self.request(
            "POST",
            f"{self.url}/translate",
            headers={"Authorization": f"DeepL-Auth-Key {self.key}"},
            json={
                "text": [escape_outside_markers(text) for text in texts],
                "source_lang": self.source_code(source_lang),
                "target_lang": self.target_code(target_lang),
                "tag_handling": "xml",
                "ignore_tags": ["x"],
            },
        )
        return [html.unescape(item["text"]) for item in response.json()["translations"]]


# ----------------------------------------------------------------------
# FR : Google Cloud / EN : Google Cloud
# ----------------------------------------------------------------------
class GoogleCloudEngine(OnlineEngine):
    """Google Cloud Translation (v2) avec clé / with key."""

    info = EngineInfo(
        "google_cloud",
        "Google Cloud",
        needs_key=True,
        fields=("key",),
        price_per_million=20.0,
        free_characters=500_000,
        signup_url="https://cloud.google.com/translate",
    )
    max_texts = 100
    max_chars = 25000
    URL = "https://translation.googleapis.com/language/translate/v2"

    def code(self, language: str) -> str:
        return GoogleFreeEngine.code(self, language)

    def supports(self, source_lang, target_lang):
        return True

    def translate_batch(self, texts, source_lang, target_lang):
        response = self.request(
            "POST",
            self.URL,
            params={"key": self.key},
            json={
                "q": texts,
                "source": self.code(source_lang),
                "target": self.code(target_lang),
                "format": "text",
            },
        )
        return [item["translatedText"] for item in response.json()["data"]["translations"]]


# ----------------------------------------------------------------------
# FR : Microsoft / EN : Microsoft
# ----------------------------------------------------------------------
class MicrosoftEngine(OnlineEngine):
    """Microsoft Translator (Azure) avec clé / with key."""

    info = EngineInfo(
        "microsoft",
        "Microsoft Translator",
        needs_key=True,
        fields=("key", "region"),
        price_per_million=10.0,
        free_characters=2_000_000,
        signup_url="https://azure.microsoft.com/products/ai-services/ai-translator",
    )
    max_texts = 100
    max_chars = 9000
    URL = "https://api.cognitive.microsofttranslator.com"

    def code(self, language: str) -> str:
        return {"pt": "pt-PT", "pt-BR": "pt", "zh": "zh-Hans"}.get(language, language)

    def supports(self, source_lang, target_lang):
        return True

    def translate_batch(self, texts, source_lang, target_lang):
        headers = {"Ocp-Apim-Subscription-Key": self.key}
        if self.options.get("region"):
            headers["Ocp-Apim-Subscription-Region"] = self.options["region"]
        response = self.request(
            "POST",
            f"{self.URL}/translate",
            params={
                "api-version": "3.0",
                "from": self.code(source_lang),
                "to": self.code(target_lang),
            },
            headers=headers,
            json=[{"Text": text} for text in texts],
        )
        return [item["translations"][0]["text"] for item in response.json()]


# ----------------------------------------------------------------------
# FR : LibreTranslate / EN : LibreTranslate
# ----------------------------------------------------------------------
class LibreTranslateEngine(OnlineEngine):
    """LibreTranslate (serveur au choix) / LibreTranslate (server of your choice)."""

    info = EngineInfo(
        "libretranslate",
        "LibreTranslate",
        needs_key=False,
        fields=("url", "key"),
        signup_url="https://libretranslate.com/",
    )
    max_texts = 50
    max_chars = 5000
    DEFAULT_URL = "https://libretranslate.com"

    def code(self, language: str) -> str:
        return {"pt-BR": "pb", "zh": "zh-Hans", "zh-Hant": "zh-Hant"}.get(language, language)

    def supports(self, source_lang, target_lang):
        return True

    @property
    def url(self) -> str:
        return (self.options.get("url") or self.DEFAULT_URL).rstrip("/")

    def translate_batch(self, texts, source_lang, target_lang):
        payload = {
            "q": texts,
            "source": self.code(source_lang),
            "target": self.code(target_lang),
            "format": "text",
        }
        if self.key:
            payload["api_key"] = self.key
        response = self.request("POST", f"{self.url}/translate", json=payload)
        translated = response.json()["translatedText"]
        return translated if isinstance(translated, list) else [translated]


# FR : Tous les moteurs en ligne, dans l'ordre par défaut (clé Yandex avant le
#      Yandex gratuit, comme décidé le 18 octobre).
# EN : All online engines, in default order (Yandex key before Yandex free).
ENGINE_CLASSES: dict[str, type[OnlineEngine]] = {
    cls.info.engine_id: cls
    for cls in (
        YandexCloudEngine,
        YandexFreeEngine,
        GoogleFreeEngine,
        DeepLEngine,
        GoogleCloudEngine,
        MicrosoftEngine,
        LibreTranslateEngine,
    )
}
DEFAULT_ORDER = tuple(ENGINE_CLASSES)
# FR : Moteurs activés au départ (sans clé à saisir). EN : Engines enabled at first.
DEFAULT_ENABLED = ("yandex_free", "google_free")


def create_engine(
    engine_id: str,
    key: str = "",
    options: dict[str, str] | None = None,
    client_factory: Callable[[], Any] | None = None,
) -> OnlineEngine:
    """FR : fabrique un moteur en ligne. EN : build an online engine."""
    return ENGINE_CLASSES[engine_id](key, options, client_factory)
