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

"""Fenêtre « Paramètres » / "Settings" window.

FR : Rassemble tous les réglages de RuneCast, rangés par pages (liste à
     gauche, contenu à droite). Trois boutons, comme dans la plupart des
     logiciels :
       - « OK » applique les changements et ferme ;
       - « Appliquer » applique sans fermer ;
       - « Annuler » ferme sans rien changer de ce qui n'a pas été appliqué.
     Chaque page sait lire les réglages (load) et y écrire ses valeurs
     (store). Les étapes suivantes ajouteront leurs propres pages
     (traduction, modèles, moteurs…) de la même façon.

EN : Gathers all RuneCast settings, sorted into pages (list on the left,
     content on the right). Three buttons, as in most software: "OK" applies
     and closes; "Apply" applies without closing; "Cancel" closes without
     changing anything that was not applied. Each page can read the settings
     (load) and write its values into them (store). Later steps will add
     their own pages (translation, models, engines…) the same way.
"""

from collections.abc import Callable
from dataclasses import replace

from PySide6.QtCore import QEvent, QLocale, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from runecast.core.cache import TranslationCache, cache_file
from runecast.core.languages import LANGUAGES, SYSTEM_LANGUAGE
from runecast.core.paths import AppPaths
from runecast.core.settings import Settings
from runecast.core.themes import Theme, find_theme
from runecast.ui.i18n import format_size, keep_left_to_right
from runecast.ui.models_page import ModelsPage
from runecast.ui.settings_base import SettingsPage


class GeneralPage(SettingsPage):
    """Page « Général » : langue et thème / "General" page: language and theme."""

    def __init__(self, theme_name: Callable[[Theme], str]) -> None:
        super().__init__()
        self.setObjectName("generalPage")
        # FR : fonction qui donne le nom affiché d'un thème (traduit pour les
        #      thèmes intégrés). EN : function giving a theme's display name.
        self.theme_name = theme_name
        self.themes: dict[str, Theme] = {}
        self.language_combo = QComboBox()
        self.language_combo.setObjectName("languageCombo")
        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("themeCombo")
        self.manage_themes_button = QPushButton()
        theme_row = QHBoxLayout()
        theme_row.addWidget(self.theme_combo, stretch=1)
        theme_row.addWidget(self.manage_themes_button)

        self.language_label = QLabel()
        self.theme_label = QLabel()
        self.language_note = QLabel()
        self.language_note.setWordWrap(True)
        form = QFormLayout(self)
        form.addRow(self.language_label, self.language_combo)
        form.addRow("", self.language_note)
        form.addRow(self.theme_label, theme_row)
        self.retranslate()

    def title(self) -> str:
        return self.tr("Général")

    def retranslate(self) -> None:
        self.language_label.setText(self.tr("Langue de l'interface :"))
        self.theme_label.setText(self.tr("Thème :"))
        self.manage_themes_button.setText(self.tr("Gérer les thèmes…"))
        self.language_note.setText(
            self.tr(
                "C'est la langue des menus et des fenêtres de RuneCast. Les jeux "
                "pourront être traduits vers d'autres langues."
            )
        )
        current = self.language_combo.currentData()
        self.language_combo.clear()
        self.language_combo.addItem(self.tr("Langue du système"), SYSTEM_LANGUAGE)
        for code, language in LANGUAGES.items():
            self.language_combo.addItem(language.native_name, code)
        if current is not None:
            self.language_combo.setCurrentIndex(self.language_combo.findData(current))
        self.set_themes(self.themes, self.theme_combo.currentData())

    def set_themes(self, themes: dict[str, Theme], selected: str | None) -> None:
        """FR : (re)remplit la liste des thèmes. EN : (re)fill the theme list."""
        self.themes = themes
        self.theme_combo.clear()
        for theme in themes.values():
            self.theme_combo.addItem(self.theme_name(theme), theme.id)
        if themes:
            chosen = find_theme(selected or "", themes).id
            self.theme_combo.setCurrentIndex(self.theme_combo.findData(chosen))

    def load(self, settings: Settings) -> None:
        index = self.language_combo.findData(settings.interface_language)
        self.language_combo.setCurrentIndex(max(index, 0))
        self.set_themes(self.themes, settings.theme)

    def store(self, settings: Settings) -> None:
        settings.interface_language = self.language_combo.currentData()
        settings.theme = self.theme_combo.currentData()


class WindowPage(SettingsPage):
    """Page « Fenêtre » / "Window" page."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("windowPage")
        self.remember_check = QCheckBox()
        layout = QVBoxLayout(self)
        layout.addWidget(self.remember_check)
        layout.addStretch()
        self.retranslate()

    def title(self) -> str:
        return self.tr("Fenêtre")

    def retranslate(self) -> None:
        self.remember_check.setText(
            self.tr("Rouvrir la fenêtre principale à la même taille et à la même place")
        )

    def load(self, settings: Settings) -> None:
        self.remember_check.setChecked(settings.remember_window)

    def store(self, settings: Settings) -> None:
        settings.remember_window = self.remember_check.isChecked()


class FoldersLogPage(SettingsPage):
    """Page « Dossiers et journal » / "Folders and log" page."""

    def __init__(self, paths: AppPaths) -> None:
        super().__init__()
        self.setObjectName("foldersLogPage")
        self.paths = paths
        self.settings_folder_label = QLabel()
        self.data_folder_label = QLabel()
        for label in (self.settings_folder_label, self.data_folder_label):
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            label.setWordWrap(True)
        self.manage_folders_button = QPushButton()
        self.detailed_log_check = QCheckBox()
        self.detailed_log_note = QLabel()
        self.detailed_log_note.setWordWrap(True)
        self.open_log_button = QPushButton()

        self.folders_title = QLabel()
        self.log_title = QLabel()
        folders_row = QHBoxLayout()
        folders_row.addWidget(self.manage_folders_button)
        folders_row.addStretch()
        log_row = QHBoxLayout()
        log_row.addWidget(self.open_log_button)
        log_row.addStretch()
        layout = QVBoxLayout(self)
        for widget in (self.folders_title, self.settings_folder_label, self.data_folder_label):
            layout.addWidget(widget)
        layout.addLayout(folders_row)
        layout.addSpacing(12)
        for widget in (self.log_title, self.detailed_log_check, self.detailed_log_note):
            layout.addWidget(widget)
        layout.addLayout(log_row)
        layout.addStretch()
        self.retranslate()

    def title(self) -> str:
        return self.tr("Dossiers et journal")

    def retranslate(self) -> None:
        folders_title = self.tr("Dossiers")
        log_title = self.tr("Journal")
        self.folders_title.setText(f"<b>{folders_title}</b>")
        self.log_title.setText(f"<b>{log_title}</b>")
        self.manage_folders_button.setText(self.tr("Gérer les dossiers…"))
        self.detailed_log_check.setText(self.tr("Journal détaillé"))
        self.detailed_log_note.setText(
            self.tr(
                "À activer seulement pour signaler un problème : RuneCast note "
                "alors aussi les messages techniques."
            )
        )
        self.open_log_button.setText(self.tr("Ouvrir le dossier du journal"))
        self.show_paths(self.paths)

    def show_paths(self, paths: AppPaths) -> None:
        """FR : affiche les dossiers utilisés. EN : show the folders in use."""
        self.paths = paths
        self.settings_folder_label.setText(
            self.tr("Réglages : {folder}").format(folder=keep_left_to_right(str(paths.config_dir)))
        )
        self.data_folder_label.setText(
            self.tr("Données : {folder}").format(folder=keep_left_to_right(str(paths.data_dir)))
        )

    def load(self, settings: Settings) -> None:
        self.detailed_log_check.setChecked(settings.detailed_log)

    def store(self, settings: Settings) -> None:
        settings.detailed_log = self.detailed_log_check.isChecked()


class CachePage(SettingsPage):
    """Page « Cache des traductions » / "Translation cache" page.

    FR : Montre ce que contient le cache et l'historique, et permet de les
         vider (après confirmation). Ces boutons agissent tout de suite.
    EN : Shows what the cache and the history hold, and lets the user empty
         them (after confirmation). These buttons act at once.
    """

    def __init__(self, paths: AppPaths) -> None:
        super().__init__()
        self.setObjectName("cachePage")
        self.paths = paths
        self.explanation = QLabel()
        self.explanation.setWordWrap(True)
        self.translations_label = QLabel()
        self.history_label = QLabel()
        self.size_label = QLabel()
        self.clear_cache_button = QPushButton()
        self.clear_cache_button.clicked.connect(self.clear_cache)
        self.clear_history_button = QPushButton()
        self.clear_history_button.clicked.connect(self.clear_history)
        buttons = QHBoxLayout()
        buttons.addWidget(self.clear_cache_button)
        buttons.addWidget(self.clear_history_button)
        buttons.addStretch()
        layout = QVBoxLayout(self)
        for widget in (
            self.explanation,
            self.translations_label,
            self.history_label,
            self.size_label,
        ):
            layout.addWidget(widget)
        layout.addLayout(buttons)
        layout.addStretch()
        self.retranslate()

    def title(self) -> str:
        return self.tr("Cache des traductions")

    def retranslate(self) -> None:
        self.explanation.setText(
            self.tr(
                "RuneCast garde chaque phrase déjà traduite : une phrase identique "
                "n'est jamais retraduite (c'est plus rapide, et gratuit avec les "
                "moteurs payants). L'historique garde la trace de ce qui a été traduit."
            )
        )
        self.clear_cache_button.setText(self.tr("Vider le cache…"))
        self.clear_history_button.setText(self.tr("Vider l'historique…"))
        self.refresh()

    def _cache(self) -> TranslationCache | None:
        """FR : ouvre la base si elle existe déjà (sans la créer pour rien).

        EN : open the base if it already exists (without creating it for nothing).
        """
        path = cache_file(self.paths.data_dir)
        return TranslationCache(path) if path.exists() else None

    def refresh(self) -> None:
        """FR : met à jour les chiffres. EN : update the figures."""
        translations = history = size = 0
        cache = self._cache()
        if cache is not None:
            with cache:
                stats = cache.stats()
            translations, history, size = stats.translations, stats.history, stats.size_bytes
        self.translations_label.setText(
            self.tr("Phrases en mémoire : {count}").format(count=QLocale().toString(translations))
        )
        self.history_label.setText(
            self.tr("Lignes d'historique : {count}").format(count=QLocale().toString(history))
        )
        self.size_label.setText(
            self.tr("Taille du fichier : {size}").format(size=format_size(size))
        )
        self.clear_cache_button.setEnabled(translations > 0)
        self.clear_history_button.setEnabled(history > 0)

    def _confirm(self, title: str, text: str) -> bool:
        answer = QMessageBox.question(self, title, text)
        return answer == QMessageBox.StandardButton.Yes

    def clear_cache(self) -> None:
        """FR : vide le cache, après confirmation. EN : empty the cache, after confirmation."""
        if not self._confirm(
            self.tr("Vider le cache ?"),
            self.tr(
                "Les phrases déjà traduites seront oubliées : elles seront "
                "retraduites la prochaine fois. Continuer ?"
            ),
        ):
            return
        cache = self._cache()
        if cache is not None:
            with cache:
                cache.clear_cache()
        self.refresh()

    def clear_history(self) -> None:
        """FR : vide l'historique (après confirmation). EN : empty the history (confirmed)."""
        if not self._confirm(
            self.tr("Vider l'historique ?"),
            self.tr("L'historique des traductions sera effacé définitivement. Continuer ?"),
        ):
            return
        cache = self._cache()
        if cache is not None:
            with cache:
                cache.clear_history()
        self.refresh()

    def show_paths(self, paths: AppPaths) -> None:
        """FR : les données ont changé de dossier. EN : the data moved."""
        self.paths = paths
        self.refresh()

    def load(self, settings: Settings) -> None:
        self.refresh()

    def store(self, settings: Settings) -> None:
        """FR : aucun réglage sur cette page. EN : no setting on this page."""


class SettingsDialog(QDialog):
    """Fenêtre « Paramètres » / "Settings" window."""

    # FR : nouveaux réglages à appliquer (une copie : les réglages en cours ne
    #      sont jamais modifiés par la fenêtre elle-même).
    # EN : new settings to apply (a copy: the current settings are never
    #      changed by the window itself).
    applied = Signal(object)

    def __init__(
        self,
        settings: Settings,
        themes: dict[str, Theme],
        paths: AppPaths,
        theme_name: Callable[[Theme], str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("settingsDialog")
        self.settings = settings
        self.general_page = GeneralPage(theme_name)
        self.general_page.set_themes(themes, settings.theme)
        self.window_page = WindowPage()
        self.folders_page = FoldersLogPage(paths)
        self.cache_page = CachePage(paths)
        self.models_page = ModelsPage(paths)
        self.pages: list[SettingsPage] = [
            self.general_page,
            self.models_page,
            self.cache_page,
            self.window_page,
            self.folders_page,
        ]

        self.page_list = QListWidget()
        self.page_list.setObjectName("pageList")
        self.page_list.setFixedWidth(190)
        self.stack = QStackedWidget()
        for page in self.pages:
            self.page_list.addItem(page.title())
            self.stack.addWidget(page)
        self.page_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.page_list.setCurrentRow(0)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.apply_button.clicked.connect(self.apply)

        body = QHBoxLayout()
        body.addWidget(self.page_list)
        body.addWidget(self.stack, stretch=1)
        layout = QVBoxLayout(self)
        layout.addLayout(body)
        layout.addWidget(self.buttons)
        self.resize(860, 560)
        self.load(settings)
        self.retranslate()

    @property
    def apply_button(self) -> QPushButton:
        return self.buttons.button(QDialogButtonBox.StandardButton.Apply)

    def load(self, settings: Settings) -> None:
        """FR : affiche des réglages dans toutes les pages. EN : show settings in every page."""
        self.settings = settings
        for page in self.pages:
            page.load(settings)

    def edited_settings(self) -> Settings:
        """FR : copie des réglages avec les valeurs de la fenêtre.

        EN : copy of the settings with the window's values.
        """
        edited = replace(self.settings, extra=dict(self.settings.extra))
        for page in self.pages:
            page.store(edited)
        return edited

    def apply(self) -> None:
        """FR : applique les changements, sans fermer. EN : apply the changes, without closing."""
        edited = self.edited_settings()
        self.settings = edited
        self.applied.emit(edited)

    def accept(self) -> None:
        """FR : « OK » : appliquer puis fermer. EN : "OK": apply then close."""
        self.apply()
        super().accept()

    def done(self, result: int) -> None:
        """FR : fermeture (OK, Annuler, Échap) : chaque page s'arrête proprement.

        EN : closing (OK, Cancel, Esc): every page stops cleanly.
        """
        for page in self.pages:
            page.shutdown()
        super().done(result)

    def retranslate(self) -> None:
        """FR : (re)pose les textes dans la langue actuelle. EN : (re)set every text."""
        self.setWindowTitle(self.tr("Paramètres"))
        for index, page in enumerate(self.pages):
            page.retranslate()
            self.page_list.item(index).setText(page.title())

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802 (nom imposé par Qt)
        """FR : la langue a changé (bouton Appliquer). EN : the language changed (Apply)."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslate()
        super().changeEvent(event)
