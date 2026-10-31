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

"""Rangement des clés des moteurs payants / Storage of paid engine keys.

FR : Les clés d'accès (DeepL, Google Cloud, Yandex…) sont des secrets : elles
     sont rangées dans le TROUSSEAU SÉCURISÉ du système, jamais dans le
     fichier des réglages :
       - Windows : Gestionnaire d'identification ;
       - Linux : GNOME Trousseau ou KWallet (service « Secret Service »).
     Deux exceptions, signalées à l'utilisateur :
       - en mode portable, les clés restent dans le dossier portable (le
         trousseau ne voyage pas sur une clé USB) ;
       - si le système n'a pas de trousseau (certains Linux minimalistes),
         elles sont gardées dans un fichier du dossier des réglages.

EN : Access keys (DeepL, Google Cloud, Yandex…) are secrets: they are stored
     in the system's SECURE KEYRING, never in the settings file (Windows:
     Credential Manager; Linux: GNOME Keyring or KWallet, "Secret Service").
     Two exceptions, shown to the user: in portable mode the keys stay in the
     portable folder (the keyring does not travel on a USB stick); if the
     system has no keyring (some minimal Linux), they are kept in a file of
     the settings folder.

     Ce module ne dépend pas de Qt. / This module does not depend on Qt.
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# FR : Nom du service dans le trousseau. EN : Service name in the keyring.
SERVICE = "RuneCast"
# FR : Fichier de repli. EN : Fallback file.
KEYS_FILE = "cles.json"


def _system_keyring():
    """FR : le trousseau du système, ou None s'il n'y en a pas d'utilisable.

    EN : the system keyring, or None when there is no usable one.
    """
    try:
        import keyring
        from keyring.backends import fail, null
    except ImportError:  # pragma: no cover (keyring est livré / keyring is shipped)
        return None
    backend = keyring.get_keyring()
    if isinstance(backend, fail.Keyring | null.Keyring):
        return None
    return keyring


class KeyStore:
    """Clés des moteurs / Engine keys."""

    def __init__(self, config_dir: Path, portable: bool = False) -> None:
        self.file = config_dir / KEYS_FILE
        self.keyring = None if portable else _system_keyring()
        self.portable = portable

    @property
    def secure(self) -> bool:
        """FR : les clés sont-elles dans le trousseau sécurisé ? EN : in the secure keyring?"""
        return self.keyring is not None

    def _read_file(self) -> dict[str, str]:
        try:
            data = json.loads(self.file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}

    def _write_file(self, keys: dict[str, str]) -> None:
        self.file.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.file.with_name(self.file.name + ".tmp")
        temporary.write_text(json.dumps(keys, indent=2), encoding="utf-8")
        if os.name != "nt":
            temporary.chmod(0o600)  # FR : lisible par toi seul / EN : readable by you only
        os.replace(temporary, self.file)

    def get(self, name: str) -> str:
        """FR : clé enregistrée (vide si aucune). EN : stored key (empty if none)."""
        if self.keyring is not None:
            try:
                return self.keyring.get_password(SERVICE, name) or ""
            except Exception as error:  # noqa: BLE001 (trousseau verrouillé, etc.)
                logger.warning("Trousseau illisible / Keyring unreadable: %s", error)
                return ""
        return self._read_file().get(name, "")

    def set(self, name: str, value: str) -> None:
        """FR : enregistre une clé ; une valeur vide l'efface. EN : store a key; empty erases."""
        value = value.strip()
        if self.keyring is not None:
            if value:
                self.keyring.set_password(SERVICE, name, value)
            elif self.keyring.get_password(SERVICE, name) is not None:
                self.keyring.delete_password(SERVICE, name)
            return
        keys = self._read_file()
        if value:
            keys[name] = value
        else:
            keys.pop(name, None)
        self._write_file(keys)
