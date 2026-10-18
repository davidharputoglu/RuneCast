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

"""Tests des icônes / Icon tests.

FR : Ces tests vérifient que toutes les icônes existent, qu'elles ont la
     bonne taille, et qu'elles correspondent bien au logo d'origine (on les
     refabrique dans un dossier temporaire et on compare les pixels).
EN : These tests check that every icon exists, has the right size, and
     really matches the original logo (they are rebuilt in a temporary folder
     and the pixels are compared).
"""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from PIL import Image, ImageChops

# FR : Dossier principal du projet. EN : Project main folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = PROJECT_ROOT / "assets" / "icons"


def _load_make_icons() -> ModuleType:
    """FR : charge tools/make_icons.py (ce n'est pas un paquet Python).

    EN : load tools/make_icons.py (it is not a Python package).
    """
    path = PROJECT_ROOT / "tools" / "make_icons.py"
    spec = importlib.util.spec_from_file_location("make_icons", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


make_icons = _load_make_icons()


@pytest.mark.parametrize("size", make_icons.LINUX_SIZES)
def test_linux_png_exists_with_the_right_size(size: int) -> None:
    """FR : chaque PNG Linux existe et a la bonne taille. EN : right PNG size."""
    with Image.open(ICONS_DIR / "png" / f"runecast-{size}.png") as image:
        assert image.size == (size, size)


def test_windows_ico_contains_every_size() -> None:
    """FR : le .ico Windows contient toutes les tailles. EN : all .ico sizes."""
    with Image.open(ICONS_DIR / "runecast.ico") as icon:
        sizes = icon.info["sizes"]
    for size in make_icons.WINDOWS_ICO_SIZES:
        assert (size, size) in sizes


def test_favicon_contains_every_size() -> None:
    """FR : le favicon contient 16, 32 et 48 px. EN : favicon sizes."""
    with Image.open(ICONS_DIR / "favicon.ico") as icon:
        sizes = icon.info["sizes"]
    for size in make_icons.FAVICON_SIZES:
        assert (size, size) in sizes


def test_square_logo_is_square_and_large_enough() -> None:
    """FR : le logo carré est carré et assez grand pour 512 px.

    EN : the square logo is square and large enough for 512 px.
    """
    with Image.open(PROJECT_ROOT / "assets" / "branding" / "runecast-logo-square.png") as logo:
        width, height = logo.size
    assert width == height
    assert width >= max(make_icons.LINUX_SIZES)


def test_square_crop_stays_inside_the_image() -> None:
    """FR : le carré ne sort jamais de l'image, même près d'un bord.

    EN : the square never leaves the image, even near an edge.
    """
    box = make_icons.square_crop_box((0, 0, 100, 50), (300, 200), 0.12)
    left, top, right, bottom = box
    assert right - left == bottom - top
    assert left >= 0 and top >= 0 and right <= 300 and bottom <= 200


def test_logo_is_found_on_a_dark_background() -> None:
    """FR : sur une image sombre, le carré turquoise est bien retrouvé.

    EN : on a dark image, the turquoise square is found.
    """
    image = Image.new("RGB", (200, 100), (20, 30, 35))
    image.paste((60, 220, 210), (50, 20, 90, 70))
    assert make_icons.find_logo_box(image) == (50, 20, 90, 70)


def test_committed_icons_match_the_original_logo(tmp_path: Path) -> None:
    """FR : les icônes du dépôt sont bien issues du logo d'origine, sans retouche.

    EN : the icons in the repository really come from the untouched original logo.
    """
    make_icons.build_all(root=tmp_path)
    for size in (16, 48, 256, 512):
        name = Path("assets") / "icons" / "png" / f"runecast-{size}.png"
        with Image.open(PROJECT_ROOT / name) as committed, Image.open(tmp_path / name) as rebuilt:
            difference = ImageChops.difference(committed.convert("RGB"), rebuilt.convert("RGB"))
            # FR : on tolère un écart de 2 sur 255 (arrondis selon le système).
            # EN : a gap of 2 out of 255 is tolerated (rounding between systems).
            assert max(high for _low, high in difference.getextrema()) <= 2
