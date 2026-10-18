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

"""Dossiers de données de RuneCast / RuneCast data folders.

FR : Décide où RuneCast range ses fichiers. Trois modes :

     1. Normal (par défaut) : la norme de chaque système (décision du
        18 octobre 2026).
          - réglages, thèmes, glossaires, profils :
              Windows %APPDATA%\\RuneCast — Linux ~/.config/runecast
          - gros fichiers (modèles, sauvegardes, historique) :
              Windows %LOCALAPPDATA%\\RuneCast — Linux ~/.local/share/runecast
          - cache (fichiers temporaires) :
              Windows %LOCALAPPDATA%\\RuneCast\\Cache — Linux ~/.cache/runecast
          - journaux (logs) :
              Windows %LOCALAPPDATA%\\RuneCast\\Logs — Linux ~/.local/state/runecast/log

     2. Personnalisé : l'utilisateur a choisi un dossier (ex. D:\\RuneCast) ;
        tout y est rangé, dans 4 sous-dossiers (config, data, cache, logs).
        Le chemin choisi est noté dans un petit fichier « emplacement.json »,
        rangé dans le dossier normal des réglages.

     3. Portable : tout est rangé dans un dossier à côté de l'application,
        pour l'emporter sur une clé USB.

EN : Decides where RuneCast stores its files. Three modes: normal (each
     system's standard, see list above), custom (a folder chosen by the user,
     e.g. D:\\RuneCast, recorded in a small "emplacement.json" file kept in the
     normal settings folder) and portable (a folder next to the application,
     to carry it on a USB stick).
"""

import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import platformdirs

logger = logging.getLogger(__name__)

# FR : Les trois modes possibles. EN : The three possible modes.
MODE_NORMAL = "normal"
MODE_CUSTOM = "custom"
MODE_PORTABLE = "portable"

# FR : Nom du dossier : « RuneCast » sous Windows, « runecast » sous Linux
#      (sous Linux, l'usage est d'écrire les noms de dossiers en minuscules).
# EN : Folder name: "RuneCast" on Windows, "runecast" on Linux (on Linux,
#      folder names are usually lower case).
WINDOWS_FOLDER_NAME = "RuneCast"
LINUX_FOLDER_NAME = "runecast"

# FR : Si ce fichier existe à côté de l'application, RuneCast passe en mode
#      portable. La version portable (étape 37) sera livrée avec ce fichier.
# EN : If this file exists next to the application, RuneCast switches to
#      portable mode. The portable version (step 37) will ship with this file.
PORTABLE_MARKER = "portable.txt"

# FR : Nom du dossier de données en mode portable.
# EN : Name of the data folder in portable mode.
PORTABLE_DATA_FOLDER = "data"

# FR : Dossier utilisé par l'option « --portable » quand on lance RuneCast
#      depuis le code source (ignoré par Git).
# EN : Folder used by the "--portable" option when RuneCast runs from the
#      source code (ignored by Git).
DEV_PORTABLE_FOLDER = "portable-data"

# FR : Fichier qui mémorise le dossier choisi par l'utilisateur.
# EN : File that remembers the folder chosen by the user.
LOCATION_FILE_NAME = "emplacement.json"

# FR : Nom du fichier des réglages. EN : Settings file name.
SETTINGS_FILE_NAME = "settings.json"


@dataclass(frozen=True)
class AppPaths:
    """Les dossiers utilisés par RuneCast / The folders used by RuneCast."""

    mode: str  # MODE_NORMAL, MODE_CUSTOM ou/or MODE_PORTABLE
    config_dir: Path  # FR : réglages, thèmes, glossaires / EN : settings, themes, glossaries
    data_dir: Path  # FR : modèles, sauvegardes, historique / EN : models, backups, history
    cache_dir: Path  # FR : fichiers temporaires / EN : temporary files
    log_dir: Path  # FR : journaux / EN : logs
    # FR : dossier choisi par l'utilisateur mais introuvable au démarrage (ex. disque
    #      débranché) : RuneCast utilise alors l'emplacement normal et prévient.
    # EN : folder chosen by the user but missing at start-up (e.g. unplugged drive):
    #      RuneCast then uses the normal location and warns the user.
    unavailable_custom_root: Path | None = None

    @property
    def portable(self) -> bool:
        """FR : vrai en mode portable. EN : true in portable mode."""
        return self.mode == MODE_PORTABLE

    @property
    def root(self) -> Path | None:
        """FR : dossier unique (modes personnalisé et portable), sinon None.

        EN : single folder (custom and portable modes), otherwise None.
        """
        if self.mode == MODE_NORMAL:
            return None
        return self.config_dir.parent

    @property
    def settings_file(self) -> Path:
        """FR : chemin du fichier des réglages. EN : settings file path."""
        return self.config_dir / SETTINGS_FILE_NAME

    def folders(self) -> dict[str, Path]:
        """FR : les 4 dossiers, avec un nom court. EN : the 4 folders, with a short name."""
        return {
            "config": self.config_dir,
            "data": self.data_dir,
            "cache": self.cache_dir,
            "logs": self.log_dir,
        }

    def create(self) -> None:
        """FR : crée les dossiers s'ils n'existent pas. EN : create missing folders."""
        for folder in self.folders().values():
            folder.mkdir(parents=True, exist_ok=True)


def application_folder() -> Path:
    """Dossier qui contient l'application / Folder containing the application.

    FR : Pour une version installée ou portable (fabriquée à partir de
         l'étape 35), c'est le dossier du fichier RuneCast.exe. Quand on lance
         RuneCast depuis le code source, c'est le dossier principal du projet.
    EN : For an installed or portable build (made from step 35 on), it is the
         folder of the RuneCast.exe file. When RuneCast runs from the source
         code, it is the project's main folder.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # FR : ce fichier est dans src/runecast/core/ : on remonte de 3 dossiers.
    # EN : this file lives in src/runecast/core/: go up 3 folders.
    return Path(__file__).resolve().parents[3]


def single_folder_paths(root: Path, mode: str) -> AppPaths:
    """FR : les 4 dossiers rangés dans un seul dossier (personnalisé ou portable).

    EN : the 4 folders stored inside a single folder (custom or portable).
    """
    return AppPaths(
        mode=mode,
        config_dir=root / "config",
        data_dir=root / "data",
        cache_dir=root / "cache",
        log_dir=root / "logs",
    )


def system_paths() -> AppPaths:
    """FR : dossiers standard du système (mode normal).

    EN : the system's standard folders (normal mode).
    """
    if sys.platform == "win32":
        name = WINDOWS_FOLDER_NAME
        return AppPaths(
            mode=MODE_NORMAL,
            # FR : AppData\Roaming : petits fichiers qui suivent l'utilisateur.
            # EN : AppData\Roaming: small files that follow the user.
            config_dir=Path(platformdirs.user_config_dir(name, appauthor=False, roaming=True)),
            # FR : AppData\Local : gros fichiers, propres à ce PC.
            # EN : AppData\Local: large files, specific to this PC.
            data_dir=Path(platformdirs.user_data_dir(name, appauthor=False, roaming=False)),
            cache_dir=Path(platformdirs.user_cache_dir(name, appauthor=False)),
            log_dir=Path(platformdirs.user_log_dir(name, appauthor=False)),
        )
    name = LINUX_FOLDER_NAME
    return AppPaths(
        mode=MODE_NORMAL,
        config_dir=Path(platformdirs.user_config_dir(name, appauthor=False)),
        data_dir=Path(platformdirs.user_data_dir(name, appauthor=False)),
        cache_dir=Path(platformdirs.user_cache_dir(name, appauthor=False)),
        log_dir=Path(platformdirs.user_log_dir(name, appauthor=False)),
    )


def portable_root(app_folder: Path) -> Path | None:
    """Dossier portable, ou None / Portable folder, or None.

    FR : Renvoie le dossier de données portable si le fichier « portable.txt »
         se trouve à côté de l'application, sinon None.
    EN : Returns the portable data folder if the "portable.txt" file sits next
         to the application, otherwise None.
    """
    if (app_folder / PORTABLE_MARKER).is_file():
        return app_folder / PORTABLE_DATA_FOLDER
    return None


def location_file() -> Path:
    """FR : fichier qui mémorise le dossier choisi (dans le dossier normal des réglages).

    EN : file remembering the chosen folder (in the normal settings folder).
    """
    return system_paths().config_dir / LOCATION_FILE_NAME


def read_custom_root() -> Path | None:
    """FR : dossier choisi par l'utilisateur, ou None s'il n'en a pas choisi.

    EN : folder chosen by the user, or None if none was chosen.
    """
    path = location_file()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Path(data["data_folder"])
    except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError) as error:
        logger.error("Fichier d'emplacement illisible / Unreadable location file: %s", error)
        return None


def write_custom_root(root: Path | None) -> None:
    """Mémorise le dossier choisi / Remember the chosen folder.

    FR : root=None : retour à l'emplacement normal (le fichier est retiré).
    EN : root=None: back to the normal location (the file is removed).
    """
    path = location_file()
    if root is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    content = json.dumps({"data_folder": str(root)}, indent=2, ensure_ascii=False) + "\n"
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def resolve_paths(force_portable: bool = False) -> AppPaths:
    """Choisit les dossiers à utiliser / Choose which folders to use.

    FR : Dans l'ordre :
         1. option « --portable » : dossier « portable-data » à côté de l'application ;
         2. fichier « portable.txt » à côté de l'application : mode portable ;
         3. dossier choisi par l'utilisateur : mode personnalisé ;
         4. sinon : dossiers standard du système (mode normal).
    EN : In this order: 1. "--portable" option; 2. "portable.txt" file next to
         the application; 3. folder chosen by the user; 4. otherwise the system's
         standard folders.
    """
    app_folder = application_folder()
    if force_portable:
        return single_folder_paths(app_folder / DEV_PORTABLE_FOLDER, MODE_PORTABLE)
    root = portable_root(app_folder)
    if root is not None:
        return single_folder_paths(root, MODE_PORTABLE)

    custom_root = read_custom_root()
    if custom_root is not None:
        try:
            custom_root.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            logger.warning(
                "Dossier choisi introuvable / Chosen folder unavailable: %s (%s)",
                custom_root,
                error,
            )
            normal = system_paths()
            return AppPaths(
                mode=normal.mode,
                config_dir=normal.config_dir,
                data_dir=normal.data_dir,
                cache_dir=normal.cache_dir,
                log_dir=normal.log_dir,
                unavailable_custom_root=custom_root,
            )
        return single_folder_paths(custom_root, MODE_CUSTOM)
    return system_paths()
