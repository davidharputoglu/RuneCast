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

"""RuneCast : traduction de jeux vidéo / video game translation.

FR : Paquet principal de RuneCast. Pour l'instant, il ne contient que le
     numéro de version et les informations « À propos ». Les autres parties
     (cœur, moteurs de traduction, formats de jeux, interface) seront ajoutées
     étape par étape, comme prévu dans docs/PLAN-V1.md.

EN : RuneCast main package. For now it only holds the version number and the
     "About" information. The other parts (core, translation engines, game
     formats, user interface) will be added step by step, as planned in
     docs/PLAN-V1.md.
"""

# FR : Numéro de version unique du projet. Il est aussi lu par pyproject.toml,
#      pour n'être écrit qu'à un seul endroit. Règle de numérotation (voir
#      CHANGELOG.md) : chaque étape validée ou correctif augmente le dernier
#      chiffre (0.1.0 → 0.1.1), chaque fin de jalon le chiffre du milieu
#      (0.2.0), et 1.0.0 sera la première version complète publiée.
# EN : Single source of truth for the project version. pyproject.toml reads it
#      from here so it is written in one place only. Numbering rule (see
#      CHANGELOG.md): each validated step or fix bumps the last number
#      (0.1.0 → 0.1.1), each completed milestone the middle number (0.2.0),
#      and 1.0.0 will be the first complete public release.
__version__ = "0.1.0"
