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

"""Tests des dossiers de données / Data folder tests."""

import sys
from pathlib import Path

import pytest

from runecast.core import paths


def test_portable_marker_enables_portable_mode(tmp_path: Path) -> None:
    """FR : « portable.txt » active le mode portable. EN : marker enables portable."""
    (tmp_path / paths.PORTABLE_MARKER).write_text("", encoding="utf-8")
    assert paths.portable_root(tmp_path) == tmp_path / paths.PORTABLE_DATA_FOLDER


def test_no_marker_means_no_portable_mode(tmp_path: Path) -> None:
    """FR : sans fichier, pas de mode portable. EN : no marker, no portable mode."""
    assert paths.portable_root(tmp_path) is None


def test_single_folder_layout(tmp_path: Path) -> None:
    """FR : en mode portable, tout est dans un seul dossier. EN : one folder for all."""
    app_paths = paths.single_folder_paths(tmp_path, paths.MODE_PORTABLE)
    assert app_paths.portable
    assert app_paths.root == tmp_path
    for folder in app_paths.folders().values():
        assert folder.parent == tmp_path
    assert app_paths.settings_file == tmp_path / "config" / paths.SETTINGS_FILE_NAME


def test_create_makes_every_folder(tmp_path: Path) -> None:
    """FR : create() crée les 4 dossiers. EN : create() makes the 4 folders."""
    app_paths = paths.single_folder_paths(tmp_path / "x", paths.MODE_CUSTOM)
    app_paths.create()
    assert all(folder.is_dir() for folder in app_paths.folders().values())


def test_system_paths_follow_the_standard(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """FR : les dossiers normaux suivent la norme du système (choix du 18/10/2026).

    EN : normal folders follow the system's standard (decision of 18/10/2026).
    """
    if sys.platform == "win32":
        app_paths = paths.system_paths()
        assert app_paths.config_dir.name == "RuneCast"
        assert "Roaming" in str(app_paths.config_dir)
        assert app_paths.data_dir.name == "RuneCast"
        assert "Local" in str(app_paths.data_dir)
    else:
        for variable in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME"):
            monkeypatch.delenv(variable, raising=False)
        monkeypatch.setenv("HOME", str(tmp_path))
        app_paths = paths.system_paths()
        assert app_paths.config_dir == tmp_path / ".config" / "runecast"
        assert app_paths.data_dir == tmp_path / ".local" / "share" / "runecast"
        assert app_paths.cache_dir == tmp_path / ".cache" / "runecast"
    assert app_paths.mode == paths.MODE_NORMAL
    assert app_paths.config_dir != app_paths.data_dir


def test_chosen_folder_is_remembered(tmp_path: Path) -> None:
    """FR : le dossier choisi est mémorisé, puis oublié au retour à la normale.

    EN : the chosen folder is remembered, then forgotten when going back.
    """
    chosen = tmp_path / "mes-donnees"
    paths.write_custom_root(chosen)
    assert paths.read_custom_root() == chosen
    resolved = paths.resolve_paths()
    assert resolved.mode == paths.MODE_CUSTOM
    assert resolved.root == chosen

    paths.write_custom_root(None)
    assert paths.read_custom_root() is None
    assert paths.resolve_paths().mode == paths.MODE_NORMAL


def test_unavailable_chosen_folder_falls_back(tmp_path: Path) -> None:
    """FR : dossier choisi impossible à créer : emplacement normal + avertissement.

    EN : chosen folder cannot be created: normal location + warning.
    """
    blocker = tmp_path / "un-fichier.txt"
    blocker.write_text("ceci n'est pas un dossier", encoding="utf-8")
    paths.write_custom_root(blocker / "sous-dossier")
    resolved = paths.resolve_paths()
    assert resolved.mode == paths.MODE_NORMAL
    assert resolved.unavailable_custom_root == blocker / "sous-dossier"


def test_damaged_location_file_is_ignored(isolated_location_file: Path) -> None:
    """FR : un fichier d'emplacement abîmé est ignoré. EN : damaged file ignored."""
    isolated_location_file.parent.mkdir(parents=True, exist_ok=True)
    isolated_location_file.write_text("{ pas du json", encoding="utf-8")
    assert paths.read_custom_root() is None


def test_portable_option_uses_portable_data_folder() -> None:
    """FR : « --portable » range tout dans « portable-data ». EN : --portable folder."""
    resolved = paths.resolve_paths(force_portable=True)
    assert resolved.portable
    assert resolved.root == paths.application_folder() / paths.DEV_PORTABLE_FOLDER
