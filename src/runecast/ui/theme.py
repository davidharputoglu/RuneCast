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

"""Thème Turquoise de base / Basic Turquoise theme.

FR : Version simple du thème par défaut de RuneCast, avec des couleurs prises
     dans le logo. Le vrai moteur de thèmes (Turquoise, Noir, Sombre, Clair et
     thèmes personnels enregistrables) arrivera aux étapes 8 et 9 et
     remplacera ce module.
     On utilise le style « Fusion » de Qt pour que RuneCast ait exactement le
     même aspect sous Windows et sous Linux.

EN : Simple version of the RuneCast default theme, with colours taken from
     the logo. The real theme engine (Turquoise, Black, Dark, Light and
     savable custom themes) will come in steps 8 and 9 and replace this module.
     Qt's "Fusion" style is used so that RuneCast looks exactly the same on
     Windows and on Linux.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

# FR : Couleurs du thème Turquoise (codes hexadécimaux).
# EN : Turquoise theme colours (hexadecimal codes).
TURQUOISE = {
    "window": "#102026",  # FR : fond des fenêtres / EN : window background
    "base": "#0B171B",  # FR : fond des champs et tableaux / EN : fields and tables
    "alternate_base": "#14272E",  # FR : lignes alternées / EN : alternate rows
    "surface": "#1B353C",  # FR : boutons, menus / EN : buttons, menus
    "text": "#E3F6F5",  # FR : texte principal / EN : main text
    "disabled_text": "#5E7A80",  # FR : texte désactivé / EN : disabled text
    "placeholder": "#7FA3A8",  # FR : texte d'exemple / EN : placeholder text
    "highlight": "#2A7F8A",  # FR : sélection / EN : selection
    "highlighted_text": "#FFFFFF",  # FR : texte sélectionné / EN : selected text
    "accent": "#3CCFC7",  # FR : turquoise vif / EN : bright turquoise
    "link": "#76E0DC",  # FR : liens / EN : links
    "border": "#2A4A52",  # FR : bordures / EN : borders
}


def build_palette(colors: dict[str, str]) -> QPalette:
    """Construit la palette Qt / Build the Qt palette.

    FR : Une palette indique à Qt quelle couleur utiliser pour chaque « rôle »
         (fond, texte, bouton, sélection…).
    EN : A palette tells Qt which colour to use for each "role" (background,
         text, button, selection…).
    """
    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: colors["window"],
        QPalette.ColorRole.WindowText: colors["text"],
        QPalette.ColorRole.Base: colors["base"],
        QPalette.ColorRole.AlternateBase: colors["alternate_base"],
        QPalette.ColorRole.Text: colors["text"],
        QPalette.ColorRole.Button: colors["surface"],
        QPalette.ColorRole.ButtonText: colors["text"],
        QPalette.ColorRole.ToolTipBase: colors["surface"],
        QPalette.ColorRole.ToolTipText: colors["text"],
        QPalette.ColorRole.PlaceholderText: colors["placeholder"],
        QPalette.ColorRole.Highlight: colors["highlight"],
        QPalette.ColorRole.HighlightedText: colors["highlighted_text"],
        QPalette.ColorRole.Link: colors["link"],
        QPalette.ColorRole.LinkVisited: colors["link"],
        QPalette.ColorRole.BrightText: colors["accent"],
    }
    for role, value in roles.items():
        palette.setColor(role, QColor(value))

    # FR : Les éléments désactivés sont grisés.
    # EN : Disabled elements are greyed out.
    for role in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(colors["disabled_text"]))
    return palette


def build_stylesheet(colors: dict[str, str]) -> str:
    """Construit la feuille de style / Build the style sheet.

    FR : Quelques finitions que la palette seule ne permet pas (bordures,
         arrondis, survol des menus et des boutons).
    EN : A few finishing touches the palette alone cannot do (borders, rounded
         corners, hover effect on menus and buttons).
    """
    return f"""
        QMenuBar {{ background: {colors["window"]}; }}
        QMenuBar::item:selected {{ background: {colors["highlight"]}; }}
        QMenu {{ background: {colors["surface"]}; border: 1px solid {colors["border"]}; }}
        QMenu::item:selected {{ background: {colors["highlight"]}; }}
        QPushButton {{
            background: {colors["surface"]};
            border: 1px solid {colors["border"]};
            border-radius: 4px;
            padding: 6px 16px;
        }}
        QPushButton:hover, QPushButton:default {{ border-color: {colors["accent"]}; }}
        QPushButton:pressed {{ background: {colors["highlight"]}; }}
    """


# FR : Nom du thème, mémorisé sur l'application (utile aux tests et, plus tard,
#      au moteur de thèmes).
# EN : Theme name, stored on the application (useful for tests and, later,
#      for the theme engine).
THEME_PROPERTY = "runecastTheme"


def apply_turquoise_theme(app: QApplication) -> None:
    """Applique le thème Turquoise à toute l'application / Apply it app-wide."""
    app.setStyle("Fusion")
    app.setPalette(build_palette(TURQUOISE))
    app.setStyleSheet(build_stylesheet(TURQUOISE))
    app.setProperty(THEME_PROPERTY, "turquoise")
    # FR : On signale au système que le thème est sombre : sous Windows, la
    #      barre de titre des fenêtres devient alors sombre elle aussi.
    # EN : Tell the system the theme is dark: on Windows, window title bars
    #      then become dark as well.
    app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
