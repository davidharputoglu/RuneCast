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

"""Modèle commun des pages de Paramètres / Common model of the Settings pages.

FR : Chaque page de la fenêtre « Paramètres » suit ce modèle. Il est rangé
     à part pour que chaque grande page puisse avoir son propre fichier.
EN : Every page of the "Settings" window follows this model. It is kept
     apart so that each large page can have its own file.
"""

from PySide6.QtWidgets import QWidget

from runecast.core.settings import Settings


class SettingsPage(QWidget):
    """Modèle commun des pages / Common model of the pages.

    FR : Une page a un titre, lit les réglages (load) et y écrit ses valeurs
         (store). Ses textes sont (re)posés par retranslate(). shutdown() est
         appelé à la fermeture de la fenêtre (pour arrêter un travail en cours).
    EN : A page has a title, reads the settings (load) and writes its values
         into them (store). Its texts are (re)set by retranslate(). shutdown()
         is called when the window closes (to stop a running job).
    """

    def title(self) -> str:
        raise NotImplementedError

    def load(self, settings: Settings) -> None:
        raise NotImplementedError

    def store(self, settings: Settings) -> None:
        raise NotImplementedError

    def retranslate(self) -> None:
        """FR : textes de la page. EN : texts of the page."""

    def shutdown(self) -> None:
        """FR : fermeture de la fenêtre. EN : the window is closing."""
