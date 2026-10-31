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

"""Page « Modèles de traduction » / "Translation models" page.

FR : Page des Paramètres qui gère les modèles de traduction locale (sans
     internet) :
       - liste de tous les modèles du catalogue, avec une recherche par
         langue ; chaque modèle traduit dans un sens (English → Français) ;
       - « Télécharger et installer » (avec barre de progression et bouton
         « Annuler » ; un téléchargement coupé reprend où il s'était
         arrêté), « Supprimer » ;
       - pack hors-ligne : « Télécharger pour un autre PC… » enregistre le
         fichier du modèle dans un dossier (clé USB…), « Importer des
         fichiers… » l'installe sur un PC sans internet ;
       - « Essayer » : traduit une phrase avec les modèles installés, pour
         vérifier que tout marche, même Wi-Fi coupé ;
       - « Performance » : cœurs du processeur utilisés et largeur de
         recherche (rapide, équilibré, précis), avec un bouton « Mesurer la
         vitesse… » qui essaie chaque réglage sur ce PC et choisit le meilleur
         (étape 14).
     Les travaux longs tournent en arrière-plan : la fenêtre ne se fige pas.

EN : Settings page managing the local (offline) translation models: list of
     every catalogue model with a language search, each translating one way
     (English → Français); "Download and install" (with progress bar and
     "Cancel" button; an interrupted download resumes where it stopped),
     "Delete"; offline pack: "Download for another PC…" saves the model file
     into a folder (USB stick…), "Import files…" installs it on a PC without
     internet; "Try": translates a sentence with the installed models, to
     check everything works, even with Wi-Fi off; "Performance": processor
     cores used and search width (fast, balanced, accurate), with a "Measure
     the speed…" button that tries each setting on this PC and picks the best
     (step 14). Long jobs run in the background: the window never freezes.
"""

import logging
from pathlib import Path

from PySide6.QtCore import QLocale, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from runecast.core.paths import AppPaths
from runecast.core.settings import Settings
from runecast.engines.argos import PIVOT_LANGUAGE, LocalEngine, default_threads
from runecast.engines.benchmark import memory_growth, physical_cores, recommend, run_benchmark
from runecast.engines.models import (
    ARCHIVE_SUFFIX,
    CatalogEntry,
    ChecksumError,
    DownloadCancelled,
    ModelStore,
    load_catalog,
    models_folder,
)
from runecast.ui.i18n import format_size, keep_left_to_right, language_name
from runecast.ui.settings_base import SettingsPage
from runecast.ui.tasks import TaskThread

logger = logging.getLogger(__name__)

# FR : Colonnes du tableau. EN : Table columns.
COLUMN_DIRECTION, COLUMN_SIZE, COLUMN_STATE = range(3)


def model_store(paths: AppPaths) -> ModelStore:
    """FR : les modèles installés pour ces dossiers. EN : installed models for these folders."""
    return ModelStore(models_folder(paths.data_dir), paths.cache_dir / "downloads")


class ModelsPage(SettingsPage):
    """Page « Modèles de traduction » / "Translation models" page."""

    def __init__(self, paths: AppPaths) -> None:
        super().__init__()
        self.setObjectName("modelsPage")
        self.paths = paths
        self.models = model_store(paths)
        self.catalog: list[CatalogEntry] = load_catalog()
        self.engine = LocalEngine(self.models.packages)
        self.task: TaskThread | None = None

        self.explanation = QLabel()
        self.explanation.setWordWrap(True)
        self.search_edit = QLineEdit()
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._apply_filter)
        self.table = QTableWidget(0, 3)
        self.table.setObjectName("modelsTable")
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(COLUMN_DIRECTION, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COLUMN_SIZE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COLUMN_STATE, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._update_buttons)

        self.install_button = QPushButton()
        self.install_button.clicked.connect(self.install_selected)
        self.remove_button = QPushButton()
        self.remove_button.clicked.connect(self.remove_selected)
        self.export_button = QPushButton()
        self.export_button.clicked.connect(self.download_for_other_pc)
        self.import_button = QPushButton()
        self.import_button.clicked.connect(self.import_files)
        buttons = QHBoxLayout()
        for button in (
            self.install_button,
            self.remove_button,
            self.export_button,
            self.import_button,
        ):
            buttons.addWidget(button)
        buttons.addStretch()

        self.progress_label = QLabel()
        self.progress_bar = QProgressBar()
        self.cancel_button = QPushButton()
        self.cancel_button.clicked.connect(self.cancel)
        progress_row = QHBoxLayout()
        progress_row.addWidget(self.progress_label)
        progress_row.addWidget(self.progress_bar, stretch=1)
        progress_row.addWidget(self.cancel_button)
        self._show_progress(False)

        self.try_box = QGroupBox()
        self.try_from = QComboBox()
        self.try_to = QComboBox()
        self.try_text = QLineEdit()
        self.try_button = QPushButton()
        self.try_button.clicked.connect(self.try_translation)
        self.try_result = QLabel()
        self.try_result.setObjectName("tryResult")
        self.try_result.setWordWrap(True)
        self.try_result.setTextFormat(Qt.TextFormat.PlainText)
        self.try_result.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.arrow_label = QLabel("→")
        try_row = QHBoxLayout()
        try_row.addWidget(self.try_from)
        try_row.addWidget(self.arrow_label)
        try_row.addWidget(self.try_to)
        try_row.addWidget(self.try_text, stretch=1)
        try_row.addWidget(self.try_button)
        try_layout = QVBoxLayout(self.try_box)
        try_layout.addLayout(try_row)
        try_layout.addWidget(self.try_result)

        self.performance_box = QGroupBox()
        self.threads_label = QLabel()
        self.threads_combo = QComboBox()
        self.threads_combo.setObjectName("threadsCombo")
        self.beam_label = QLabel()
        self.beam_combo = QComboBox()
        self.beam_combo.setObjectName("beamCombo")
        self.measure_button = QPushButton()
        self.measure_button.clicked.connect(self.measure_speed)
        performance_row = QHBoxLayout(self.performance_box)
        performance_row.addWidget(self.threads_label)
        performance_row.addWidget(self.threads_combo)
        performance_row.addSpacing(12)
        performance_row.addWidget(self.beam_label)
        performance_row.addWidget(self.beam_combo)
        performance_row.addStretch()
        performance_row.addWidget(self.measure_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.explanation)
        layout.addWidget(self.search_edit)
        layout.addWidget(self.table, stretch=1)
        layout.addLayout(buttons)
        layout.addLayout(progress_row)
        layout.addWidget(self.try_box)
        layout.addWidget(self.performance_box)
        self.retranslate()

    # ------------------------------------------------------------------
    # FR : Textes et tableau / EN : Texts and table
    # ------------------------------------------------------------------
    def title(self) -> str:
        return self.tr("Modèles de traduction")

    def retranslate(self) -> None:
        self.explanation.setText(
            self.tr(
                "Les modèles traduisent sur ce PC, sans internet. Chacun traduit dans "
                "un seul sens. S'il n'y a pas de modèle direct, RuneCast passe par "
                "l'anglais : par exemple Français → English, puis English → Türkçe."
            )
        )
        self.search_edit.setPlaceholderText(self.tr("Rechercher une langue…"))
        self.table.setHorizontalHeaderLabels(
            [self.tr("Sens de traduction"), self.tr("Taille"), self.tr("État")]
        )
        self.install_button.setText(self.tr("Télécharger et installer"))
        self.remove_button.setText(self.tr("Supprimer"))
        self.export_button.setText(self.tr("Télécharger pour un autre PC…"))
        self.import_button.setText(self.tr("Importer des fichiers…"))
        self.cancel_button.setText(self.tr("Annuler"))
        self.try_box.setTitle(self.tr("Essayer"))
        self.try_text.setPlaceholderText(self.tr("Phrase à traduire"))
        self.try_button.setText(self.tr("Traduire"))
        self.performance_box.setTitle(self.tr("Performance"))
        self.threads_label.setText(self.tr("Cœurs utilisés :"))
        self.beam_label.setText(self.tr("Traduction :"))
        self.measure_button.setText(self.tr("Mesurer la vitesse…"))
        threads, beam = self.threads_combo.currentData(), self.beam_combo.currentData()
        self.threads_combo.clear()
        self.threads_combo.addItem(
            self.tr("Automatique ({count})").format(count=default_threads()), 0
        )
        for count in range(1, physical_cores() + 1):
            self.threads_combo.addItem(str(count), count)
        self.beam_combo.clear()
        self.beam_combo.addItem(self.tr("Rapide"), 1)
        self.beam_combo.addItem(self.tr("Équilibrée (conseillée)"), 2)
        self.beam_combo.addItem(self.tr("Précise (plus lente)"), 4)
        self._select_performance(threads if threads is not None else 0, beam or 2)
        self.refresh()

    @staticmethod
    def direction(from_code: str, to_code: str, from_name: str = "", to_name: str = "") -> str:
        """FR : « English → Français », toujours écrit de gauche à droite (sinon, en
             arabe, la flèche semblerait pointer dans le mauvais sens).
        EN : "English → Français", always written left to right (otherwise, in
             Arabic, the arrow would seem to point the wrong way).
        """
        source, target = language_name(from_code, from_name), language_name(to_code, to_name)
        return keep_left_to_right(f"{source} → {target}")

    def refresh(self) -> None:
        """FR : relit les modèles et remplit le tableau. EN : reload and fill the table."""
        installed = self.models.installed()
        selected = self.selected_entry()
        self.table.setRowCount(0)
        for entry in self.catalog:
            row = self.table.rowCount()
            self.table.insertRow(row)
            model = installed.get((entry.from_code, entry.to_code))
            name = QTableWidgetItem(
                self.direction(entry.from_code, entry.to_code, entry.from_name, entry.to_name)
            )
            name.setData(Qt.ItemDataRole.UserRole, entry)
            name.setToolTip(f"{entry.from_name} → {entry.to_name} ({entry.version})")
            size_value = model.size if model else entry.size
            size = QTableWidgetItem(format_size(size_value) if size_value else "—")
            state = QTableWidgetItem(self.tr("Installé") if model else "")
            for column, item in enumerate((name, size, state)):
                self.table.setItem(row, column, item)
            if entry == selected:
                self.table.selectRow(row)
        self._apply_filter()
        self._fill_try_languages(installed)
        self._update_buttons()

    def _apply_filter(self) -> None:
        """FR : n'affiche que les modèles qui correspondent à la recherche.

        EN : show only the models matching the search.
        """
        words = self.search_edit.text().strip().casefold()
        for row in range(self.table.rowCount()):
            entry: CatalogEntry = self.table.item(row, COLUMN_DIRECTION).data(
                Qt.ItemDataRole.UserRole
            )
            haystack = " ".join(
                [
                    self.table.item(row, COLUMN_DIRECTION).text(),
                    entry.from_name,
                    entry.to_name,
                    entry.from_code,
                    entry.to_code,
                ]
            ).casefold()
            self.table.setRowHidden(row, bool(words) and words not in haystack)

    def selected_entry(self) -> CatalogEntry | None:
        """FR : modèle choisi dans le tableau. EN : model chosen in the table."""
        rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if not rows:
            return None
        return self.table.item(rows[0].row(), COLUMN_DIRECTION).data(Qt.ItemDataRole.UserRole)

    def select(self, from_code: str, to_code: str) -> None:
        """FR : choisit un modèle dans le tableau. EN : select a model in the table."""
        for row in range(self.table.rowCount()):
            entry = self.table.item(row, COLUMN_DIRECTION).data(Qt.ItemDataRole.UserRole)
            if (entry.from_code, entry.to_code) == (from_code, to_code):
                self.table.selectRow(row)
                return

    def _is_installed(self, entry: CatalogEntry) -> bool:
        return (entry.from_code, entry.to_code) in self.models.installed()

    def _update_buttons(self) -> None:
        entry = self.selected_entry()
        busy = self.task is not None
        installed = entry is not None and self._is_installed(entry)
        self.install_button.setEnabled(entry is not None and not installed and not busy)
        self.remove_button.setEnabled(installed and not busy)
        self.export_button.setEnabled(entry is not None and not busy)
        self.import_button.setEnabled(not busy)
        self.try_button.setEnabled(not busy and self.try_from.count() > 0)
        self.measure_button.setEnabled(not busy and bool(self.models.installed()))

    def _fill_try_languages(self, installed) -> None:
        """FR : langues des modèles installés, pour « Essayer ». EN : languages for "Try"."""
        sources = sorted({key[0] for key in installed})
        targets = sorted({key[1] for key in installed})
        for combo, codes in ((self.try_from, sources), (self.try_to, targets)):
            current = combo.currentData()
            combo.clear()
            for code in codes:
                combo.addItem(language_name(code), code)
            index = combo.findData(current)
            if index >= 0:
                combo.setCurrentIndex(index)
        if self.try_from.currentData() == PIVOT_LANGUAGE and self.try_to.count() > 1:
            index = self.try_to.findData(PIVOT_LANGUAGE)
            if index == self.try_to.currentIndex():
                self.try_to.setCurrentIndex(0 if index != 0 else 1)
        has_models = bool(installed)
        for widget in (self.try_from, self.try_to, self.try_text):
            widget.setEnabled(has_models)
        if not has_models:
            self.try_result.setText(self.tr("Installe d'abord un modèle."))

    # ------------------------------------------------------------------
    # FR : Travaux en arrière-plan / EN : Background jobs
    # ------------------------------------------------------------------
    def _show_progress(self, visible: bool, text: str = "") -> None:
        self.progress_label.setText(text)
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, 100)
        for widget in (self.progress_label, self.progress_bar, self.cancel_button):
            widget.setVisible(visible)

    def _on_progress(self, done: int, total: int) -> None:
        if total > 0:
            self.progress_bar.setRange(0, 1000)
            self.progress_bar.setValue(int(done * 1000 / total))
            self.progress_bar.setFormat(f"{format_size(done)} / {format_size(total)}")
        else:
            self.progress_bar.setRange(0, 0)  # FR : taille inconnue / EN : unknown size

    def _start(self, work, text: str, on_success) -> TaskThread:
        """FR : lance un travail en arrière-plan. EN : start a background job."""
        task = TaskThread(work, self)
        task.progress.connect(self._on_progress)
        task.succeeded.connect(on_success)
        task.failed.connect(self._on_failure)
        task.finished.connect(self._on_finished)
        self.task = task
        self._show_progress(True, text)
        self._update_buttons()
        task.start()
        return task

    def _on_finished(self) -> None:
        self.task = None
        self._show_progress(False)
        self.refresh()

    def _on_failure(self, error: Exception) -> None:
        if isinstance(error, DownloadCancelled):
            return
        if isinstance(error, ChecksumError):
            message = self.tr(
                "Le fichier téléchargé est abîmé ou a été modifié : il a été refusé. "
                "Réessaie plus tard."
            )
        else:
            message = self.tr("L'opération a échoué :\n{details}").format(details=error)
        QMessageBox.warning(self, self.tr("Modèles de traduction"), message)

    def cancel(self) -> None:
        """FR : annule le travail en cours. EN : cancel the running job."""
        if self.task is not None:
            self.task.cancel()

    def shutdown(self) -> None:
        """FR : fermeture : arrête proprement le travail en cours et libère la mémoire.

        EN : closing: stop the running job cleanly and free the memory.
        """
        if self.task is not None:
            self.task.cancel()
            self.task.wait()
        self.engine.unload()

    # ------------------------------------------------------------------
    # FR : Actions / EN : Actions
    # ------------------------------------------------------------------
    def install_selected(self) -> None:
        """FR : télécharge et installe le modèle choisi. EN : download and install the selection."""
        entry = self.selected_entry()
        if entry is None:
            return
        name = self.direction(entry.from_code, entry.to_code, entry.from_name, entry.to_name)
        self._start(
            lambda progress, cancelled: self.models.download_and_install(
                entry, progress, cancelled
            ),
            self.tr("Téléchargement : {model}").format(model=name),
            lambda _model: None,
        )

    def remove_selected(self) -> None:
        """FR : supprime le modèle choisi (confirmé). EN : delete it (confirmed)."""
        entry = self.selected_entry()
        if entry is None or not self._is_installed(entry):
            return
        name = self.direction(entry.from_code, entry.to_code, entry.from_name, entry.to_name)
        answer = QMessageBox.question(
            self,
            self.tr("Supprimer le modèle ?"),
            self.tr(
                "Le modèle « {model} » sera supprimé de ce PC. Il pourra être "
                "téléchargé de nouveau. Continuer ?"
            ).format(model=name),
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.engine.unload()
        self.models.remove(entry.from_code, entry.to_code)
        self.refresh()

    def download_for_other_pc(self) -> None:
        """FR : enregistre le fichier du modèle dans un dossier (pack hors-ligne).

        EN : save the model file into a folder (offline pack).
        """
        entry = self.selected_entry()
        if entry is None:
            return
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Dossier où enregistrer le modèle (clé USB…)")
        )
        if not folder:
            return
        destination = Path(folder)
        name = self.direction(entry.from_code, entry.to_code, entry.from_name, entry.to_name)

        def saved(path: Path) -> None:
            QMessageBox.information(
                self,
                self.tr("Modèle enregistré"),
                self.tr(
                    "Fichier enregistré :\n{file}\n\nCopie-le sur l'autre PC, puis : "
                    "Paramètres → Modèles de traduction → Importer des fichiers…"
                ).format(file=keep_left_to_right(str(path))),
            )

        self._start(
            lambda progress, cancelled: self.models.download(
                entry, destination, progress, cancelled
            ),
            self.tr("Téléchargement : {model}").format(model=name),
            saved,
        )

    def import_files(self) -> None:
        """FR : installe des fichiers de modèles (pack hors-ligne). EN : install model files."""
        files, _filter = QFileDialog.getOpenFileNames(
            self,
            self.tr("Importer des modèles"),
            str(Path.home()),
            self.tr("Modèles Argos (*{suffix})").format(suffix=ARCHIVE_SUFFIX),
        )
        if not files:
            return
        paths = [Path(file) for file in files]
        self._start(
            lambda _progress, _cancelled: self.models.import_files(paths, self.catalog),
            self.tr("Installation…"),
            lambda models: QMessageBox.information(
                self,
                self.tr("Modèles importés"),
                self.tr("{count} modèle(s) installé(s).").format(count=len(models)),
            ),
        )

    def try_translation(self) -> None:
        """FR : traduit la phrase d'essai en arrière-plan. EN : translate the test sentence."""
        text = self.try_text.text().strip()
        source, target = self.try_from.currentData(), self.try_to.currentData()
        if not text or source is None or target is None:
            return
        if not self.engine.supports(source, target):
            self.try_result.setText(
                self.tr("Aucun modèle installé pour {direction}.").format(
                    direction=self.direction(source, target)
                )
            )
            return
        self.try_result.setText(self.tr("Traduction en cours…"))
        self._start(
            lambda _progress, _cancelled: self.engine.translate([text], source, target)[0],
            self.tr("Traduction en cours…"),
            self.try_result.setText,
        )

    def _select_performance(self, threads: int, beam: int) -> None:
        """FR : affiche des réglages de performance. EN : show performance settings."""
        index = self.threads_combo.findData(threads)
        self.threads_combo.setCurrentIndex(max(index, 0))
        index = self.beam_combo.findData(beam)
        self.beam_combo.setCurrentIndex(index if index >= 0 else self.beam_combo.findData(2))

    def benchmark_pair(self) -> tuple[str, str] | None:
        """FR : sens de traduction utilisé pour la mesure (anglais → français si
             possible, sinon le premier modèle installé).
        EN : direction used for the measure (English → French if possible,
             otherwise the first installed model).
        """
        installed = sorted(self.models.installed())
        if not installed:
            return None
        return ("en", "fr") if ("en", "fr") in installed else installed[0]

    def measure_speed(self) -> None:
        """FR : banc d'essai en arrière-plan, puis réglages conseillés choisis.

        EN : background benchmark, then recommended settings selected.
        """
        pair = self.benchmark_pair()
        if pair is None:
            return
        source, target = pair
        packages = self.models.packages

        def work(progress, cancelled):
            results = run_benchmark(
                lambda threads, beam: LocalEngine(packages, threads=threads, beam_size=beam),
                source,
                target,
                progress=progress,
                should_cancel=cancelled,
            )
            if cancelled() or not results:
                return None
            best = recommend(results)
            engine = LocalEngine(packages, threads=best.threads, beam_size=best.beam_size)
            growth = memory_growth(engine, source, target, rounds=2)
            return results, recommend(results, growth)

        self._start(work, self.tr("Mesure de la vitesse…"), self._show_measure)

    def _show_measure(self, outcome) -> None:
        """FR : affiche le résultat de la mesure. EN : show the measure's result."""
        if outcome is None:
            return
        results, advice = outcome
        chosen = next(
            r for r in results if (r.threads, r.beam_size) == (advice.threads, advice.beam_size)
        )
        self._select_performance(advice.threads, advice.beam_size)
        stable = self.tr("stable") if advice.memory_stable else self.tr("à surveiller")
        QMessageBox.information(
            self,
            self.tr("Mesure de la vitesse"),
            self.tr(
                "Réglages conseillés pour ce PC : {threads} cœur(s), traduction "
                "« {quality} ».\nVitesse : {speed} phrases par seconde. Mémoire : "
                "{memory} ({stable}).\n\nIls sont sélectionnés : clique sur « OK » "
                "ou « Appliquer » pour les garder."
            ).format(
                threads=advice.threads,
                quality=self.beam_combo.currentText(),
                speed=QLocale().toString(chosen.sentences_per_second, "f", 1),
                memory=format_size(int(chosen.memory_mb * 1024 * 1024)),
                stable=stable,
            ),
        )

    # ------------------------------------------------------------------
    # FR : Réglages / EN : Settings
    # ------------------------------------------------------------------
    def show_paths(self, paths: AppPaths) -> None:
        """FR : les données ont changé de dossier. EN : the data moved."""
        self.engine.unload()
        self.paths = paths
        self.models = model_store(paths)
        self.engine = LocalEngine(self.models.packages)
        self.refresh()

    def load(self, settings: Settings) -> None:
        self._select_performance(settings.local_threads, settings.local_beam_size)
        self.engine.configure(settings.local_threads or None, settings.local_beam_size)
        self.refresh()

    def store(self, settings: Settings) -> None:
        """FR : réglages de performance. EN : performance settings."""
        settings.local_threads = self.threads_combo.currentData()
        settings.local_beam_size = self.beam_combo.currentData()
        self.engine.configure(settings.local_threads or None, settings.local_beam_size)
