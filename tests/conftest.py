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

"""Réglages communs à tous les tests / Settings shared by all tests.

FR : - Les tests des fenêtres s'exécutent « hors écran » : Qt dessine les
       fenêtres en mémoire, sans les afficher. Les tests ne font donc rien
       apparaître sur ton bureau, et ils fonctionnent aussi sur les serveurs
       de GitHub, qui n'ont pas d'écran.
     - Les tests n'écrivent JAMAIS dans tes vrais dossiers RuneCast : tout se
       passe dans des dossiers temporaires, effacés après les tests.
EN : - Window tests run "offscreen": Qt draws the windows in memory without
       showing them, so nothing pops up on your desktop, and they also work on
       GitHub's servers, which have no screen.
     - Tests NEVER write into your real RuneCast folders: everything happens
       in temporary folders, deleted after the tests.
"""

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from runecast.core import paths  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_location_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """FR : le fichier « emplacement.json » est rangé dans un dossier temporaire.

    EN : the "emplacement.json" file is kept in a temporary folder.
    """
    location = tmp_path / "standard-config" / paths.LOCATION_FILE_NAME
    monkeypatch.setattr(paths, "location_file", lambda: location)
    return location


@pytest.fixture
def standard_like_paths(tmp_path: Path) -> paths.AppPaths:
    """FR : dossiers « normaux » fictifs, rangés comme sous Windows (le cache et
         les journaux DANS le dossier des gros fichiers).

    EN : fake "normal" folders, laid out like on Windows (cache and logs INSIDE
         the large-files folder).
    """
    local = tmp_path / "Local" / "RuneCast"
    return paths.AppPaths(
        mode=paths.MODE_NORMAL,
        config_dir=tmp_path / "standard-config",
        data_dir=local,
        cache_dir=local / "Cache",
        log_dir=local / "Logs",
    )


@pytest.fixture
def custom_paths(tmp_path: Path) -> paths.AppPaths:
    """FR : un dossier personnalisé fictif. EN : a fake custom folder."""
    return paths.single_folder_paths(tmp_path / "mes-donnees", paths.MODE_CUSTOM)
