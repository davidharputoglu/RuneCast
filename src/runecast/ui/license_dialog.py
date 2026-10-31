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

"""Fenêtre d'acceptation de la licence NLLB / NLLB license acceptance window.

FR : Avant de télécharger le modèle NLLB-200, l'utilisateur doit lire et
     accepter sa licence (CC-BY-NC 4.0, usage non commercial). Le bouton
     « Accepter et télécharger » reste grisé tant que la case n'est pas cochée.
EN : Before downloading the NLLB-200 model, the user must read and accept its
     license (CC-BY-NC 4.0, non-commercial use). The "Accept and download"
     button stays greyed out until the box is checked.
"""

from html import escape

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from runecast.engines.nllb import NllbCatalog
from runecast.ui.i18n import format_size


class NllbLicenseDialog(QDialog):
    """Acceptation de la licence NLLB-200 / NLLB-200 license acceptance."""

    def __init__(self, catalog: NllbCatalog, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("nllbLicenseDialog")
        self.setWindowTitle(self.tr("Licence du modèle NLLB-200"))
        title = self.tr("Modèle étendu NLLB-200 (Meta)")
        summary = self.tr(
            "Ce modèle traduit sans internet entre 200 langues, dont le kazakh, "
            "l'ouzbek, le turkmène, le tatar et l'ouïghour. Taille : {size}."
        ).format(size=format_size(catalog.total_size))
        terms = self.tr(
            "Il est publié par Meta sous la licence Creative Commons BY-NC 4.0 : "
            "utilisation NON COMMERCIALE seulement (pas de traduction vendue ou faite "
            "pour une entreprise), en citant Meta. Meta le présente comme un modèle "
            "de recherche : ses traductions peuvent contenir des erreurs."
        )
        link_text = self.tr("Lire la licence complète")
        text = QLabel(
            f"<h3>{escape(title)}</h3><p>{escape(summary)}</p><p>{escape(terms)}</p>"
            f'<p><a href="{escape(catalog.license_url)}">{escape(link_text)}</a> · '
            f'<a href="{escape(catalog.source)}">{escape(catalog.source)}</a></p>'
        )
        text.setWordWrap(True)
        text.setOpenExternalLinks(True)
        self.accept_check = QCheckBox(
            self.tr(
                "J'ai lu la licence et je m'engage à n'utiliser ce modèle que sans but commercial"
            )
        )
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.ok_button = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setText(self.tr("Accepter et télécharger"))
        self.ok_button.setEnabled(False)
        self.accept_check.toggled.connect(self.ok_button.setEnabled)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(text)
        layout.addWidget(self.accept_check)
        layout.addWidget(self.buttons)
        self.setMinimumWidth(560)
