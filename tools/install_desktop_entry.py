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

"""Ajoute RuneCast au menu de Linux (développement) / Add RuneCast to the Linux menu (development).

FR : Sous Linux avec Wayland (Fedora 44), le dock n'affiche l'icône d'une
     application que si elle possède un fichier « .desktop ». Quand on lance
     RuneCast depuis le code source, ce fichier n'existe pas encore : ce
     script le crée pour ton compte utilisateur uniquement (aucun mot de passe
     administrateur), avec les icônes. RuneCast apparaît alors aussi dans la
     liste des applications.
     Les vrais paquets .rpm et .deb (étapes 38 et 39) installeront eux-mêmes
     ce fichier ; ce script ne sert que pendant le développement.

EN : On Linux with Wayland (Fedora 44), the dock only shows an application's
     icon if it has a ".desktop" file. When RuneCast runs from the source code,
     that file does not exist yet: this script creates it for your user account
     only (no administrator password), together with the icons. RuneCast then
     also appears in the application list.
     The real .rpm and .deb packages (steps 38 and 39) will install this file
     themselves; this script is only used during development.

Utilisation / Usage :
    uv run python tools/install_desktop_entry.py           (installer / install)
    uv run python tools/install_desktop_entry.py --remove  (retirer / remove)
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# FR : Le script est lancé depuis le dossier du projet : on rend le code de
#      RuneCast importable pour lire son identifiant et ses icônes.
# EN : The script runs from the project folder: make the RuneCast code
#      importable to read its identifier and icons.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from runecast import about  # noqa: E402
from runecast.resources import resource_path  # noqa: E402

# FR : Dossiers standard de Linux pour les fichiers d'un utilisateur.
# EN : Standard Linux folders for a user's files.
DATA_HOME = Path.home() / ".local" / "share"
DESKTOP_FILE = DATA_HOME / "applications" / f"{about.APP_ID}.desktop"
ICON_THEME_DIR = DATA_HOME / "icons" / "hicolor"
ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)


def desktop_file_content(python: str) -> str:
    """Contenu du fichier .desktop / Content of the .desktop file.

    FR : « Exec » lance RuneCast avec le Python du projet (dossier .venv).
    EN : "Exec" starts RuneCast with the project's Python (.venv folder).
    """
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={about.APP_NAME}\n"
        "Comment=Traduction de jeux vidéo\n"
        "Comment[en]=Video game translation\n"
        f'Exec="{python}" -m runecast\n'
        f"Icon={about.APP_ID}\n"
        "Terminal=false\n"
        "Categories=Utility;\n"
        f"StartupWMClass={about.APP_NAME}\n"
    )


def icon_destination(size: int) -> Path:
    """FR : emplacement d'une icône installée. EN : installed icon location."""
    return ICON_THEME_DIR / f"{size}x{size}" / "apps" / f"{about.APP_ID}.png"


def refresh_caches() -> None:
    """FR : prévient le bureau des changements (si les outils existent).

    EN : tell the desktop about the changes (if the tools exist).
    """
    for command in (
        ["update-desktop-database", str(DESKTOP_FILE.parent)],
        ["gtk-update-icon-cache", "--quiet", "--ignore-theme-index", str(ICON_THEME_DIR)],
    ):
        if shutil.which(command[0]):
            subprocess.run(command, check=False)


def install() -> None:
    """Installe le fichier .desktop et les icônes / Install .desktop and icons."""
    DESKTOP_FILE.parent.mkdir(parents=True, exist_ok=True)
    DESKTOP_FILE.write_text(desktop_file_content(sys.executable), encoding="utf-8")
    print(f"  OK  {DESKTOP_FILE}")
    for size in ICON_SIZES:
        target = icon_destination(size)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(resource_path("icons", f"runecast-{size}.png"), target)
        print(f"  OK  {target}")
    refresh_caches()


def remove() -> None:
    """Retire uniquement les fichiers créés par install() / Remove only our files."""
    for path in (DESKTOP_FILE, *(icon_destination(size) for size in ICON_SIZES)):
        if path.exists():
            path.unlink()
            print(f"  retiré / removed  {path}")
    refresh_caches()


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée du script / Script entry point."""
    if not sys.platform.startswith("linux"):
        print("Ce script ne sert que sous Linux. / This script is for Linux only.")
        return 1
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--remove", action="store_true", help="retirer / remove")
    args = parser.parse_args(argv)
    if args.remove:
        remove()
    else:
        install()
    print("Terminé / Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
