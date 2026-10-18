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

"""Ressources embarquées dans RuneCast / Resources shipped inside RuneCast.

FR : Ce dossier contient les fichiers dont l'application a besoin pour
     fonctionner (icônes, plus tard polices et traductions). Ils font partie
     du paquet RuneCast : on les retrouve donc aussi bien quand on lance
     RuneCast depuis le code source que depuis une version installée.
     Les icônes de ce dossier sont fabriquées par tools/make_icons.py.

EN : This folder holds the files the application needs to run (icons, later
     fonts and translations). They are part of the RuneCast package, so they
     are found both when RuneCast runs from the source code and from an
     installed version. The icons in this folder are built by
     tools/make_icons.py.
"""

from importlib.resources import files
from pathlib import Path


def resource_path(*parts: str) -> Path:
    """Chemin d'une ressource / Path of a resource.

    FR : Exemple : resource_path("icons", "runecast-256.png").
    EN : Example: resource_path("icons", "runecast-256.png").
    """
    return Path(str(files(__name__).joinpath(*parts)))
