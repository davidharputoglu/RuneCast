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

"""Éditeur de thèmes personnels / Custom theme editor.

FR : Fenêtre « Gérer les thèmes » (menu Affichage → Thème). Elle permet de :
       - partir d'un thème (intégré ou personnel) et le DUPLIQUER pour créer
         son propre thème ;
       - changer chaque couleur (sélecteur de couleurs ou code #RRGGBB), le
         nom, et le caractère sombre ou clair ;
       - voir le résultat en direct dans l'aperçu, avec un avertissement si un
         texte devient peu lisible ;
       - ENREGISTRER, UTILISER, SUPPRIMER, IMPORTER et EXPORTER un thème.
     Les thèmes intégrés ne sont jamais modifiés : on en fait une copie.

EN : "Manage themes" window (View → Theme menu). It lets the user start from
     a theme (built-in or custom) and DUPLICATE it, change each colour (colour
     picker or #RRGGBB code), the name and the dark/light flag, see the result
     live in the preview with a warning when text becomes hard to read, and
     SAVE, USE, DELETE, IMPORT and EXPORT a theme. Built-in themes are never
     modified: a copy is made instead.
"""

import logging
from html import escape
from pathlib import Path

from PySide6.QtCore import QLocale, QRegularExpression, Qt, Signal
from PySide6.QtGui import QColor, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from runecast.core.themes import (
    COLOR_KEYS,
    DEFAULT_THEME,
    MINIMUM_CONTRAST,
    Theme,
    ThemeError,
    all_themes,
    custom_themes_folder,
    delete_custom_theme,
    duplicate_theme,
    export_theme,
    import_theme,
    readability_problems,
    save_custom_theme,
    theme_from_dict,
    theme_to_dict,
)
from runecast.ui.i18n import keep_left_to_right
from runecast.ui.theme import build_palette

logger = logging.getLogger(__name__)

# FR : Taille des petits carrés de couleur. EN : Size of the small colour squares.
SWATCH_SIZE = (32, 22)


def preview_stylesheet(colors: dict[str, str]) -> str:
    """Feuille de style de l'aperçu / Preview style sheet.

    FR : Toutes les règles commencent par « #themePreview » : elles ne
         touchent que l'aperçu, jamais le reste de RuneCast.
    EN : Every rule starts with "#themePreview": it only affects the preview,
         never the rest of RuneCast.
    """
    c = colors
    return f"""
        #themePreview {{ background: {c["window"]}; border: 1px solid {c["border"]};
            border-radius: 4px; }}
        #themePreview QLabel, #themePreview QCheckBox {{ color: {c["text"]};
            background: transparent; }}
        #themePreview QLabel:disabled {{ color: {c["disabled_text"]}; }}
        #themePreview QLineEdit {{ background: {c["base"]}; color: {c["text"]};
            border: 1px solid {c["border"]}; border-radius: 3px; padding: 3px; }}
        #themePreview QListWidget {{ background: {c["base"]}; color: {c["text"]};
            alternate-background-color: {c["alternate_base"]};
            selection-background-color: {c["highlight"]};
            selection-color: {c["highlighted_text"]};
            border: 1px solid {c["border"]}; }}
        #themePreview QPushButton {{ background: {c["surface"]}; color: {c["text"]};
            border: 1px solid {c["accent"]}; border-radius: 4px; padding: 6px 16px; }}
    """


class ThemeEditorDialog(QDialog):
    """Fenêtre « Gérer les thèmes » / "Manage themes" window."""

    # FR : la liste des thèmes a changé (création, import, suppression…).
    # EN : the list of themes changed (creation, import, deletion…).
    themes_changed = Signal()
    # FR : l'utilisateur veut utiliser ce thème. EN : the user wants to use this theme.
    theme_chosen = Signal(str)

    def __init__(self, config_dir: Path, current_theme_id: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("themeEditorDialog")
        self.setWindowTitle(self.tr("Thèmes personnels"))
        self.config_dir = config_dir
        self.folder = custom_themes_folder(config_dir)
        self.themes: dict[str, Theme] = all_themes(config_dir)
        self.current: Theme = self.themes.get(current_theme_id) or self.themes[DEFAULT_THEME]
        self.edited_colors: dict[str, str] = dict(self.current.colors)
        self.dirty = False
        self._loading = False

        self._build()
        self._fill_combo()
        self.select_theme(self.current.id, ask=False)
        self.setMinimumWidth(820)

    # ------------------------------------------------------------------
    # FR : Construction de la fenêtre / EN : Building the window
    # ------------------------------------------------------------------
    def _build(self) -> None:
        # FR : 1. Choix du thème + actions. EN : 1. Theme choice + actions.
        self.theme_combo = QComboBox()
        self.theme_combo.currentIndexChanged.connect(self._on_combo_changed)
        self.duplicate_button = QPushButton(self.tr("Dupliquer"))
        self.duplicate_button.clicked.connect(self.duplicate)
        self.import_button = QPushButton(self.tr("Importer…"))
        self.import_button.clicked.connect(self.import_file)
        self.export_button = QPushButton(self.tr("Exporter…"))
        self.export_button.clicked.connect(self.export_file)
        self.delete_button = QPushButton(self.tr("Supprimer"))
        self.delete_button.clicked.connect(self.delete_current)
        top = QHBoxLayout()
        top.addWidget(QLabel(self.tr("Thème :")))
        top.addWidget(self.theme_combo, stretch=1)
        for button in (
            self.duplicate_button,
            self.import_button,
            self.export_button,
            self.delete_button,
        ):
            top.addWidget(button)

        self.builtin_note = QLabel(
            self.tr(
                "Les thèmes intégrés ne peuvent pas être modifiés. "
                "Clique sur « Dupliquer » pour créer ta propre version."
            )
        )
        self.builtin_note.setWordWrap(True)

        # FR : 2. Nom, sombre/clair et les 12 couleurs.
        # EN : 2. Name, dark/light and the 12 colours.
        self.name_edit = QLineEdit()
        self.name_edit.textEdited.connect(self._mark_dirty)
        self.dark_check = QCheckBox(self.tr("Thème sombre"))
        self.dark_check.toggled.connect(self._mark_dirty)
        form = QFormLayout()
        form.addRow(self.tr("Nom :"), self.name_edit)
        form.addRow("", self.dark_check)

        labels = self.role_labels()
        colors_grid = QGridLayout()
        self.swatches: dict[str, QPushButton] = {}
        self.hex_edits: dict[str, QLineEdit] = {}
        validator = QRegularExpressionValidator(QRegularExpression(r"#?[0-9A-Fa-f]{0,6}"))
        for row, key in enumerate(COLOR_KEYS):
            swatch = QPushButton()
            swatch.setObjectName(f"swatch_{key}")
            swatch.setFixedSize(*SWATCH_SIZE)
            swatch.setToolTip(self.tr("Choisir une couleur"))
            swatch.clicked.connect(lambda _checked=False, k=key: self.pick_color(k))
            hex_edit = QLineEdit()
            hex_edit.setValidator(validator)
            hex_edit.setMaxLength(7)
            hex_edit.setFixedWidth(90)
            hex_edit.editingFinished.connect(lambda k=key: self._on_hex_finished(k))
            colors_grid.addWidget(QLabel(labels[key]), row, 0)
            colors_grid.addWidget(swatch, row, 1)
            colors_grid.addWidget(hex_edit, row, 2)
            self.swatches[key] = swatch
            self.hex_edits[key] = hex_edit

        editor = QVBoxLayout()
        editor.addLayout(form)
        editor.addLayout(colors_grid)
        editor.addStretch()

        # FR : 3. Aperçu en direct et lisibilité. EN : 3. Live preview and readability.
        self.preview = self._build_preview()
        self.readability_label = QLabel()
        self.readability_label.setObjectName("readabilityLabel")
        self.readability_label.setWordWrap(True)
        right = QVBoxLayout()
        # FR : texte traduit à part (l'outil de traduction ne lit pas les f-strings).
        # EN : text translated separately (the translation tool skips f-strings).
        preview_title = self.tr("Aperçu")
        right.addWidget(QLabel(f"<b>{escape(preview_title)}</b>"))
        right.addWidget(self.preview)
        right.addWidget(self.readability_label)
        right.addStretch()

        middle = QHBoxLayout()
        middle.addLayout(editor, stretch=1)
        middle.addSpacing(16)
        middle.addLayout(right, stretch=1)

        # FR : 4. Boutons du bas. EN : 4. Bottom buttons.
        self.save_button = QPushButton(self.tr("Enregistrer"))
        self.save_button.clicked.connect(self.save)
        self.use_button = QPushButton(self.tr("Utiliser ce thème"))
        self.use_button.clicked.connect(self.use_current)
        self.close_button = QPushButton(self.tr("Fermer"))
        self.close_button.clicked.connect(self.reject)
        bottom = QHBoxLayout()
        bottom.addStretch()
        for button in (self.save_button, self.use_button, self.close_button):
            bottom.addWidget(button)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.builtin_note)
        layout.addLayout(middle)
        layout.addLayout(bottom)

    def _build_preview(self) -> QFrame:
        """FR : petit échantillon d'interface coloré avec le thème édité.

        EN : small sample interface coloured with the edited theme.
        """
        frame = QFrame()
        frame.setObjectName("themePreview")
        frame.setAutoFillBackground(True)
        sample = QLabel(self.tr("Exemple de texte"))
        field = QLineEdit()
        field.setPlaceholderText(self.tr("Champ de saisie"))
        button = QPushButton(self.tr("Bouton"))
        items = QListWidget()
        items.addItems([self.tr("Élément sélectionné"), self.tr("Autre élément")])
        items.setCurrentRow(0)
        items.setAlternatingRowColors(True)
        items.setFixedHeight(64)
        self.preview_link_text = self.tr("Un lien")
        self.preview_link = link = QLabel()
        check = QCheckBox(self.tr("Case cochée"))
        check.setChecked(True)
        disabled = QLabel(self.tr("Texte désactivé"))
        disabled.setEnabled(False)
        layout = QVBoxLayout(frame)
        self.preview_field = field
        for widget in (sample, field, button, items, check, link, disabled):
            # FR : simple échantillon : il ne réagit ni au clavier ni à la souris.
            # EN : just a sample: it reacts neither to the keyboard nor the mouse.
            widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            layout.addWidget(widget)
        return frame

    # ------------------------------------------------------------------
    # FR : Textes traduits / EN : Translated texts
    # ------------------------------------------------------------------
    def role_labels(self) -> dict[str, str]:
        """FR : nom affiché de chaque rôle de couleur. EN : display name of each colour role."""
        return {
            "window": self.tr("Fond des fenêtres"),
            "base": self.tr("Fond des champs et tableaux"),
            "alternate_base": self.tr("Lignes alternées"),
            "surface": self.tr("Boutons et menus"),
            "text": self.tr("Texte"),
            "disabled_text": self.tr("Texte désactivé"),
            "placeholder": self.tr("Texte d'exemple (champs vides)"),
            "highlight": self.tr("Sélection"),
            "highlighted_text": self.tr("Texte sélectionné"),
            "accent": self.tr("Couleur vive (survol, bordures)"),
            "link": self.tr("Liens"),
            "border": self.tr("Bordures"),
        }

    def theme_label(self, theme: Theme) -> str:
        """FR : nom d'un thème, traduit pour les thèmes intégrés.

        EN : name of a theme, translated for built-in themes.
        """
        builtin_names = {
            "turquoise": self.tr("Turquoise"),
            "noir": self.tr("Noir"),
            "sombre": self.tr("Sombre"),
            "clair": self.tr("Clair"),
        }
        if theme.builtin and theme.id in builtin_names:
            return builtin_names[theme.id]
        return theme.name

    def display_name(self, theme: Theme) -> str:
        """FR : nom affiché dans la liste (« (intégré) » pour les thèmes fournis).

        EN : name shown in the list ("(built-in)" for shipped themes).
        """
        if theme.builtin:
            return self.tr("{name} (intégré)").format(name=self.theme_label(theme))
        return theme.name

    # ------------------------------------------------------------------
    # FR : Choix du thème / EN : Theme choice
    # ------------------------------------------------------------------
    def _fill_combo(self) -> None:
        """FR : remplit la liste des thèmes. EN : fill the theme list."""
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        for theme in self.themes.values():
            self.theme_combo.addItem(self.display_name(theme), theme.id)
        self.theme_combo.blockSignals(False)

    def _on_combo_changed(self, index: int) -> None:
        theme_id = self.theme_combo.itemData(index)
        if theme_id and theme_id != self.current.id:
            self.select_theme(theme_id)

    def select_theme(self, theme_id: str, ask: bool = True) -> bool:
        """Affiche un thème dans l'éditeur / Show a theme in the editor.

        FR : S'il y a des modifications non enregistrées, on demande d'abord.
        EN : If there are unsaved changes, the user is asked first.
        """
        if ask and not self._handle_unsaved_changes():
            self._show_current_in_combo()
            return False
        self.current = self.themes[theme_id]
        self.edited_colors = dict(self.current.colors)
        self._loading = True
        self.name_edit.setText(self.theme_label(self.current))
        self.dark_check.setChecked(self.current.dark)
        for key in COLOR_KEYS:
            self._show_color(key)
        self._loading = False
        self.dirty = False
        editable = not self.current.builtin
        self.builtin_note.setVisible(not editable)
        for widget in (
            self.name_edit,
            self.dark_check,
            self.save_button,
            self.delete_button,
            *self.swatches.values(),
            *self.hex_edits.values(),
        ):
            widget.setEnabled(editable)
        self._show_current_in_combo()
        self._update_preview()
        return True

    def _show_current_in_combo(self) -> None:
        index = self.theme_combo.findData(self.current.id)
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentIndex(index)
        self.theme_combo.blockSignals(False)

    # ------------------------------------------------------------------
    # FR : Couleurs / EN : Colours
    # ------------------------------------------------------------------
    def _show_color(self, key: str) -> None:
        """FR : affiche une couleur dans son carré et son champ. EN : show a colour."""
        value = self.edited_colors[key]
        self.swatches[key].setStyleSheet(
            f"background: {value}; border: 1px solid #808080; border-radius: 3px;"
        )
        self.hex_edits[key].setText(value)

    def set_color(self, key: str, value: str) -> None:
        """FR : change une couleur du thème édité. EN : change a colour of the edited theme."""
        self.edited_colors[key] = value.upper()
        self._show_color(key)
        self._mark_dirty()

    def pick_color(self, key: str) -> None:
        """FR : ouvre le sélecteur de couleurs. EN : open the colour picker."""
        color = QColorDialog.getColor(
            QColor(self.edited_colors[key]), self, self.tr("Choisir une couleur")
        )
        if color.isValid():
            self.set_color(key, color.name())

    def _on_hex_finished(self, key: str) -> None:
        """FR : code #RRGGBB tapé à la main (le « # » peut être oublié) ; un
             code incomplet est annulé.
        EN : #RRGGBB code typed by hand (the "#" may be left out); an
             incomplete code is reverted.
        """
        text = self.hex_edits[key].text().strip()
        if not text.startswith("#"):
            text = "#" + text
        if len(text) == 7 and text.upper() != self.edited_colors[key]:
            self.set_color(key, text)
        else:
            self._show_color(key)

    def _mark_dirty(self, *_args) -> None:
        if self._loading:
            return
        self.dirty = True
        self._update_preview()

    def edited_theme(self) -> Theme:
        """FR : le thème tel qu'il est dans l'éditeur. EN : the theme as in the editor."""
        return Theme(
            id=self.current.id,
            name=self.name_edit.text().strip(),
            dark=self.dark_check.isChecked(),
            colors=dict(self.edited_colors),
            builtin=self.current.builtin,
        )

    def _update_preview(self) -> None:
        """FR : met à jour l'aperçu et l'avis de lisibilité. EN : update preview and readability."""
        colors = self.edited_colors
        # FR : RuneCast a déjà son propre thème : chaque élément de l'aperçu
        #      reçoit donc ses couleurs une par une (palette + feuille de style
        #      limitée à l'aperçu), sinon il garderait celles de RuneCast.
        # EN : RuneCast already has its own theme: each preview element is
        #      therefore given its colours one by one (palette + style sheet
        #      limited to the preview), otherwise it would keep RuneCast's.
        palette = build_palette(colors)
        for widget in (self.preview, *self.preview.findChildren(QWidget)):
            widget.setPalette(palette)
        self.preview.setStyleSheet(preview_stylesheet(colors))
        self.preview_link.setText(
            f'<a href="#" style="color: {colors["link"]};">{escape(self.preview_link_text)}</a>'
        )
        labels = self.role_labels()
        problems = readability_problems(colors)
        if not problems:
            self.readability_label.setText(self.tr("Lisibilité : bonne"))
            return
        warning = self.tr(
            "Attention : « {first} » sur « {second} » est peu lisible "
            "(contraste {ratio}, au moins {minimum} conseillé)."
        )
        lines = [
            warning.format(
                first=labels[fg],
                second=labels[bg],
                ratio=self.ratio_text(ratio),
                minimum=self.ratio_text(MINIMUM_CONTRAST),
            )
            for fg, bg, ratio in problems
        ]
        self.readability_label.setText("\n".join(lines))

    @staticmethod
    def ratio_text(ratio: float) -> str:
        """FR : contraste écrit à la façon de la langue choisie (« 3,2:1 », « 3.2:1 »…).

        EN : contrast written the way of the chosen language ("3,2:1", "3.2:1"…).
        """
        locale = QLocale()
        return f"{locale.toString(ratio, 'f', 1)}:{locale.toString(1)}"

    # ------------------------------------------------------------------
    # FR : Actions / EN : Actions
    # ------------------------------------------------------------------
    def duplicate(self) -> None:
        """FR : crée un thème personnel à partir du thème affiché.

        EN : create a custom theme from the displayed theme.
        """
        if not self._handle_unsaved_changes():
            return
        base = self.edited_theme()
        name = self.tr("{name} (copie)").format(name=self.theme_label(self.current))
        copy = duplicate_theme(base, name, set(self.themes))
        save_custom_theme(copy, self.folder)
        logger.info("Thème dupliqué / Theme duplicated: %s -> %s", self.current.id, copy.id)
        self.themes[copy.id] = copy
        self._fill_combo()
        self.select_theme(copy.id, ask=False)
        self.themes_changed.emit()

    def save(self) -> bool:
        """FR : enregistre le thème personnel affiché. EN : save the displayed custom theme."""
        if self.current.builtin:
            return False
        theme = self.edited_theme()
        if not theme.name:
            QMessageBox.warning(self, self.tr("Nom manquant"), self.tr("Donne un nom au thème."))
            return False
        try:
            theme = theme_from_dict(theme_to_dict(theme))
            save_custom_theme(theme, self.folder)
        except (ThemeError, OSError) as error:
            logger.warning("Thème non enregistré / Theme not saved: %s (%s)", theme.id, error)
            QMessageBox.warning(self, self.tr("Enregistrement impossible"), str(error))
            return False
        logger.info("Thème enregistré / Theme saved: %s", theme.id)
        self.themes[theme.id] = theme
        self.current = theme
        self.dirty = False
        self._fill_combo()
        self._show_current_in_combo()
        self.themes_changed.emit()
        return True

    def use_current(self) -> None:
        """FR : applique le thème affiché à RuneCast (en l'enregistrant d'abord).

        EN : apply the displayed theme to RuneCast (saving it first).
        """
        if self.dirty and not self.save():
            return
        self.theme_chosen.emit(self.current.id)

    def delete_current(self) -> None:
        """FR : supprime le thème personnel affiché, après confirmation.

        EN : delete the displayed custom theme, after confirmation.
        """
        if self.current.builtin:
            return
        answer = QMessageBox.question(
            self,
            self.tr("Supprimer le thème ?"),
            self.tr("Le thème « {name} » sera supprimé définitivement. Continuer ?").format(
                name=self.current.name
            ),
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        delete_custom_theme(self.current.id, self.folder)
        logger.info("Thème supprimé / Theme deleted: %s", self.current.id)
        del self.themes[self.current.id]
        self.dirty = False
        self._fill_combo()
        self.select_theme(DEFAULT_THEME, ask=False)
        self.themes_changed.emit()

    def import_file(self) -> None:
        """FR : importe un fichier de thème (.json). EN : import a theme file (.json)."""
        if not self._handle_unsaved_changes():
            return
        path, _filter = QFileDialog.getOpenFileName(
            self,
            self.tr("Importer un thème"),
            str(Path.home()),
            self.tr("Thèmes RuneCast (*.json)"),
        )
        if not path:
            return
        try:
            theme = import_theme(Path(path), self.folder, set(self.themes))
        except (ThemeError, OSError) as error:
            logger.warning("Thème non importé / Theme not imported: %s (%s)", path, error)
            QMessageBox.warning(
                self,
                self.tr("Import impossible"),
                self.tr("Ce fichier n'est pas un thème RuneCast valide :\n{details}").format(
                    details=error
                ),
            )
            return
        logger.info("Thème importé / Theme imported: %s -> %s", path, theme.id)
        self.themes[theme.id] = theme
        self._fill_combo()
        self.select_theme(theme.id, ask=False)
        self.themes_changed.emit()
        QMessageBox.information(
            self,
            self.tr("Thème importé"),
            self.tr("Le thème « {name} » a été ajouté.").format(name=theme.name),
        )

    def export_file(self) -> None:
        """FR : exporte le thème affiché dans un fichier, pour le partager.

        EN : export the displayed theme to a file, to share it.
        """
        path, _filter = QFileDialog.getSaveFileName(
            self,
            self.tr("Exporter le thème"),
            str(Path.home() / f"{self.current.id}.json"),
            self.tr("Thèmes RuneCast (*.json)"),
        )
        if not path:
            return
        destination = Path(path)
        if destination.suffix.lower() != ".json":
            # FR : on ajoute « .json » ; si ce fichier existe déjà, on demande
            #      avant de le remplacer (la fenêtre de Qt ne l'a pas fait).
            # EN : ".json" is added; if that file already exists, ask before
            #      replacing it (Qt's window did not).
            destination = destination.with_name(destination.name + ".json")
            if destination.exists() and not self._confirm_replace(destination):
                return
        theme = self.edited_theme()
        if not theme.name:
            QMessageBox.warning(self, self.tr("Nom manquant"), self.tr("Donne un nom au thème."))
            return
        try:
            export_theme(theme, destination)
        except OSError as error:
            logger.warning("Thème non exporté / Theme not exported: %s (%s)", destination, error)
            QMessageBox.warning(self, self.tr("Export impossible"), str(error))
            return
        logger.info("Thème exporté / Theme exported: %s -> %s", theme.id, destination)

    def _confirm_replace(self, path: Path) -> bool:
        """FR : demande avant de remplacer un fichier. EN : ask before replacing a file."""
        answer = QMessageBox.question(
            self,
            self.tr("Remplacer le fichier ?"),
            self.tr("Le fichier « {file} » existe déjà. Le remplacer ?").format(
                file=keep_left_to_right(str(path))
            ),
        )
        return answer == QMessageBox.StandardButton.Yes

    # ------------------------------------------------------------------
    # FR : Modifications non enregistrées / EN : Unsaved changes
    # ------------------------------------------------------------------
    def _handle_unsaved_changes(self) -> bool:
        """FR : propose d'enregistrer. Renvoie False si l'utilisateur annule.

        EN : offer to save. Returns False if the user cancels.
        """
        if not self.dirty:
            return True
        answer = QMessageBox.question(
            self,
            self.tr("Modifications non enregistrées"),
            self.tr("Le thème « {name} » a été modifié. Enregistrer les modifications ?").format(
                name=self.current.name
            ),
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if answer == QMessageBox.StandardButton.Save:
            return self.save()
        if answer == QMessageBox.StandardButton.Discard:
            # FR : on revient à la version enregistrée. EN : back to the saved version.
            self.select_theme(self.current.id, ask=False)
            return True
        return False

    def reject(self) -> None:
        """FR : fermeture (bouton Fermer, Échap…). EN : closing (Close button, Esc…)."""
        if self._handle_unsaved_changes():
            super().reject()
