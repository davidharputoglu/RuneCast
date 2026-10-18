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

"""Journal de RuneCast (logs) / RuneCast log.

FR : RuneCast note ce qu'il fait dans un fichier texte (runecast.log) du
     dossier des journaux : démarrage, dossiers utilisés, erreurs… En cas de
     problème, c'est ce fichier qu'il faudra me transmettre.
     Pour ne jamais remplir le disque, le fichier est limité à 1 Mo : au-delà,
     il est renommé (runecast.log.1, .2…) et seuls les 5 derniers sont gardés.

EN : RuneCast writes what it does into a text file (runecast.log) inside the
     log folder: start-up, folders used, errors… If something goes wrong, this
     is the file to send. So that the disk never fills up, the file is limited
     to 1 MB: beyond that it is renamed (runecast.log.1, .2…) and only the last
     5 are kept.
"""

import logging
import platform
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from runecast import about
from runecast.core.paths import AppPaths

# FR : Nom du fichier journal. EN : Log file name.
LOG_FILE_NAME = "runecast.log"
# FR : Taille maximale d'un fichier (1 Mo). EN : Maximum size of one file (1 MB).
MAX_BYTES = 1_000_000
# FR : Nombre d'anciens fichiers gardés. EN : Number of old files kept.
BACKUP_COUNT = 5
# FR : Forme de chaque ligne : date, gravité, origine, message.
# EN : Shape of each line: date, severity, origin, message.
LINE_FORMAT = "%(asctime)s %(levelname)-8s %(name)s : %(message)s"

# FR : Tous les messages de RuneCast passent par ce journal principal.
# EN : Every RuneCast message goes through this main logger.
ROOT_LOGGER_NAME = "runecast"


def setup_logging(
    log_dir: Path,
    level: int = logging.INFO,
    max_bytes: int = MAX_BYTES,
    backup_count: int = BACKUP_COUNT,
) -> Path:
    """Met en place le journal / Set up the log.

    FR : Renvoie le chemin du fichier journal. Peut être appelée plusieurs
         fois sans dupliquer les lignes (utile pour les tests).
    EN : Returns the log file path. Can be called several times without
         duplicating lines (useful for tests).
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / LOG_FILE_NAME

    root = logging.getLogger(ROOT_LOGGER_NAME)
    root.setLevel(level)
    # FR : on retire les anciens réglages du journal avant d'en mettre de nouveaux.
    # EN : remove the previous log setup before adding a new one.
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(LINE_FORMAT))
    root.addHandler(file_handler)

    # FR : Les avertissements et erreurs s'affichent aussi dans le terminal.
    # EN : Warnings and errors are also shown in the terminal.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter(LINE_FORMAT))
    root.addHandler(console_handler)
    return log_file


def log_startup(paths: AppPaths) -> None:
    """FR : note la version, le système et les dossiers utilisés.

    EN : record the version, the system and the folders in use.
    """
    logger = logging.getLogger(ROOT_LOGGER_NAME)
    logger.info("Démarrage / Start: %s %s", about.APP_NAME, about.APP_VERSION)
    logger.info("Système / System: %s, Python %s", platform.platform(), sys.version.split()[0])
    logger.info("Mode : %s", paths.mode)
    for name, folder in paths.folders().items():
        logger.info("Dossier / Folder %s: %s", name, folder)
    if paths.unavailable_custom_root is not None:
        logger.warning(
            "Dossier choisi introuvable, emplacement normal utilisé / "
            "Chosen folder unavailable, normal location used: %s",
            paths.unavailable_custom_root,
        )


def stop_file_logging() -> None:
    """FR : arrête l'écriture dans le fichier journal (le terminal continue).

         Utilisé pendant le déplacement des données : le fichier journal doit
         être fermé pour être copié et vérifié sans changer en route.
    EN : stop writing to the log file (the terminal keeps going). Used while
         moving the data: the log file must be closed to be copied and verified
         without changing in between.
    """
    root = logging.getLogger(ROOT_LOGGER_NAME)
    for handler in list(root.handlers):
        if isinstance(handler, logging.FileHandler):
            root.removeHandler(handler)
            handler.close()


def log_uncaught_exceptions() -> None:
    """FR : toute erreur imprévue est notée dans le journal avant l'arrêt.

    EN : any unexpected error is written to the log before stopping.
    """
    previous_hook = sys.excepthook

    def hook(exc_type, exc_value, exc_traceback) -> None:
        logging.getLogger(ROOT_LOGGER_NAME).critical(
            "Erreur imprévue / Unexpected error", exc_info=(exc_type, exc_value, exc_traceback)
        )
        previous_hook(exc_type, exc_value, exc_traceback)

    sys.excepthook = hook
