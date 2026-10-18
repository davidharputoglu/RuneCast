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

"""Tests des informations « À propos » / Tests for the "About" information.

FR : Ces tests vérifient automatiquement que les mentions obligatoires du
     cahier des charges sont présentes et exactes. Si quelqu'un les modifie
     par erreur, les tests échouent.
EN : These tests automatically check that the mandatory mentions from the
     specification are present and exact. If someone changes them by mistake,
     the tests fail.
"""

import re

from runecast import __main__ as cli
from runecast import about


def test_credit_line_is_exact() -> None:
    """FR : la mention exigée est écrite mot pour mot. EN : exact wording."""
    assert about.CREDIT_LINE_FR == "Créé par HARPUTOGLU David, aidé par l'IA"


def test_contact_email_is_exact() -> None:
    """FR : l'adresse de contact est la bonne. EN : correct contact address."""
    assert about.CONTACT_EMAIL == "kasparof57@gmail.com"


def test_license_is_gpl3_or_later() -> None:
    """FR : la licence est GPLv3 ou ultérieure. EN : license is GPLv3 or later."""
    assert about.LICENSE_SPDX == "GPL-3.0-or-later"


def test_version_looks_valid() -> None:
    """FR : la version a la forme 0.1.0 ou 0.1.0.dev0. EN : version format."""
    assert re.fullmatch(r"\d+\.\d+\.\d+(\.dev\d+)?", about.APP_VERSION)


def test_about_text_contains_every_mention() -> None:
    """FR : le texte « À propos » contient tout. EN : About text has everything."""
    text = about.about_text()
    for expected in (
        about.APP_NAME,
        about.APP_VERSION,
        about.CREDIT_LINE_FR,
        about.CREDIT_LINE_EN,
        about.CONTACT_EMAIL,
        about.LICENSE_SPDX,
        about.REPOSITORY_URL,
    ):
        assert expected in text


def test_command_line_version(capsys) -> None:
    """FR : « runecast --version » affiche les crédits et réussit.

    EN : "runecast --version" prints the credits and succeeds.
    """
    exit_code = cli.main(["--version"])
    printed = capsys.readouterr().out
    assert exit_code == 0
    assert about.CREDIT_LINE_FR in printed
    assert about.CONTACT_EMAIL in printed
