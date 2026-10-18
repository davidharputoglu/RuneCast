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

"""Informations « À propos » de RuneCast / RuneCast "About" information.

FR : Ce module rassemble en un seul endroit les mentions obligatoires du cahier
     des charges (auteur, mention « aidé par l'IA », contact, licence). La
     fenêtre « À propos » (étape 4) et les pages légales (étape 34) viendront
     les lire ici : ainsi, elles ne sont jamais écrites deux fois et ne peuvent
     pas se contredire.

EN : This module gathers in one place the mandatory mentions required by the
     specification (author, "assisted by AI" mention, contact, license). The
     "About" window (step 4) and the legal pages (step 34) will read them from
     here, so they are never written twice and can never disagree.
"""

from runecast import __version__

# FR : Nom de l'application, tel qu'il s'affiche partout.
# EN : Application name, as displayed everywhere.
APP_NAME = "RuneCast"

# FR : Version de l'application (reprise de runecast/__init__.py).
# EN : Application version (taken from runecast/__init__.py).
APP_VERSION = __version__

# FR : Auteur du projet.
# EN : Project author.
AUTHOR = "HARPUTOGLU David"

# FR : Mention obligatoire du cahier des charges, en français et en anglais.
#      Les autres langues de l'interface seront ajoutées à l'étape 34.
# EN : Mandatory mention from the specification, in French and English.
#      The other interface languages will be added in step 34.
CREDIT_LINE_FR = "Créé par HARPUTOGLU David, aidé par l'IA"
CREDIT_LINE_EN = "Created by HARPUTOGLU David, assisted by AI"

# FR : Adresse de contact affichée dans l'application.
# EN : Contact address displayed in the application.
CONTACT_EMAIL = "kasparof57@gmail.com"

# FR : Licence, sous sa forme normalisée (identifiant SPDX) et en toutes lettres.
# EN : License, in its standard form (SPDX identifier) and spelled out.
LICENSE_SPDX = "GPL-3.0-or-later"
LICENSE_NAME = "GNU General Public License v3.0 or later"

# FR : Adresse du code source sur GitHub.
# EN : Address of the source code on GitHub.
REPOSITORY_URL = "https://github.com/davidharputoglu/RuneCast"

# FR : Adresse du texte officiel de la licence.
# EN : Address of the official license text.
LICENSE_URL = "https://www.gnu.org/licenses/gpl-3.0.html"

# FR : Identifiant unique de l'application pour Linux (nom du fichier .desktop,
#      reconnu par le dock de GNOME/KDE sous Wayland pour afficher l'icône).
# EN : Unique application identifier for Linux (.desktop file name, used by the
#      GNOME/KDE dock under Wayland to display the icon).
APP_ID = "io.github.davidharputoglu.RuneCast"

# FR : Identifiant pour la barre des tâches de Windows : sans lui, Windows
#      afficherait l'icône de Python au lieu de celle de RuneCast.
# EN : Identifier for the Windows taskbar: without it, Windows would show the
#      Python icon instead of the RuneCast one.
WINDOWS_APP_USER_MODEL_ID = "davidharputoglu.RuneCast"


def about_text() -> str:
    """Construit le texte « À propos » / Build the "About" text.

    FR : Renvoie un texte de plusieurs lignes avec le nom, la version, les
         mentions de création, le contact, la licence et l'adresse du code.
    EN : Returns a multi-line text with the name, version, credit lines,
         contact, license and source code address.
    """
    lines = [
        f"{APP_NAME} {APP_VERSION}",
        CREDIT_LINE_FR,
        CREDIT_LINE_EN,
        f"Contact : {CONTACT_EMAIL}",
        f"Licence / License : {LICENSE_NAME} ({LICENSE_SPDX})",
        f"Code source / Source code : {REPOSITORY_URL}",
    ]
    # FR : On assemble les lignes avec un retour à la ligne entre chacune.
    # EN : Lines are joined with a line break between each one.
    return "\n".join(lines)
