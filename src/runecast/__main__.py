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

"""Point d'entrée en ligne de commande / Command-line entry point.

FR : Permet de lancer RuneCast depuis un terminal, avec « runecast » ou
     « python -m runecast ». Pour l'instant, seule l'option --version existe ;
     la fenêtre de l'application arrivera à l'étape 4.

EN : Lets you start RuneCast from a terminal, with "runecast" or
     "python -m runecast". For now only the --version option exists; the
     application window will come in step 4.
"""

import argparse
import sys

from runecast import about


def build_parser() -> argparse.ArgumentParser:
    """Décrit les options acceptées / Describe the accepted options."""
    parser = argparse.ArgumentParser(
        prog="runecast",
        description=("RuneCast : traduction de jeux vidéo / video game translation"),
    )
    # FR : --version affiche la version et les mentions « À propos ».
    # EN : --version prints the version and the "About" mentions.
    parser.add_argument(
        "--version",
        action="store_true",
        help="affiche la version et les crédits / show version and credits",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Lance RuneCast / Start RuneCast.

    FR : Renvoie 0 si tout s'est bien passé (convention des programmes).
    EN : Returns 0 when everything went fine (standard program convention).
    """
    args = build_parser().parse_args(argv)

    # FR : Dans tous les cas, on affiche les informations « À propos ».
    # EN : In every case, the "About" information is printed.
    print(about.about_text())

    if not args.version:
        # FR : Sans option, on prévient que l'interface n'existe pas encore.
        # EN : Without an option, we explain that the interface does not exist yet.
        print()
        print("L'interface graphique arrivera à l'étape 4.")
        print("The graphical interface will come in step 4.")
    return 0


# FR : Ce bloc s'exécute seulement quand on lance « python -m runecast ».
# EN : This block only runs when "python -m runecast" is used.
if __name__ == "__main__":
    sys.exit(main())
