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

"""Fenêtre « À propos de RuneCast » / "About RuneCast" window.

FR : Affiche le logo, la version, les mentions obligatoires du cahier des
     charges (« Créé par HARPUTOGLU David, aidé par l'IA », contact), la
     licence GPLv3 et l'adresse du code source. Tous ces textes viennent de
     runecast/about.py : ils ne sont écrits qu'à un seul endroit.

EN : Shows the logo, the version, the mandatory mentions from the
     specification ("Created by HARPUTOGLU David, assisted by AI", contact),
     the GPLv3 license and the source code address. All these texts come from
     runecast/about.py: they are written in one place only.
"""

from html import escape

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from runecast import about
from runecast.ui.icons import app_icon

# FR : Taille d'affichage du logo dans la fenêtre (en pixels logiques).
# EN : Display size of the logo in the window (in logical pixels).
LOGO_SIZE = 128


def _link(url: str, text: str | None = None) -> str:
    """FR : fabrique un lien cliquable. EN : build a clickable link."""
    return f'<a href="{escape(url)}">{escape(text or url)}</a>'


class AboutDialog(QDialog):
    """Fenêtre « À propos » / "About" window."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("aboutDialog")
        self.setWindowTitle(self.tr("À propos de RuneCast"))
        self.setWindowIcon(app_icon())

        # FR : Le logo, à gauche. EN : The logo, on the left.
        logo = QLabel()
        logo.setObjectName("aboutLogo")
        logo.setPixmap(app_icon().pixmap(LOGO_SIZE, LOGO_SIZE))
        logo.setAlignment(Qt.AlignmentFlag.AlignTop)

        # FR : Le texte, à droite. Chaque ligne est une étiquette séparée, ce qui
        #      facilitera la traduction de l'interface (étape 7).
        # EN : The text, on the right. Each line is a separate label, which will
        #      make translating the interface easier (step 7).
        texts = [
            f"<h2>{escape(about.APP_NAME)}</h2>",
            escape(self.tr("Version {version}").format(version=about.APP_VERSION)),
            f"<b>{escape(about.CREDIT_LINE_FR)}</b>",
            f"<i>{escape(about.CREDIT_LINE_EN)}</i>",
            escape(self.tr("Contact :"))
            + " "
            + _link(f"mailto:{about.CONTACT_EMAIL}", about.CONTACT_EMAIL),
            escape(self.tr("Licence :"))
            + " "
            + _link(about.LICENSE_URL, about.LICENSE_NAME)
            + f" ({escape(about.LICENSE_SPDX)})",
            escape(self.tr("Code source :")) + " " + _link(about.REPOSITORY_URL),
            "<small>"
            + escape(
                self.tr(
                    "Ce programme est un logiciel libre, fourni SANS AUCUNE GARANTIE. "
                    "Vous pouvez le redistribuer selon les termes de la licence."
                )
            )
            + "</small>",
        ]
        self.text_labels: list[QLabel] = []
        text_layout = QVBoxLayout()
        for text in texts:
            label = QLabel(text)
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setWordWrap(True)
            # FR : Les liens s'ouvrent dans le navigateur ou la messagerie.
            # EN : Links open in the web browser or the e-mail program.
            label.setOpenExternalLinks(True)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
            text_layout.addWidget(label)
            self.text_labels.append(label)
        text_layout.addStretch()

        content = QHBoxLayout()
        content.addWidget(logo)
        content.addSpacing(16)
        content.addLayout(text_layout, stretch=1)

        # FR : Le bouton « Fermer ». EN : The "Close" button.
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText(self.tr("Fermer"))
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(content)
        layout.addWidget(buttons)
        self.setMinimumWidth(560)

    def plain_text(self) -> str:
        """FR : tout le texte affiché, sans mise en forme (utile aux tests).

        EN : all the displayed text, without formatting (useful for tests).
        """
        document = QTextDocument()
        parts = []
        for label in self.text_labels:
            document.setHtml(label.text())
            parts.append(document.toPlainText())
        return "\n".join(parts)
