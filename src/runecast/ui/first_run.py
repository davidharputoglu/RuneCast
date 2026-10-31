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

"""Assistant de premier lancement / First-launch wizard.

FR : S'ouvre au tout premier lancement (profil vierge, sans fichier de
     réglages) et reste accessible par Aide → Assistant de premier
     lancement… Cinq pages :
       1. langue de l'interface (appliquée aussitôt) ;
       2. thème (appliqué aussitôt) ;
       3. traduction en ligne ou 100 % locale ;
       4. modèle local pour ta langue (téléchargement facultatif ; pour le
          kazakh, l'ouzbek, le turkmène, le tatar ou l'ouïghour : NLLB-200,
          après acceptation de sa licence) ;
       5. résumé. Tout reste modifiable dans Fichier → Paramètres…

EN : Opens at the very first launch (blank profile, no settings file) and
     stays available from Help → First-launch wizard… Five pages: interface
     language (applied at once); theme (applied at once); online or 100 %
     local translation; local model for your language (optional download;
     for Kazakh, Uzbek, Turkmen, Tatar or Uyghur: NLLB-200, after accepting
     its license); summary. Everything stays changeable in File → Settings…
"""

from datetime import UTC, datetime

from PySide6.QtCore import QEvent, QLocale, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

from runecast.core.languages import LANGUAGES, SYSTEM_LANGUAGE, resolve_language
from runecast.core.paths import AppPaths
from runecast.core.settings import Settings
from runecast.core.themes import BUILTIN_THEME_IDS, Theme
from runecast.engines.chain import MODE_LOCAL, MODE_ONLINE
from runecast.engines.models import CatalogEntry, load_catalog
from runecast.engines.nllb import NLLB_CODES
from runecast.ui.i18n import format_size, keep_left_to_right, language_name
from runecast.ui.license_dialog import NllbLicenseDialog
from runecast.ui.models_page import model_store, nllb_store
from runecast.ui.tasks import TaskThread

# FR : Langue des jeux la plus courante (Ren'Py). EN : Most common game language.
GAME_LANGUAGE = "en"


class FirstRunWizard(QWizard):
    """Assistant de premier lancement / First-launch wizard."""

    # FR : choix appliqués aussitôt par la fenêtre principale.
    # EN : choices applied at once by the main window.
    language_chosen = Signal(str)
    theme_chosen = Signal(str)
    # FR : licence NLLB acceptée (date ISO). EN : NLLB license accepted (ISO date).
    nllb_license_accepted = Signal(str)

    def __init__(
        self,
        paths: AppPaths,
        settings: Settings,
        themes: dict[str, Theme],
        theme_name,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("firstRunWizard")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.paths = paths
        self.settings = settings
        self.theme_name = theme_name
        self.models = model_store(paths)
        self.nllb = nllb_store(paths)
        self.catalog: list[CatalogEntry] = load_catalog()
        self.task: TaskThread | None = None
        self.license_date = settings.nllb_license_accepted

        # FR : 1. Langue. EN : 1. Language.
        self.language_page = QWizardPage()
        self.welcome_label = QLabel()
        self.welcome_label.setWordWrap(True)
        self.language_combo = QComboBox()
        self.language_combo.setObjectName("wizardLanguage")
        self.language_combo.addItem("", SYSTEM_LANGUAGE)
        for code, language in LANGUAGES.items():
            self.language_combo.addItem(language.native_name, code)
        index = self.language_combo.findData(settings.interface_language)
        self.language_combo.setCurrentIndex(max(index, 0))
        self.language_combo.currentIndexChanged.connect(self._language_changed)
        layout = QVBoxLayout(self.language_page)
        layout.addWidget(self.welcome_label)
        layout.addWidget(self.language_combo)
        layout.addStretch()

        # FR : 2. Thème. EN : 2. Theme.
        self.theme_page = QWizardPage()
        self.theme_buttons = QButtonGroup(self)
        self.theme_radios: dict[str, QRadioButton] = {}
        layout = QVBoxLayout(self.theme_page)
        for theme_id in BUILTIN_THEME_IDS:
            radio = QRadioButton()
            radio.setChecked(theme_id == settings.theme)
            radio.toggled.connect(lambda checked, t=theme_id: checked and self.theme_chosen.emit(t))
            self.theme_buttons.addButton(radio)
            self.theme_radios[theme_id] = radio
            layout.addWidget(radio)
        self.themes = themes
        self.theme_note = QLabel()
        self.theme_note.setWordWrap(True)
        layout.addWidget(self.theme_note)
        layout.addStretch()

        # FR : 3. Mode. EN : 3. Mode.
        self.mode_page = QWizardPage()
        self.online_radio = QRadioButton()
        self.local_radio = QRadioButton()
        self.mode_buttons = QButtonGroup(self)
        self.mode_buttons.addButton(self.online_radio)
        self.mode_buttons.addButton(self.local_radio)
        (
            self.local_radio if settings.translation_mode == MODE_LOCAL else self.online_radio
        ).setChecked(True)
        self.online_note = QLabel()
        self.local_note = QLabel()
        for note in (self.online_note, self.local_note):
            note.setWordWrap(True)
            note.setIndent(24)
        layout = QVBoxLayout(self.mode_page)
        for widget in (self.online_radio, self.online_note, self.local_radio, self.local_note):
            layout.addWidget(widget)
        layout.addStretch()

        # FR : 4. Modèle local. EN : 4. Local model.
        self.model_page = QWizardPage()
        self.model_intro = QLabel()
        self.model_intro.setWordWrap(True)
        self.target_combo = QComboBox()
        self.target_combo.setObjectName("wizardTarget")
        targets = {e.to_code for e in self.catalog if e.from_code == GAME_LANGUAGE} | set(
            NLLB_CODES
        )
        targets.discard(GAME_LANGUAGE)
        for code in sorted(targets, key=lambda c: language_name(c).casefold()):
            self.target_combo.addItem(language_name(code), code)
        self.target_combo.currentIndexChanged.connect(self._update_model)
        self.model_label = QLabel()
        self.model_label.setObjectName("wizardModel")
        self.model_label.setWordWrap(True)
        self.download_button = QPushButton()
        self.download_button.clicked.connect(self.download)
        self.cancel_button = QPushButton()
        self.cancel_button.clicked.connect(self.cancel_download)
        self.progress = QProgressBar()
        download_row = QHBoxLayout()
        download_row.addWidget(self.download_button)
        download_row.addWidget(self.progress, stretch=1)
        download_row.addWidget(self.cancel_button)
        layout = QVBoxLayout(self.model_page)
        layout.addWidget(self.model_intro)
        layout.addWidget(self.target_combo)
        layout.addWidget(self.model_label)
        layout.addLayout(download_row)
        layout.addStretch()
        self._show_progress(False)

        # FR : 5. Résumé. EN : 5. Summary.
        self.summary_page = QWizardPage()
        self.summary_label = QLabel()
        self.summary_label.setObjectName("wizardSummary")
        self.summary_label.setWordWrap(True)
        layout = QVBoxLayout(self.summary_page)
        layout.addWidget(self.summary_label)
        layout.addStretch()

        for page in (
            self.language_page,
            self.theme_page,
            self.mode_page,
            self.model_page,
            self.summary_page,
        ):
            self.addPage(page)
        self.currentIdChanged.connect(self._page_changed)
        self._default_target()
        self.resize(640, 440)
        self.retranslate()

    # ------------------------------------------------------------------
    # FR : Textes / EN : Texts
    # ------------------------------------------------------------------
    def retranslate(self) -> None:
        self.setWindowTitle(self.tr("Bienvenue dans RuneCast"))
        self.language_page.setTitle(self.tr("Langue de l'interface"))
        self.welcome_label.setText(
            self.tr(
                "Bienvenue ! Quelques questions pour préparer RuneCast. Tout reste "
                "modifiable ensuite dans Fichier → Paramètres…"
            )
        )
        self.language_combo.setItemText(0, self.tr("Langue du système"))
        self.theme_page.setTitle(self.tr("Thème"))
        for theme_id, radio in self.theme_radios.items():
            radio.setText(self.theme_name(self.themes[theme_id]))
        self.theme_note.setText(
            self.tr(
                "Tu pourras aussi créer ton propre thème : Affichage → Thème → Gérer les thèmes…"
            )
        )
        self.mode_page.setTitle(self.tr("Traduction en ligne ou locale ?"))
        self.online_radio.setText(self.tr("En ligne (conseillé si tu as internet)"))
        self.online_note.setText(
            self.tr(
                "Les phrases sont envoyées à Yandex, Google ou un autre moteur. Si internet "
                "est coupé ou si un moteur refuse, RuneCast passe au suivant, puis à la "
                "traduction locale."
            )
        )
        self.local_radio.setText(self.tr("100 % local"))
        self.local_note.setText(
            self.tr(
                "Tout est traduit sur ce PC : aucune phrase n'est envoyée sur internet. "
                "Internet ne sert qu'aux mises à jour et au téléchargement des modèles."
            )
        )
        self.model_page.setTitle(self.tr("Modèle de traduction locale"))
        self.model_intro.setText(
            self.tr(
                "Un modèle permet de traduire sans internet. La plupart des jeux Ren'Py "
                "sont en anglais : vers quelle langue veux-tu traduire ?"
            )
        )
        self.download_button.setText(self.tr("Télécharger maintenant"))
        self.cancel_button.setText(self.tr("Annuler"))
        self.summary_page.setTitle(self.tr("C'est prêt !"))
        self._update_model()
        self._update_summary()

    def _language_changed(self) -> None:
        """FR : la fenêtre principale change la langue, puis l'assistant se retraduit
             tout de suite (sans attendre l'avis de Qt, qui n'arrive qu'aux
             fenêtres déjà affichées).
        EN : the main window changes the language, then the wizard retranslates
             at once (without waiting for Qt's notice, which only reaches windows
             already shown).
        """
        self.language_chosen.emit(self.language_combo.currentData())
        self.retranslate()

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802 (nom imposé par Qt)
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslate()
        super().changeEvent(event)

    # ------------------------------------------------------------------
    # FR : Modèle / EN : Model
    # ------------------------------------------------------------------
    def _default_target(self) -> None:
        """FR : propose la langue de l'interface (ou le français). EN : propose the UI language."""
        code = resolve_language(self.language_combo.currentData(), QLocale.system().name())
        index = self.target_combo.findData(code if code != GAME_LANGUAGE else "fr")
        self.target_combo.setCurrentIndex(max(index, 0))

    def argos_entry(self, target: str) -> CatalogEntry | None:
        """FR : modèle Argos anglais → langue choisie. EN : Argos English → chosen language."""
        return next(
            (e for e in self.catalog if (e.from_code, e.to_code) == (GAME_LANGUAGE, target)), None
        )

    def model_installed(self, target: str) -> bool:
        if self.argos_entry(target) is not None:
            return (GAME_LANGUAGE, target) in self.models.installed()
        return self.nllb.installed()

    def _update_model(self) -> None:
        """FR : décrit le modèle conseillé. EN : describe the advised model."""
        target = self.target_combo.currentData()
        if target is None:
            return
        entry = self.argos_entry(target)
        name = keep_left_to_right(f"English → {language_name(target)}")
        if self.model_installed(target):
            text = self.tr("Modèle déjà installé : {model}.").format(model=name)
        elif entry is not None:
            text = self.tr("Modèle conseillé : {model} ({size}).").format(
                model=name, size=format_size(entry.size or 0)
            )
        else:
            text = self.tr(
                "Modèle conseillé : NLLB-200 ({size}), qui couvre cette langue. Sa licence "
                "(usage non commercial) te sera présentée avant le téléchargement."
            ).format(size=format_size(self.nllb.catalog.total_size))
        self.model_label.setText(text)
        self.download_button.setEnabled(self.task is None and not self.model_installed(target))

    def _show_progress(self, visible: bool) -> None:
        self.progress.setVisible(visible)
        self.cancel_button.setVisible(visible)
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)

    def download(self) -> None:
        """FR : télécharge le modèle conseillé, en arrière-plan. EN : download the advised model."""
        target = self.target_combo.currentData()
        entry = self.argos_entry(target)
        if entry is not None:
            work = lambda progress, cancelled: self.models.download_and_install(  # noqa: E731
                entry, progress, cancelled
            )
        else:
            if not self.license_date:
                if (
                    NllbLicenseDialog(self.nllb.catalog, self).exec()
                    != NllbLicenseDialog.DialogCode.Accepted
                ):
                    return
                self.license_date = datetime.now(UTC).isoformat(timespec="seconds")
                self.nllb_license_accepted.emit(self.license_date)
            work = lambda progress, cancelled: self.nllb.install(progress, cancelled)  # noqa: E731
        task = TaskThread(work, self)
        task.progress.connect(
            lambda done, total: self.progress.setValue(int(done * 1000 / total) if total else 0)
        )
        task.failed.connect(
            lambda error: self.model_label.setText(
                self.tr(
                    "Téléchargement interrompu : {reason}. Tu pourras réessayer dans "
                    "Paramètres → Modèles de traduction."
                ).format(reason=error)
            )
        )
        task.finished.connect(self._download_finished)
        self.task = task
        self._show_progress(True)
        self.download_button.setEnabled(False)
        task.start()

    def cancel_download(self) -> None:
        if self.task is not None:
            self.task.cancel()

    def _download_finished(self) -> None:
        self.task = None
        self._show_progress(False)
        if self.model_installed(self.target_combo.currentData()):
            self._update_model()
        else:
            self.download_button.setEnabled(True)

    # ------------------------------------------------------------------
    # FR : Fin / EN : End
    # ------------------------------------------------------------------
    def mode(self) -> str:
        return MODE_LOCAL if self.local_radio.isChecked() else MODE_ONLINE

    def _page_changed(self, _page_id: int) -> None:
        if self.currentPage() is self.summary_page:
            self._update_summary()

    def _update_summary(self) -> None:
        target = self.target_combo.currentData() or "fr"
        installed = self.model_installed(target)
        lines = [
            self.tr("Mode : {mode}").format(
                mode=self.tr("100 % local") if self.mode() == MODE_LOCAL else self.tr("en ligne")
            ),
            self.tr("Modèle local : {state}").format(
                state=self.tr("installé") if installed else self.tr("pas encore installé")
            ),
        ]
        if self.mode() == MODE_LOCAL and not installed:
            lines.append(
                self.tr(
                    "Attention : en mode local, il faut un modèle pour traduire. Tu pourras "
                    "l'installer dans Fichier → Paramètres → Modèles de traduction."
                )
            )
        lines.append(self.tr("Tout reste modifiable dans Fichier → Paramètres…"))
        self.summary_label.setText("\n\n".join(lines))

    def done(self, result: int) -> None:
        """FR : fermeture : le téléchargement en cours est arrêté proprement.

        EN : closing: the running download is stopped cleanly.
        """
        if self.task is not None:
            self.task.cancel()
            self.task.wait()
        super().done(result)
