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

"""Réglages de RuneCast / RuneCast settings.

FR : Les réglages sont enregistrés dans un fichier texte lisible
     (settings.json) du dossier des réglages. Trois protections :
       - numéro de version du format (« schema_version ») : quand une future
         version de RuneCast changera le format, elle saura convertir
         l'ancien fichier sans rien perdre (« migrations ») ;
       - écriture « atomique » : le fichier est d'abord écrit à côté, puis
         remplace l'ancien d'un coup ; une coupure de courant ne peut donc pas
         laisser un fichier à moitié écrit ;
       - copie de sécurité : l'ancien fichier est gardé en settings.json.bak,
         et un fichier abîmé est mis de côté (jamais effacé) avant de repartir
         des réglages par défaut.

EN : Settings are stored in a readable text file (settings.json) inside the
     settings folder. Three safeguards:
       - format version number ("schema_version"): when a future RuneCast
         version changes the format, it will convert the old file without
         losing anything ("migrations");
       - "atomic" writing: the file is first written next to the old one, then
         replaces it in one go, so a power cut cannot leave a half-written file;
       - safety copy: the previous file is kept as settings.json.bak, and a
         damaged file is set aside (never deleted) before falling back to the
         default settings.
"""

import json
import logging
import os
import shutil
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# FR : Version actuelle du format du fichier de réglages.
# EN : Current version of the settings file format.
SCHEMA_VERSION = 1

# FR : Conversions d'un ancien format vers le suivant : {ancienne version: fonction}.
#      Vide pour l'instant, puisque c'est le premier format.
# EN : Conversions from an old format to the next one: {old version: function}.
#      Empty for now, since this is the first format.
MIGRATIONS: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {}


@dataclass
class Settings:
    """Les réglages de RuneCast / RuneCast settings.

    FR : Chaque réglage a une valeur par défaut, utilisée au premier lancement.
         Les autres réglages (moteurs de traduction, etc.) seront ajoutés
         avec leurs fonctions.
    EN : Every setting has a default value, used on first launch. Other
         settings (translation engines, etc.) will be added together with
         their features.
    """

    schema_version: int = SCHEMA_VERSION
    # FR : langue de l'interface (étape 7). EN : interface language (step 7).
    interface_language: str = "fr"
    # FR : thème choisi (étape 8). EN : chosen theme (step 8).
    theme: str = "turquoise"
    # FR : taille et position de la fenêtre principale, mémorisées à la fermeture.
    # EN : size and position of the main window, remembered when it closes.
    window_geometry: str = ""
    # FR : réglages inconnus (écrits par une version plus récente) : conservés tels quels.
    # EN : unknown settings (written by a newer version): kept as they are.
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Settings":
        """FR : construit les réglages depuis le contenu du fichier.

        EN : build the settings from the file content.
        """
        known = {f.name for f in fields(cls) if f.name != "extra"}
        values = {key: value for key, value in data.items() if key in known}
        extra = {key: value for key, value in data.items() if key not in known}
        settings = cls(**values)
        settings.extra = extra
        return settings

    def to_dict(self) -> dict[str, Any]:
        """FR : contenu à écrire dans le fichier. EN : content to write to the file."""
        data = asdict(self)
        extra = data.pop("extra")
        data.update(extra)
        return data


def _timestamp() -> str:
    """FR : date et heure pour nommer les copies. EN : date and time for copy names."""
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def migrate(data: dict[str, Any]) -> dict[str, Any]:
    """Convertit un ancien format / Convert an old format.

    FR : Applique les conversions une par une jusqu'au format actuel.
    EN : Applies the conversions one by one up to the current format.
    """
    version = int(data.get("schema_version", 1))
    if version > SCHEMA_VERSION:
        logger.warning(
            "Réglages écrits par une version plus récente de RuneCast (format %s) / "
            "Settings written by a newer RuneCast version (format %s)",
            version,
            version,
        )
        return data
    while version < SCHEMA_VERSION:
        data = MIGRATIONS[version](data)
        version += 1
        data["schema_version"] = version
    return data


def load_settings(path: Path) -> Settings:
    """Lit les réglages / Read the settings.

    FR : Fichier absent : réglages par défaut. Fichier abîmé : il est renommé
         (settings.json.abime-DATE) pour ne rien perdre, puis on repart des
         réglages par défaut.
    EN : Missing file: default settings. Damaged file: it is renamed
         (settings.json.abime-DATE) so nothing is lost, then default settings
         are used.
    """
    if not path.exists():
        logger.info("Premier lancement : réglages par défaut / First launch: default settings")
        return Settings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("le fichier ne contient pas un objet JSON / not a JSON object")
    except (OSError, UnicodeDecodeError, ValueError) as error:
        damaged = path.with_name(f"{path.name}.abime-{_timestamp()}")
        shutil.copy2(path, damaged)
        logger.error(
            "Réglages illisibles, copie mise de côté / Unreadable settings, copy kept: %s (%s)",
            damaged,
            error,
        )
        return Settings()
    return Settings.from_dict(migrate(data))


def save_settings(settings: Settings, path: Path) -> None:
    """Enregistre les réglages sans risque / Save the settings safely."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(settings.to_dict(), indent=2, ensure_ascii=False) + "\n"

    # FR : 1. On écrit d'abord dans un fichier temporaire, à côté.
    # EN : 1. First write into a temporary file, next to the real one.
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(content, encoding="utf-8")

    # FR : 2. On garde une copie de l'ancien fichier.
    # EN : 2. Keep a copy of the previous file.
    if path.exists():
        shutil.copy2(path, path.with_name(path.name + ".bak"))

    # FR : 3. Le nouveau fichier remplace l'ancien d'un seul coup.
    # EN : 3. The new file replaces the old one in one go.
    os.replace(temporary, path)
