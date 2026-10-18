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

"""Langues de l'interface de RuneCast / RuneCast interface languages.

FR : Liste des langues dans lesquelles l'interface de RuneCast est disponible,
     et choix de la langue à utiliser. Les textes sont écrits en français dans
     le code (langue « source ») ; les autres langues sont des traductions
     rangées dans le dossier « translations ».
     Pour l'instant : français, anglais et arabe (premier essai de l'écriture
     de droite à gauche). Les 12 autres langues prévues (8 langues turciques,
     espagnol, portugais, italien) seront ajoutées à l'étape 33.
     Attention : ce sont les langues de l'INTERFACE ; les jeux, eux, pourront
     être traduits vers bien d'autres langues.

EN : List of the languages in which the RuneCast interface is available, and
     choice of the language to use. Texts are written in French in the code
     ("source" language); the other languages are translations stored in the
     "translations" folder. For now: French, English and Arabic (first
     right-to-left trial). The 12 other planned languages will be added in
     step 33. Note: these are INTERFACE languages; games can be translated
     into many more languages.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    """Une langue de l'interface / An interface language."""

    code: str  # FR : code ISO (ex. « fr ») / EN : ISO code (e.g. "fr")
    native_name: str  # FR : nom dans la langue elle-même / EN : name in the language itself
    right_to_left: bool = False  # FR : écriture de droite à gauche / EN : right-to-left script


# FR : Langue dans laquelle les textes sont écrits dans le code.
# EN : Language in which texts are written in the code.
SOURCE_LANGUAGE = "fr"

# FR : Langue utilisée si la langue du système n'est pas disponible.
# EN : Language used when the system language is not available.
FALLBACK_LANGUAGE = "en"

# FR : Réglage spécial : suivre la langue du système.
# EN : Special setting: follow the system language.
SYSTEM_LANGUAGE = ""

# FR : Langues disponibles, dans l'ordre d'affichage du menu.
# EN : Available languages, in menu display order.
LANGUAGES: dict[str, Language] = {
    "fr": Language("fr", "Français"),
    "en": Language("en", "English"),
    "ar": Language("ar", "العربية", right_to_left=True),
}


def translated_languages() -> list[str]:
    """FR : langues qui ont un fichier de traduction (toutes sauf la source).

    EN : languages that have a translation file (all but the source one).
    """
    return [code for code in LANGUAGES if code != SOURCE_LANGUAGE]


def resolve_language(setting: str, system_locale: str) -> str:
    """Choisit la langue à afficher / Choose the language to display.

    FR : « setting » est le réglage de l'utilisateur (vide = langue du
         système) ; « system_locale » est la langue du système, par exemple
         « fr_FR » ou « ar_SA ». Si elle n'est pas disponible : anglais.
    EN : "setting" is the user's setting (empty = system language);
         "system_locale" is the system language, e.g. "fr_FR" or "ar_SA".
         If it is not available: English.
    """
    if setting in LANGUAGES:
        return setting
    system_code = system_locale.replace("-", "_").split("_")[0].lower()
    if system_code in LANGUAGES:
        return system_code
    return FALLBACK_LANGUAGE
