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

"""Fabrique les icônes de RuneCast à partir du logo / Build RuneCast icons from the logo.

FR : Ce script part de l'image fournie par l'auteur
     (assets/branding/runecast-logo-source.png) et ne la retouche PAS :
       1. il repère l'hexagone turquoise dans l'image ;
       2. il découpe un carré centré sur cet hexagone (une icône doit être
          carrée, alors que l'image d'origine est en largeur) ;
       3. il réduit ce carré aux tailles standard de Windows, de Linux et du
          web (favicon).
     L'image d'origine n'est jamais modifiée. Si le logo change un jour, il
     suffit de remplacer l'image source et de relancer ce script.

EN : This script starts from the image provided by the author
     (assets/branding/runecast-logo-source.png) and does NOT retouch it:
       1. it locates the turquoise hexagon in the image;
       2. it cuts a square centred on that hexagon (an icon must be square,
          while the original image is wide);
       3. it scales that square down to the standard Windows, Linux and web
          (favicon) sizes.
     The original image is never modified. If the logo changes one day, just
     replace the source image and run this script again.

Utilisation / Usage :
    uv run python tools/make_icons.py
"""

from pathlib import Path

from PIL import Image, ImageChops

# FR : Dossiers du projet. ROOT est le dossier principal (parent de « tools »).
# EN : Project folders. ROOT is the main folder (parent of "tools").
ROOT = Path(__file__).resolve().parent.parent
SOURCE_IMAGE = ROOT / "assets" / "branding" / "runecast-logo-source.png"
BRANDING_DIR = ROOT / "assets" / "branding"
ICONS_DIR = ROOT / "assets" / "icons"

# FR : Tailles (en pixels) attendues par Linux pour les icônes d'application.
# EN : Sizes (in pixels) expected by Linux for application icons.
LINUX_SIZES = (16, 22, 24, 32, 48, 64, 128, 256, 512)

# FR : Tailles rangées dans le fichier .ico de Windows (256 au maximum).
# EN : Sizes stored in the Windows .ico file (256 at most).
WINDOWS_ICO_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)

# FR : Tailles du favicon (petite icône des onglets de navigateur).
# EN : Favicon sizes (small icon shown in browser tabs).
FAVICON_SIZES = (16, 32, 48)

# FR : Un pixel fait partie du logo si son vert ET son bleu dépassent ce seuil
#      (sur 255). Le fond de l'image est très sombre, le logo turquoise est clair.
# EN : A pixel belongs to the logo if both its green AND blue values exceed this
#      threshold (out of 255). The background is very dark, the turquoise logo bright.
LOGO_BRIGHTNESS_THRESHOLD = 110

# FR : Marge autour de l'hexagone : 12 % de sa plus grande dimension.
# EN : Margin around the hexagon: 12 % of its largest dimension.
MARGIN_RATIO = 0.12

# Type « boîte » : (gauche, haut, droite, bas) / "Box" type: (left, top, right, bottom)
Box = tuple[int, int, int, int]


def find_logo_box(image: Image.Image) -> Box:
    """Repère le rectangle qui contient le logo / Locate the rectangle holding the logo.

    FR : On fabrique un masque noir et blanc : blanc là où le pixel est assez
         vert ET assez bleu (le turquoise du logo), noir ailleurs. Pillow donne
         ensuite le plus petit rectangle qui contient tout le blanc.
    EN : We build a black and white mask: white where the pixel is green enough
         AND blue enough (the logo's turquoise), black elsewhere. Pillow then
         gives the smallest rectangle that contains all the white.
    """
    _red, green, blue = image.convert("RGB").split()

    def to_mask(channel: Image.Image) -> Image.Image:
        return channel.point(lambda value: 255 if value > LOGO_BRIGHTNESS_THRESHOLD else 0)

    # FR : « multiply » ne garde blanc que ce qui est blanc dans les deux masques.
    # EN : "multiply" only keeps white what is white in both masks.
    mask = ImageChops.multiply(to_mask(green), to_mask(blue))
    box = mask.getbbox()
    if box is None:
        raise ValueError(
            "Logo introuvable dans l'image / Logo not found in the image: " + str(SOURCE_IMAGE)
        )
    return box


def square_crop_box(logo_box: Box, image_size: tuple[int, int], margin_ratio: float) -> Box:
    """Calcule un carré centré sur le logo / Compute a square centred on the logo.

    FR : Le côté du carré = plus grande dimension du logo + la marge. Le carré
         est ensuite décalé si besoin pour ne jamais sortir de l'image.
    EN : Square side = largest logo dimension + margin. The square is then
         shifted if needed so it never goes outside the image.
    """
    left, top, right, bottom = logo_box
    image_width, image_height = image_size

    side = round(max(right - left, bottom - top) * (1 + margin_ratio))
    side = min(side, image_width, image_height)

    centre_x = (left + right) / 2
    centre_y = (top + bottom) / 2
    x0 = round(centre_x - side / 2)
    y0 = round(centre_y - side / 2)

    # FR : On garde le carré à l'intérieur de l'image.
    # EN : Keep the square inside the image.
    x0 = max(0, min(x0, image_width - side))
    y0 = max(0, min(y0, image_height - side))
    return (x0, y0, x0 + side, y0 + side)


def make_square_logo(source: Path = SOURCE_IMAGE) -> Image.Image:
    """Découpe le logo en carré, sans retouche / Cut the logo into a square, untouched."""
    with Image.open(source) as original:
        image = original.convert("RGB")
    box = square_crop_box(find_logo_box(image), image.size, MARGIN_RATIO)
    return image.crop(box)


def resize(square: Image.Image, size: int) -> Image.Image:
    """Réduit le carré à la taille voulue / Scale the square to the wanted size.

    FR : LANCZOS est le mode de réduction le plus net de Pillow.
    EN : LANCZOS is Pillow's sharpest downscaling mode.
    """
    return square.resize((size, size), Image.Resampling.LANCZOS)


def save_ico(square: Image.Image, path: Path, sizes: tuple[int, ...]) -> None:
    """Enregistre un fichier .ico multi-tailles / Save a multi-size .ico file.

    FR : Chaque taille est réduite par nous (avec LANCZOS), puis rangée dans le
         même fichier. Windows choisit tout seul la taille adaptée à l'affichage.
    EN : Each size is scaled by us (with LANCZOS), then stored in the same file.
         Windows picks the right size for each display on its own.
    """
    frames = [resize(square, size) for size in sorted(sizes, reverse=True)]
    largest, *others = frames
    largest.save(path, format="ICO", sizes=[(s, s) for s in sizes], append_images=others)


def build_all(source: Path = SOURCE_IMAGE, root: Path = ROOT) -> list[Path]:
    """Fabrique tous les fichiers d'icônes / Build every icon file.

    FR : Renvoie la liste des fichiers écrits. « root » permet aux tests
         d'écrire dans un dossier temporaire au lieu du vrai projet.
    EN : Returns the list of written files. "root" lets the tests write into a
         temporary folder instead of the real project.
    """
    branding_dir = root / "assets" / "branding"
    icons_dir = root / "assets" / "icons"
    png_dir = icons_dir / "png"
    for folder in (branding_dir, png_dir):
        folder.mkdir(parents=True, exist_ok=True)

    square = make_square_logo(source)
    written: list[Path] = []

    # FR : 1. Le logo carré en pleine résolution (fenêtre « À propos », README…).
    # EN : 1. The full-resolution square logo ("About" window, README…).
    square_path = branding_dir / "runecast-logo-square.png"
    square.save(square_path)
    written.append(square_path)

    # FR : 2. Les PNG pour Linux, une taille par fichier.
    # EN : 2. The PNG files for Linux, one size per file.
    for size in LINUX_SIZES:
        png_path = png_dir / f"runecast-{size}.png"
        resize(square, size).save(png_path)
        written.append(png_path)

    # FR : 3. L'icône Windows (.ico) et le favicon.
    # EN : 3. The Windows icon (.ico) and the favicon.
    ico_path = icons_dir / "runecast.ico"
    save_ico(square, ico_path, WINDOWS_ICO_SIZES)
    written.append(ico_path)

    favicon_path = icons_dir / "favicon.ico"
    save_ico(square, favicon_path, FAVICON_SIZES)
    written.append(favicon_path)

    return written


def main() -> int:
    """Point d'entrée du script / Script entry point."""
    print("Fabrication des icônes / Building icons...")
    for path in build_all():
        print(f"  OK  {path.relative_to(ROOT)}")
    print("Terminé / Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
