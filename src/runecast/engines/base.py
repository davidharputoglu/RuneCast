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

"""Contrat commun des moteurs de traduction / Common contract of translation engines.

FR : Un moteur sait dire s'il peut traduire d'une langue vers une autre
     (supports) et traduire une liste de phrases (translate). Il indique
     aussi s'il passe par internet (online) : en mode local, RuneCast
     n'utilise jamais un moteur en ligne (étape 17).
EN : An engine can tell whether it can translate from one language to
     another (supports) and translate a list of sentences (translate). It
     also says whether it goes through the internet (online): in local mode,
     RuneCast never uses an online engine (step 17).
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from runecast.core.protect import STYLE_BRACKETS


class TranslationError(Exception):
    """FR : la traduction a échoué. EN : the translation failed."""


class EngineUnavailable(TranslationError):
    """FR : moteur indisponible (modèle absent, pas d'internet, clé refusée…).

    EN : engine unavailable (missing model, no internet, key refused…).
    """


class Engine(ABC):
    """Un moteur de traduction / A translation engine."""

    # FR : identifiant court (« local », « yandex »…). EN : short identifier.
    engine_id: str = ""
    # FR : passe par internet ? EN : goes through the internet?
    online: bool = False
    # FR : forme des repères de protection qu'il garde le mieux (étape 11).
    # EN : shape of the protection markers it keeps best (step 11).
    marker_style: str = STYLE_BRACKETS

    @abstractmethod
    def supports(self, source_lang: str, target_lang: str) -> bool:
        """FR : peut-il traduire de « source_lang » vers « target_lang » ?

        EN : can it translate from "source_lang" to "target_lang"?
        """

    @abstractmethod
    def translate(self, texts: Sequence[str], source_lang: str, target_lang: str) -> list[str]:
        """FR : traduit chaque texte ; renvoie autant de traductions que de textes.

             Lève EngineUnavailable ou TranslationError en cas d'échec.
        EN : translate each text; returns as many translations as texts.
             Raises EngineUnavailable or TranslationError on failure.
        """
