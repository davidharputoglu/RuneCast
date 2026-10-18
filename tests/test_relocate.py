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

"""Tests du déplacement des données / Data move tests."""

import shutil
from pathlib import Path

import pytest

from runecast.core import paths, relocate


def _fill(app_paths: paths.AppPaths) -> dict[str, Path]:
    """FR : met un fichier dans chaque dossier. EN : put one file in each folder."""
    app_paths.create()
    files = {
        "config": app_paths.config_dir / "settings.json",
        "data": app_paths.data_dir / "modeles" / "en-fr.bin",
        "cache": app_paths.cache_dir / "temp.txt",
        "logs": app_paths.log_dir / "runecast.log",
    }
    for name, path in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"contenu {name}", encoding="utf-8")
    return files


def test_human_size() -> None:
    """FR : tailles lisibles en français. EN : readable sizes in French."""
    assert relocate.human_size(512) == "512 octets"
    assert relocate.human_size(1536) == "1,5 Ko"
    assert relocate.human_size(5 * 1024 * 1024) == "5,0 Mo"


def test_empty_folder_is_accepted(standard_like_paths, custom_paths) -> None:
    """FR : un dossier vide est accepté. EN : an empty folder is accepted."""
    assert relocate.check_destination(custom_paths, standard_like_paths) is None


def test_non_empty_folder_is_refused(standard_like_paths, custom_paths) -> None:
    """FR : un dossier qui contient autre chose est refusé. EN : non-empty refused."""
    custom_paths.root.mkdir(parents=True)
    (custom_paths.root / "photo.jpg").write_text("x", encoding="utf-8")
    assert relocate.check_destination(custom_paths, standard_like_paths)


def test_folder_inside_current_folders_is_refused(standard_like_paths) -> None:
    """FR : un dossier situé dans les dossiers actuels est refusé. EN : nested refused."""
    inside = paths.single_folder_paths(standard_like_paths.data_dir / "ici", paths.MODE_CUSTOM)
    assert relocate.check_destination(inside, standard_like_paths)


def test_same_location_is_refused(custom_paths) -> None:
    """FR : choisir l'emplacement actuel ne fait rien. EN : same location refused."""
    assert relocate.check_destination(custom_paths, custom_paths)


def test_existing_runecast_data_is_detected(custom_paths) -> None:
    """FR : un dossier RuneCast existant est reconnu. EN : existing data detected."""
    _fill(custom_paths)
    assert relocate.has_runecast_data(custom_paths)


def test_copy_verify_then_delete(standard_like_paths, custom_paths, tmp_path) -> None:
    """FR : copie, vérification, puis suppression des anciens fichiers.

    EN : copy, verification, then deletion of the old files.
    """
    files = _fill(standard_like_paths)
    location = standard_like_paths.config_dir / paths.LOCATION_FILE_NAME
    location.write_text("{}", encoding="utf-8")

    plan = relocate.plan_copy(standard_like_paths, custom_paths)
    # FR : 4 fichiers, chacun une seule fois (le cache n'est pas copié deux fois),
    #      et jamais le fichier d'emplacement.
    # EN : 4 files, each only once (the cache is not copied twice), and never
    #      the location file.
    assert len(plan.files) == 4
    report = relocate.copy_and_verify(plan)
    assert report.ok
    assert (custom_paths.cache_dir / "temp.txt").read_text(encoding="utf-8") == "contenu cache"
    assert (custom_paths.data_dir / "modeles" / "en-fr.bin").is_file()
    assert not (custom_paths.data_dir / "Cache").exists()

    deleted = relocate.delete_sources(report, standard_like_paths)
    assert deleted == 4
    assert not any(path.exists() for path in files.values())
    # FR : le fichier d'emplacement n'est jamais supprimé. EN : never deleted.
    assert location.is_file()


def test_existing_file_is_never_overwritten(standard_like_paths, custom_paths) -> None:
    """FR : un fichier déjà présent bloque la copie. EN : existing file blocks copy."""
    _fill(standard_like_paths)
    custom_paths.config_dir.mkdir(parents=True)
    (custom_paths.config_dir / "settings.json").write_text("à garder", encoding="utf-8")
    plan = relocate.plan_copy(standard_like_paths, custom_paths)
    assert plan.conflicts
    report = relocate.copy_and_verify(plan)
    assert not report.ok
    assert (custom_paths.config_dir / "settings.json").read_text(encoding="utf-8") == "à garder"


def test_failed_copy_is_rolled_back(
    standard_like_paths, custom_paths, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR : copie ratée : la destination est nettoyée, les originaux intacts.

    EN : failed copy: destination cleaned up, originals untouched.
    """
    files = _fill(standard_like_paths)
    real_copy = shutil.copy2
    calls = []

    def flaky_copy(source, destination):
        calls.append(source)
        if len(calls) == 2:
            raise OSError("disque plein / disk full")
        return real_copy(source, destination)

    monkeypatch.setattr(relocate.shutil, "copy2", flaky_copy)
    report = relocate.copy_and_verify(relocate.plan_copy(standard_like_paths, custom_paths))
    assert not report.ok
    assert all(path.exists() for path in files.values())
    copied = (
        [p for p in custom_paths.root.rglob("*") if p.is_file()]
        if custom_paths.root.exists()
        else []
    )
    assert copied == []
