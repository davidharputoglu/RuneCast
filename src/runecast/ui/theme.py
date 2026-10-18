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

"""Application d'un thème à l'écran / Applying a theme on screen.

FR : Transforme un thème (runecast/core/themes.py) en palette Qt et en
     feuille de style, puis l'applique à toute l'application. On utilise le
     style « Fusion » de Qt pour que RuneCast ait exactement le même aspect
     sous Windows et sous Linux. Il est complété par RuneCastStyle, qui
     dessine les cases à cocher et les boutons ronds avec les couleurs du
     thème (avec Fusion seul, leur contour disparaît sur un fond noir).

EN : Turns a theme (runecast/core/themes.py) into a Qt palette and style
     sheet, then applies it to the whole application. Qt's "Fusion" style is
     used so that RuneCast looks exactly the same on Windows and on Linux. It
     is completed by RuneCastStyle, which draws check boxes and radio buttons
     with the theme colours (with Fusion alone, their outline disappears on a
     black background).
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPalette, QPen
from PySide6.QtWidgets import (
    QApplication,
    QProxyStyle,
    QStyle,
    QStyleFactory,
    QStyleOption,
    QWidget,
)

from runecast.core.themes import Theme

# FR : Nom du thème actif, mémorisé sur l'application (utile aux tests).
# EN : Active theme name, stored on the application (useful for tests).
THEME_PROPERTY = "runecastTheme"


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
        QPalette.ColorRole.Accent: colors["accent"],
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
        QMenuBar::item:selected {{ background: {colors["highlight"]};
            color: {colors["highlighted_text"]}; }}
        QMenu {{ background: {colors["surface"]}; border: 1px solid {colors["border"]}; }}
        QMenu::item:selected {{ background: {colors["highlight"]};
            color: {colors["highlighted_text"]}; }}
        QPushButton {{
            background: {colors["surface"]};
            border: 1px solid {colors["border"]};
            border-radius: 4px;
            padding: 6px 16px;
        }}
        QPushButton:hover, QPushButton:default {{ border-color: {colors["accent"]}; }}
        QPushButton:pressed {{ background: {colors["highlight"]};
            color: {colors["highlighted_text"]}; }}
    """


class RuneCastStyle(QProxyStyle):
    """Style Fusion + cases à cocher lisibles / Fusion style + readable check boxes.

    FR : Tout est dessiné par Fusion, sauf les cases à cocher et les boutons
         ronds : leur contour prend la couleur vive du thème, et une case
         cochée est remplie avec la couleur de sélection.
    EN : Everything is drawn by Fusion, except check boxes and radio buttons:
         their outline takes the theme's accent colour, and a checked box is
         filled with the selection colour.
    """

    def __init__(self) -> None:
        super().__init__(QStyleFactory.create("Fusion"))

    def drawPrimitive(  # noqa: N802 (nom imposé par Qt / name required by Qt)
        self,
        element: QStyle.PrimitiveElement,
        option: QStyleOption,
        painter: QPainter,
        widget: QWidget | None = None,
    ) -> None:
        if element == QStyle.PrimitiveElement.PE_IndicatorCheckBox:
            self._draw_indicator(option, painter, round_shape=False)
        elif element == QStyle.PrimitiveElement.PE_IndicatorRadioButton:
            self._draw_indicator(option, painter, round_shape=True)
        else:
            super().drawPrimitive(element, option, painter, widget)

    @staticmethod
    def _draw_indicator(option: QStyleOption, painter: QPainter, round_shape: bool) -> None:
        """FR : dessine une case (carrée ou ronde). EN : draw a box (square or round)."""
        palette = option.palette
        state = option.state
        enabled = bool(state & QStyle.StateFlag.State_Enabled)
        checked = bool(state & QStyle.StateFlag.State_On)
        partly = bool(state & QStyle.StateFlag.State_NoChange)  # FR : 3e état / EN : 3rd state
        disabled_color = palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text)
        outline = palette.color(QPalette.ColorRole.Accent) if enabled else disabled_color
        filled = enabled and (checked or partly)
        fill = palette.color(QPalette.ColorRole.Highlight if filled else QPalette.ColorRole.Base)
        mark = palette.color(QPalette.ColorRole.HighlightedText) if enabled else disabled_color
        hovered = enabled and bool(state & QStyle.StateFlag.State_MouseOver)

        rect = QRectF(option.rect).adjusted(1.5, 1.5, -1.5, -1.5)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(outline, 2.0 if hovered else 1.2))
        painter.setBrush(fill)
        if round_shape:
            painter.drawEllipse(rect)
        else:
            painter.drawRoundedRect(rect, 3, 3)

        painter.setPen(
            QPen(
                mark,
                max(1.6, rect.width() / 7),
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        painter.setBrush(Qt.BrushStyle.NoBrush)
        w, h, x, y = rect.width(), rect.height(), rect.x(), rect.y()
        if round_shape and checked:
            # FR : point central / EN : centre dot
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(mark)
            painter.drawEllipse(rect.center(), w / 4, h / 4)
        elif checked:
            # FR : coche « ✓ » / EN : "✓" tick
            tick = QPainterPath(QPointF(x + w * 0.24, y + h * 0.52))
            tick.lineTo(QPointF(x + w * 0.43, y + h * 0.71))
            tick.lineTo(QPointF(x + w * 0.77, y + h * 0.30))
            painter.drawPath(tick)
        elif partly:
            # FR : trait « – » (case à moitié cochée) / EN : "–" dash (partly checked)
            painter.drawLine(QPointF(x + w * 0.27, y + h / 2), QPointF(x + w * 0.73, y + h / 2))
        painter.restore()


def apply_theme(app: QApplication, theme: Theme) -> None:
    """Applique un thème à toute l'application / Apply a theme app-wide."""
    app.setStyle(RuneCastStyle())
    app.setPalette(build_palette(theme.colors))
    app.setStyleSheet(build_stylesheet(theme.colors))
    app.setProperty(THEME_PROPERTY, theme.id)
    # FR : On indique au système si le thème est sombre ou clair : sous Windows,
    #      la barre de titre des fenêtres suit alors le thème.
    # EN : Tell the system whether the theme is dark or light: on Windows, the
    #      window title bars then follow the theme.
    scheme = Qt.ColorScheme.Dark if theme.dark else Qt.ColorScheme.Light
    app.styleHints().setColorScheme(scheme)
