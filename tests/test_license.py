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

"""Contrôles automatiques de la licence / Automatic license checks.

FR : Ces tests garantissent la règle du cahier des charges « GPLv3 présente
     dans tous les fichiers sources » : chaque fichier Python du projet doit
     commencer par l'en-tête de licence, et le fichier LICENSE doit contenir
     le texte officiel de la GPLv3. Un nouveau fichier oublié sans en-tête
     fera échouer les tests.
EN : These tests enforce the specification rule "GPLv3 present in every source
     file": every Python file of the project must start with the license
     header, and the LICENSE file must contain the official GPLv3 text. A new
     file added without the header will make the tests fail.
"""

import tomllib
from pathlib import Path

import pytest

# FR : Dossier racine du projet (le dossier parent de « tests »).
# EN : Project root folder (the parent of the "tests" folder).
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# FR : Première ligne obligatoire de chaque fichier Python.
# EN : Mandatory first line of every Python file.
SPDX_LINE = "# SPDX-License-Identifier: GPL-3.0-or-later"


def _python_files() -> list[Path]:
    """FR : liste tous les fichiers .py du code, des outils et des tests.

    EN : list every .py file of the source code, the tools and the tests.
    """
    files: list[Path] = []
    for folder in ("src", "tools", "tests"):
        files.extend(sorted((PROJECT_ROOT / folder).rglob("*.py")))
    return files


def test_there_are_python_files() -> None:
    """FR : sécurité : on a bien trouvé des fichiers. EN : sanity check."""
    assert _python_files(), "Aucun fichier Python trouvé / No Python file found"


@pytest.mark.parametrize("path", _python_files(), ids=lambda p: str(p.relative_to(PROJECT_ROOT)))
def test_every_python_file_has_the_license_header(path: Path) -> None:
    """FR : chaque fichier .py porte l'en-tête GPL. EN : every file has it."""
    text = path.read_text(encoding="utf-8")
    first_line = text.splitlines()[0] if text else ""
    assert first_line == SPDX_LINE
    assert "Copyright (C)" in text
    assert "HARPUTOGLU David" in text
    assert "aidé par l'IA" in text
    assert "GNU General Public License" in text


def test_license_file_is_the_official_gplv3() -> None:
    """FR : LICENSE contient la GPLv3 officielle. EN : official GPLv3 text."""
    text = (PROJECT_ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "GNU GENERAL PUBLIC LICENSE" in text
    assert "Version 3, 29 June 2007" in text
    assert "END OF TERMS AND CONDITIONS" in text


def test_pyproject_declares_the_same_license() -> None:
    """FR : pyproject.toml annonce la même licence. EN : same license declared."""
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]
    assert project["license"] == "GPL-3.0-or-later"
