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

"""Thèmes de couleurs de RuneCast / RuneCast colour themes.

FR : Un thème est un petit fichier texte JSON qui donne une couleur à chaque
     « rôle » de l'interface (fond, texte, boutons, sélection…). Les 4 thèmes
     intégrés (Turquoise par défaut, Noir, Sombre, Clair) sont rangés dans
     src/runecast/resources/themes. À l'étape 9, les thèmes personnels
     utiliseront exactement le même format, ce qui permettra de les créer,
     enregistrer, importer et exporter.
     Ce module ne dépend pas de Qt : il lit et vérifie les thèmes ;
     runecast/ui/theme.py les applique à l'écran.

EN : A theme is a small JSON text file giving a colour to each interface
     "role" (background, text, buttons, selection…). The 4 built-in themes
     (Turquoise by default, Black, Dark, Light) live in
     src/runecast/resources/themes. In step 9, custom themes will use exactly
     the same format, so they can be created, saved, imported and exported.
     This module does not depend on Qt: it reads and checks themes;
     runecast/ui/theme.py applies them on screen.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runecast.resources import resource_path

# FR : Version du format des fichiers de thème. EN : Theme file format version.
THEME_FORMAT = 1

# FR : Thème utilisé par défaut (cahier des charges : Turquoise).
# EN : Default theme (specification: Turquoise).
DEFAULT_THEME = "turquoise"

# FR : Thèmes intégrés, dans l'ordre du menu. EN : Built-in themes, in menu order.
BUILTIN_THEME_IDS = ("turquoise", "noir", "sombre", "clair")

# FR : Rôles de couleur obligatoires dans chaque thème.
# EN : Colour roles required in every theme.
COLOR_KEYS = (
    "window",  # FR : fond des fenêtres / EN : window background
    "base",  # FR : fond des champs et tableaux / EN : fields and tables background
    "alternate_base",  # FR : lignes alternées / EN : alternate rows
    "surface",  # FR : boutons, menus / EN : buttons, menus
    "text",  # FR : texte principal / EN : main text
    "disabled_text",  # FR : texte désactivé / EN : disabled text
    "placeholder",  # FR : texte d'exemple / EN : placeholder text
    "highlight",  # FR : sélection / EN : selection
    "highlighted_text",  # FR : texte sélectionné / EN : selected text
    "accent",  # FR : couleur vive (survol, bordures actives) / EN : bright accent
    "link",  # FR : liens / EN : links
    "border",  # FR : bordures / EN : borders
)

# FR : Une couleur s'écrit « #RRGGBB » (ex. #3CCFC7).
# EN : A colour is written "#RRGGBB" (e.g. #3CCFC7).
COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")

# FR : Identifiant d'un thème : lettres minuscules, chiffres et tirets.
# EN : Theme identifier: lower-case letters, digits and hyphens.
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


class ThemeError(ValueError):
    """FR : fichier de thème invalide. EN : invalid theme file."""


@dataclass(frozen=True)
class Theme:
    """Un thème de couleurs / A colour theme."""

    id: str
    name: str  # FR : nom affiché pour un thème personnel / EN : display name of a custom theme
    dark: bool  # FR : thème sombre (barre de titre sombre) / EN : dark theme (dark title bar)
    colors: dict[str, str]
    builtin: bool = False  # FR : thème fourni avec RuneCast / EN : theme shipped with RuneCast


def theme_from_dict(data: Any, builtin: bool = False) -> Theme:
    """Vérifie et construit un thème / Check and build a theme.

    FR : Lève ThemeError avec une explication si le contenu est incorrect.
    EN : Raises ThemeError with an explanation if the content is wrong.
    """
    if not isinstance(data, dict):
        raise ThemeError("le thème doit être un objet JSON / the theme must be a JSON object")
    if data.get("format") != THEME_FORMAT:
        raise ThemeError(f"format de thème inconnu / unknown theme format: {data.get('format')}")
    theme_id = data.get("id")
    if not isinstance(theme_id, str) or not ID_PATTERN.match(theme_id):
        raise ThemeError(f"identifiant invalide / invalid identifier: {theme_id!r}")
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ThemeError("nom manquant / missing name")
    dark = data.get("dark")
    if not isinstance(dark, bool):
        raise ThemeError('« dark » doit valoir true ou false / "dark" must be true or false')
    colors = data.get("colors")
    if not isinstance(colors, dict):
        raise ThemeError("couleurs manquantes / missing colours")
    for key in COLOR_KEYS:
        value = colors.get(key)
        if not isinstance(value, str) or not COLOR_PATTERN.match(value):
            raise ThemeError(f"couleur invalide / invalid colour « {key} » : {value!r}")
    return Theme(
        id=theme_id,
        name=name.strip(),
        dark=dark,
        colors={key: colors[key].upper() for key in COLOR_KEYS},
        builtin=builtin,
    )


def load_theme_file(path: Path, builtin: bool = False) -> Theme:
    """FR : lit un fichier de thème. EN : read a theme file."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        raise ThemeError(f"fichier illisible / unreadable file: {path} ({error})") from error
    return theme_from_dict(data, builtin=builtin)


def builtin_themes() -> dict[str, Theme]:
    """FR : les 4 thèmes fournis avec RuneCast. EN : the 4 themes shipped with RuneCast."""
    return {
        theme_id: load_theme_file(resource_path("themes", f"{theme_id}.json"), builtin=True)
        for theme_id in BUILTIN_THEME_IDS
    }


def find_theme(theme_id: str, themes: dict[str, Theme]) -> Theme:
    """FR : thème demandé, ou Turquoise s'il n'existe pas.

    EN : requested theme, or Turquoise if it does not exist.
    """
    return themes.get(theme_id) or themes[DEFAULT_THEME]


def contrast_ratio(color_a: str, color_b: str) -> float:
    """Contraste entre deux couleurs (norme WCAG) / Contrast between two colours (WCAG).

    FR : De 1 (aucun contraste) à 21 (noir sur blanc). Un texte normal est
         bien lisible à partir de 4,5.
    EN : From 1 (no contrast) to 21 (black on white). Normal text is easily
         readable from 4.5.
    """

    def luminance(color: str) -> float:
        channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    lighter, darker = sorted((luminance(color_a), luminance(color_b)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)
