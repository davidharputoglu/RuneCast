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

"""Tests des réglages et du journal / Settings and log tests."""

import json
import logging
from pathlib import Path

from runecast.core import logs
from runecast.core.settings import SCHEMA_VERSION, Settings, load_settings, save_settings


def test_missing_file_gives_defaults(tmp_path: Path) -> None:
    """FR : premier lancement : réglages par défaut. EN : first launch: defaults."""
    settings = load_settings(tmp_path / "settings.json")
    assert settings.theme == "turquoise"
    assert settings.interface_language == "fr"
    assert settings.schema_version == SCHEMA_VERSION


def test_settings_survive_a_restart(tmp_path: Path) -> None:
    """FR : ce qui est enregistré est relu à l'identique. EN : saved = reloaded."""
    path = tmp_path / "settings.json"
    save_settings(Settings(theme="sombre", window_geometry="abc"), path)
    reloaded = load_settings(path)
    assert reloaded.theme == "sombre"
    assert reloaded.window_geometry == "abc"
    assert not path.with_name("settings.json.tmp").exists()


def test_previous_file_is_kept_as_backup(tmp_path: Path) -> None:
    """FR : l'ancien fichier est gardé en .bak. EN : previous file kept as .bak."""
    path = tmp_path / "settings.json"
    save_settings(Settings(theme="clair"), path)
    save_settings(Settings(theme="noir"), path)
    backup = json.loads(path.with_name("settings.json.bak").read_text(encoding="utf-8"))
    assert backup["theme"] == "clair"


def test_damaged_file_is_set_aside_not_deleted(tmp_path: Path) -> None:
    """FR : un fichier abîmé est mis de côté, jamais effacé. EN : damaged file kept."""
    path = tmp_path / "settings.json"
    path.write_text("{ ceci n'est pas du json", encoding="utf-8")
    settings = load_settings(path)
    assert settings.theme == "turquoise"
    kept = list(tmp_path.glob("settings.json.abime-*"))
    assert len(kept) == 1
    assert kept[0].read_text(encoding="utf-8") == "{ ceci n'est pas du json"


def test_unknown_settings_are_preserved(tmp_path: Path) -> None:
    """FR : les réglages d'une version plus récente ne sont pas perdus.

    EN : settings from a newer version are not lost.
    """
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"schema_version": 1, "futur": 42}), encoding="utf-8")
    settings = load_settings(path)
    save_settings(settings, path)
    assert json.loads(path.read_text(encoding="utf-8"))["futur"] == 42


def test_log_file_is_written(tmp_path: Path) -> None:
    """FR : le journal est bien écrit dans le dossier des journaux. EN : log written."""
    log_file = logs.setup_logging(tmp_path)
    logging.getLogger("runecast.test").info("bonjour")
    logs.stop_file_logging()
    assert "bonjour" in log_file.read_text(encoding="utf-8")


def test_log_is_not_duplicated_when_set_up_twice(tmp_path: Path) -> None:
    """FR : pas de lignes en double. EN : no duplicated lines."""
    log_file = logs.setup_logging(tmp_path)
    logs.setup_logging(tmp_path)
    logging.getLogger("runecast.test").info("une seule fois")
    logs.stop_file_logging()
    assert log_file.read_text(encoding="utf-8").count("une seule fois") == 1


def test_log_files_rotate(tmp_path: Path) -> None:
    """FR : au-delà de la taille maximale, de nouveaux fichiers sont créés, en
    nombre limité. EN : beyond the maximum size, new files are created,
    in a limited number.
    """
    logs.setup_logging(tmp_path, max_bytes=500, backup_count=2)
    for index in range(200):
        logging.getLogger("runecast.test").info("ligne numéro %s", index)
    logs.stop_file_logging()
    files = sorted(tmp_path.glob("runecast.log*"))
    assert len(files) == 3
