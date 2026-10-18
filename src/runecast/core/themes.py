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
     src/runecast/resources/themes. Les thèmes personnels utilisent
     exactement le même format : ils sont rangés dans le sous-dossier
     « themes » du dossier des réglages, et peuvent être créés, enregistrés,
     importés, exportés et supprimés.
     Ce module ne dépend pas de Qt : il lit et vérifie les thèmes ;
     runecast/ui/theme.py les applique à l'écran.

EN : A theme is a small JSON text file giving a colour to each interface
     "role" (background, text, buttons, selection…). The 4 built-in themes
     (Turquoise by default, Black, Dark, Light) live in
     src/runecast/resources/themes. Custom themes use exactly the same
     format: they live in the "themes" subfolder of the settings folder, and
     can be created, saved, imported, exported and deleted.
     This module does not depend on Qt: it reads and checks themes;
     runecast/ui/theme.py applies them on screen.
"""

import json
import logging
import os
import re
import unicodedata
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from runecast.resources import resource_path

logger = logging.getLogger(__name__)

# FR : Version du format des fichiers de thème. EN : Theme file format version.
THEME_FORMAT = 1

# FR : Thème utilisé par défaut (cahier des charges : Turquoise).
# EN : Default theme (specification: Turquoise).
DEFAULT_THEME = "turquoise"

# FR : Thèmes intégrés, dans l'ordre du menu. EN : Built-in themes, in menu order.
BUILTIN_THEME_IDS = ("turquoise", "noir", "sombre", "clair")

# FR : Nom du sous-dossier des thèmes personnels, dans le dossier des réglages.
# EN : Name of the custom themes subfolder, inside the settings folder.
CUSTOM_THEMES_FOLDER = "themes"

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


def theme_to_dict(theme: Theme) -> dict[str, Any]:
    """FR : contenu du fichier JSON d'un thème. EN : JSON file content of a theme."""
    return {
        "format": THEME_FORMAT,
        "id": theme.id,
        "name": theme.name,
        "dark": theme.dark,
        "colors": {key: theme.colors[key] for key in COLOR_KEYS},
    }


def make_theme_id(name: str, taken: set[str]) -> str:
    """Fabrique un identifiant libre à partir d'un nom / Build a free identifier from a name.

    FR : « Mon Thème Été » donne « mon-theme-ete ». Si l'identifiant est déjà
         pris (thème intégré ou personnel), on ajoute « -2 », « -3 »…
         Un nom sans lettres latines (arabe, cyrillique…) donne « theme ».
    EN : "Mon Thème Été" gives "mon-theme-ete". If the identifier is already
         taken (built-in or custom theme), "-2", "-3"… is added. A name
         without Latin letters (Arabic, Cyrillic…) gives "theme".
    """
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")[:48] or "theme"
    candidate = slug
    counter = 2
    while candidate in taken:
        candidate = f"{slug}-{counter}"
        counter += 1
    return candidate


def custom_themes_folder(config_dir: Path) -> Path:
    """FR : dossier des thèmes personnels. EN : custom themes folder."""
    return config_dir / CUSTOM_THEMES_FOLDER


def load_custom_themes(folder: Path) -> dict[str, Theme]:
    """Lit les thèmes personnels / Read the custom themes.

    FR : Un fichier abîmé est ignoré (et signalé dans le journal) : il ne doit
         jamais empêcher RuneCast de démarrer. Il n'est pas supprimé.
    EN : A damaged file is skipped (and reported in the log): it must never
         prevent RuneCast from starting. It is not deleted.
    """
    themes: dict[str, Theme] = {}
    if not folder.is_dir():
        return themes
    for path in sorted(folder.glob("*.json")):
        try:
            theme = load_theme_file(path)
        except ThemeError as error:
            logger.warning("Thème ignoré / Theme skipped: %s (%s)", path, error)
            continue
        if theme.id in BUILTIN_THEME_IDS or theme.id in themes:
            logger.warning("Identifiant déjà utilisé / Identifier already used: %s", path)
            continue
        themes[theme.id] = theme
    return themes


def all_themes(config_dir: Path) -> dict[str, Theme]:
    """FR : thèmes intégrés puis thèmes personnels. EN : built-in then custom themes."""
    themes = builtin_themes()
    themes.update(load_custom_themes(custom_themes_folder(config_dir)))
    return themes


def save_custom_theme(theme: Theme, folder: Path) -> Path:
    """Enregistre un thème personnel / Save a custom theme.

    FR : Écriture « atomique » (fichier temporaire puis remplacement), comme
         pour les réglages. Les thèmes intégrés ne peuvent pas être écrasés.
    EN : "Atomic" write (temporary file then replacement), like the settings.
         Built-in themes can never be overwritten.
    """
    if theme.builtin or theme.id in BUILTIN_THEME_IDS:
        raise ThemeError("un thème intégré ne peut pas être modifié / built-in theme")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{theme.id}.json"
    temporary = path.with_name(path.name + ".tmp")
    content = json.dumps(theme_to_dict(theme), indent=2, ensure_ascii=False) + "\n"
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)
    return path


def delete_custom_theme(theme_id: str, folder: Path) -> None:
    """FR : supprime un thème personnel (jamais un thème intégré).

    EN : delete a custom theme (never a built-in one).
    """
    if theme_id in BUILTIN_THEME_IDS:
        raise ThemeError("un thème intégré ne peut pas être supprimé / built-in theme")
    (folder / f"{theme_id}.json").unlink(missing_ok=True)


def duplicate_theme(theme: Theme, new_name: str, taken: set[str]) -> Theme:
    """FR : copie d'un thème, sous un nouveau nom et un identifiant libre.

    EN : copy of a theme, with a new name and a free identifier.
    """
    return replace(
        theme,
        id=make_theme_id(new_name, taken),
        name=new_name,
        colors=dict(theme.colors),
        builtin=False,
    )


def import_theme(source: Path, folder: Path, taken: set[str]) -> Theme:
    """Importe un fichier de thème / Import a theme file.

    FR : Le fichier est vérifié (ThemeError s'il est incorrect), reçoit un
         identifiant libre s'il est déjà pris, puis est copié dans le dossier
         des thèmes personnels. Le fichier d'origine n'est pas modifié.
    EN : The file is checked (ThemeError if wrong), gets a free identifier if
         its own is taken, then is copied into the custom themes folder. The
         original file is not modified.
    """
    theme = load_theme_file(source)
    if theme.id in taken or theme.id in BUILTIN_THEME_IDS:
        theme = replace(theme, id=make_theme_id(theme.name, taken | set(BUILTIN_THEME_IDS)))
    save_custom_theme(theme, folder)
    return theme


def export_theme(theme: Theme, destination: Path) -> None:
    """FR : écrit un thème dans un fichier, pour le partager. EN : write a theme to share it."""
    content = json.dumps(theme_to_dict(theme), indent=2, ensure_ascii=False) + "\n"
    destination.write_text(content, encoding="utf-8")


# FR : Paires « texte / fond » dont la lisibilité est contrôlée.
# EN : "text / background" pairs whose readability is checked.
READABILITY_PAIRS = (
    ("text", "window"),
    ("text", "base"),
    ("text", "surface"),
    ("link", "base"),
    ("highlighted_text", "highlight"),
    ("placeholder", "base"),
)

# FR : Contraste minimal conseillé pour un texte (norme WCAG).
# EN : Minimum recommended contrast for text (WCAG standard).
MINIMUM_CONTRAST = 4.5


def readability_problems(colors: dict[str, str]) -> list[tuple[str, str, float]]:
    """FR : paires peu lisibles : (texte, fond, contraste). EN : hard-to-read pairs."""
    problems = []
    for foreground, background in READABILITY_PAIRS:
        ratio = contrast_ratio(colors[foreground], colors[background])
        if ratio < MINIMUM_CONTRAST:
            problems.append((foreground, background, ratio))
    return problems


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
