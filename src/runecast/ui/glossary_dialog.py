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

"""Fenêtre « Glossaires » / "Glossaries" window.

FR : Outils → Glossaires… Un glossaire par jeu (et par paire de langues) :
       - tableau modifiable : terme d'origine, traduction imposée, note,
         « respecter la casse » ;
       - importer et exporter en CSV (Excel, LibreOffice…) ;
       - « Traduire et contrôler » : traduit des phrases d'essai avec le
         glossaire et affiche le rapport de contrôle (chaque terme imposé
         doit apparaître, identique, dans chaque traduction).
     Les jeux (étapes 21 et 28) utiliseront ces glossaires.

EN : Tools → Glossaries… One glossary per game (and per language pair):
     editable table (original term, imposed translation, note, "match
     case"); CSV import and export (Excel, LibreOffice…); "Translate and
     check": translates test sentences with the glossary and shows the
     control report (each imposed term must appear, identical, in each
     translation). Games (steps 21 and 28) will use these glossaries.
"""

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from runecast.core.glossary import (
    Glossary,
    GlossaryEntry,
    GlossaryError,
    delete_glossary,
    glossary_folder,
    load_glossaries,
    new_glossary,
    read_csv,
    save_glossary,
)
from runecast.engines.chain import EngineChain, translate_texts
from runecast.engines.nllb import NLLB_CODES
from runecast.ui.i18n import keep_left_to_right, language_name
from runecast.ui.tasks import TaskThread

# FR : Colonnes du tableau. EN : Table columns.
COLUMN_SOURCE, COLUMN_TARGET, COLUMN_NOTE, COLUMN_CASE = range(4)


class GlossaryDialog(QDialog):
    """Fenêtre « Glossaires » / "Glossaries" window."""

    def __init__(
        self,
        config_dir: Path,
        make_chain: Callable[[], EngineChain] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("glossaryDialog")
        self.folder = glossary_folder(config_dir)
        self.make_chain = make_chain
        self.glossaries: dict[str, Glossary] = load_glossaries(self.folder)
        self.current: Glossary | None = None
        self.dirty = False
        self._loading = False
        self.task: TaskThread | None = None

        # FR : 1. Liste des glossaires. EN : 1. Glossary list.
        self.glossary_list = QListWidget()
        self.glossary_list.setObjectName("glossaryList")
        self.glossary_list.setFixedWidth(220)
        self.glossary_list.currentItemChanged.connect(self._on_selection)
        self.new_button = QPushButton()
        self.new_button.clicked.connect(self.create)
        self.rename_button = QPushButton()
        self.rename_button.clicked.connect(self.rename)
        self.delete_button = QPushButton()
        self.delete_button.clicked.connect(self.delete)
        left = QVBoxLayout()
        left.addWidget(self.glossary_list, stretch=1)
        for button in (self.new_button, self.rename_button, self.delete_button):
            left.addWidget(button)

        # FR : 2. Langues et termes. EN : 2. Languages and terms.
        self.source_combo = QComboBox()
        self.target_combo = QComboBox()
        for combo in (self.source_combo, self.target_combo):
            for code in sorted(NLLB_CODES):
                combo.addItem(language_name(code), code)
            combo.currentIndexChanged.connect(self._mark_dirty)
        self.languages_label = QLabel()
        languages = QHBoxLayout()
        languages.addWidget(self.languages_label)
        languages.addWidget(self.source_combo)
        languages.addWidget(QLabel("→"))
        languages.addWidget(self.target_combo)
        languages.addStretch()

        self.table = QTableWidget(0, 4)
        self.table.setObjectName("termsTable")
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        header = self.table.horizontalHeader()
        for column in (COLUMN_SOURCE, COLUMN_TARGET, COLUMN_NOTE):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COLUMN_CASE, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemChanged.connect(self._mark_dirty)
        self.add_row_button = QPushButton()
        self.add_row_button.clicked.connect(lambda: self.add_row(GlossaryEntry("", "")))
        self.remove_row_button = QPushButton()
        self.remove_row_button.clicked.connect(self.remove_rows)
        self.import_button = QPushButton()
        self.import_button.clicked.connect(self.import_csv)
        self.export_button = QPushButton()
        self.export_button.clicked.connect(self.export_csv)
        table_buttons = QHBoxLayout()
        for button in (
            self.add_row_button,
            self.remove_row_button,
            self.import_button,
            self.export_button,
        ):
            table_buttons.addWidget(button)
        table_buttons.addStretch()

        # FR : 3. Contrôle. EN : 3. Check.
        self.check_box = QGroupBox()
        self.check_lines = QPlainTextEdit()
        self.check_lines.setObjectName("checkLines")
        self.check_lines.setMaximumHeight(70)
        self.check_button = QPushButton()
        self.check_button.clicked.connect(self.translate_and_check)
        self.check_button.setEnabled(make_chain is not None)
        self.report = QLabel()
        self.report.setObjectName("controlReport")
        self.report.setWordWrap(True)
        self.report.setTextFormat(Qt.TextFormat.PlainText)
        self.report.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        check_layout = QVBoxLayout(self.check_box)
        check_row = QHBoxLayout()
        check_row.addWidget(self.check_lines, stretch=1)
        check_row.addWidget(self.check_button)
        check_layout.addLayout(check_row)
        check_layout.addWidget(self.report)

        self.editor = QWidget()
        right = QVBoxLayout(self.editor)
        right.setContentsMargins(0, 0, 0, 0)
        right.addLayout(languages)
        right.addWidget(self.table, stretch=1)
        right.addLayout(table_buttons)
        right.addWidget(self.check_box)

        self.save_button = QPushButton()
        self.save_button.clicked.connect(self.save)
        self.close_button = QPushButton()
        self.close_button.clicked.connect(self.reject)
        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(self.save_button)
        bottom.addWidget(self.close_button)
        body = QHBoxLayout()
        body.addLayout(left)
        body.addWidget(self.editor, stretch=1)
        layout = QVBoxLayout(self)
        layout.addLayout(body, stretch=1)
        layout.addLayout(bottom)
        self.resize(940, 620)
        self.retranslate()
        self._fill_list()

    # ------------------------------------------------------------------
    # FR : Textes / EN : Texts
    # ------------------------------------------------------------------
    def retranslate(self) -> None:
        self.setWindowTitle(self.tr("Glossaires"))
        self.new_button.setText(self.tr("Nouveau…"))
        self.rename_button.setText(self.tr("Renommer…"))
        self.delete_button.setText(self.tr("Supprimer"))
        self.languages_label.setText(self.tr("Langues :"))
        self.table.setHorizontalHeaderLabels(
            [
                self.tr("Terme d'origine"),
                self.tr("Traduction imposée"),
                self.tr("Note"),
                self.tr("Respecter la casse"),
            ]
        )
        self.add_row_button.setText(self.tr("Ajouter un terme"))
        self.remove_row_button.setText(self.tr("Supprimer le terme"))
        self.import_button.setText(self.tr("Importer un CSV…"))
        self.export_button.setText(self.tr("Exporter en CSV…"))
        self.check_box.setTitle(self.tr("Contrôle (une phrase d'essai par ligne)"))
        self.check_button.setText(self.tr("Traduire et contrôler"))
        self.save_button.setText(self.tr("Enregistrer"))
        self.close_button.setText(self.tr("Fermer"))

    def label(self, glossary: Glossary) -> str:
        """FR : « Mon jeu (en → fr) ». EN : "My game (en → fr)"."""
        return keep_left_to_right(
            f"{glossary.name} ({glossary.source_lang} → {glossary.target_lang})"
        )

    # ------------------------------------------------------------------
    # FR : Liste / EN : List
    # ------------------------------------------------------------------
    def _fill_list(self, select: str | None = None) -> None:
        self._loading = True
        self.glossary_list.clear()
        for glossary in sorted(self.glossaries.values(), key=lambda g: g.name.casefold()):
            item = QListWidgetItem(self.label(glossary))
            item.setData(Qt.ItemDataRole.UserRole, glossary.glossary_id)
            self.glossary_list.addItem(item)
            if glossary.glossary_id == select:
                self.glossary_list.setCurrentItem(item)
        self._loading = False
        if self.glossary_list.currentItem() is None and self.glossary_list.count():
            self.glossary_list.setCurrentRow(0)
        self._show(self.current_id())

    def current_id(self) -> str | None:
        item = self.glossary_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _on_selection(self, current, previous) -> None:
        if self._loading:
            return
        if previous is not None and self.dirty and not self._handle_unsaved():
            self._loading = True
            self.glossary_list.setCurrentItem(previous)
            self._loading = False
            return
        self._show(self.current_id())

    def _show(self, glossary_id: str | None) -> None:
        """FR : affiche un glossaire dans l'éditeur. EN : show a glossary in the editor."""
        self.current = self.glossaries.get(glossary_id) if glossary_id else None
        self._loading = True
        self.table.setRowCount(0)
        if self.current is not None:
            for combo, code in (
                (self.source_combo, self.current.source_lang),
                (self.target_combo, self.current.target_lang),
            ):
                combo.setCurrentIndex(max(combo.findData(code), 0))
            for entry in self.current.entries:
                self.add_row(entry)
        self._loading = False
        self.dirty = False
        has = self.current is not None
        self.editor.setEnabled(has)
        for button in (self.rename_button, self.delete_button, self.save_button):
            button.setEnabled(has)
        self.report.setText("")

    def add_row(self, entry: GlossaryEntry) -> None:
        """FR : ajoute une ligne au tableau. EN : add a row to the table."""
        row = self.table.rowCount()
        loading = self._loading
        self._loading = True
        self.table.insertRow(row)
        for column, value in (
            (COLUMN_SOURCE, entry.source),
            (COLUMN_TARGET, entry.target),
            (COLUMN_NOTE, entry.note),
        ):
            self.table.setItem(row, column, QTableWidgetItem(value))
        case = QTableWidgetItem()
        case.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        case.setCheckState(
            Qt.CheckState.Checked if entry.case_sensitive else Qt.CheckState.Unchecked
        )
        self.table.setItem(row, COLUMN_CASE, case)
        self._loading = loading
        if not loading:
            self._mark_dirty()
            self.table.setCurrentCell(row, COLUMN_SOURCE)

    def remove_rows(self) -> None:
        """FR : supprime les termes choisis. EN : delete the chosen terms."""
        rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.table.removeRow(row)
        if rows:
            self._mark_dirty()

    def entries(self) -> list[GlossaryEntry]:
        """FR : termes du tableau (lignes vides ignorées). EN : table terms (empty rows skipped)."""
        result = []
        for row in range(self.table.rowCount()):
            cells = [self.table.item(row, c) for c in (COLUMN_SOURCE, COLUMN_TARGET, COLUMN_NOTE)]
            source, target, note = ((cell.text().strip() if cell else "") for cell in cells)
            if not source and not target:
                continue
            case = self.table.item(row, COLUMN_CASE)
            result.append(
                GlossaryEntry(
                    source,
                    target,
                    note,
                    case is not None and case.checkState() == Qt.CheckState.Checked,
                )
            )
        return result

    def edited(self) -> Glossary | None:
        """FR : le glossaire tel qu'il est à l'écran. EN : the glossary as on screen."""
        if self.current is None:
            return None
        return Glossary(
            self.current.glossary_id,
            self.current.name,
            self.source_combo.currentData(),
            self.target_combo.currentData(),
            self.entries(),
        )

    def _mark_dirty(self, *_args) -> None:
        if not self._loading:
            self.dirty = True

    # ------------------------------------------------------------------
    # FR : Actions / EN : Actions
    # ------------------------------------------------------------------
    def create(self) -> None:
        """FR : nouveau glossaire (un par jeu). EN : new glossary (one per game)."""
        if self.dirty and not self._handle_unsaved():
            return
        name, ok = QInputDialog.getText(
            self, self.tr("Nouveau glossaire"), self.tr("Nom du jeu ou du glossaire :")
        )
        if not ok or not name.strip():
            return
        source = self.current.source_lang if self.current else "en"
        target = self.current.target_lang if self.current else "fr"
        glossary = new_glossary(name, set(self.glossaries), source, target)
        save_glossary(glossary, self.folder)
        self.glossaries[glossary.glossary_id] = glossary
        self.dirty = False
        self._fill_list(glossary.glossary_id)

    def rename(self) -> None:
        if self.current is None:
            return
        name, ok = QInputDialog.getText(
            self, self.tr("Renommer le glossaire"), self.tr("Nouveau nom :"), text=self.current.name
        )
        if ok and name.strip():
            self.current.name = name.strip()
            self.save()

    def delete(self) -> None:
        if self.current is None:
            return
        answer = QMessageBox.question(
            self,
            self.tr("Supprimer le glossaire ?"),
            self.tr("Le glossaire « {name} » sera supprimé définitivement. Continuer ?").format(
                name=self.current.name
            ),
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        delete_glossary(self.current.glossary_id, self.folder)
        del self.glossaries[self.current.glossary_id]
        self.dirty = False
        self._fill_list()

    def save(self) -> bool:
        """FR : enregistre le glossaire affiché. EN : save the displayed glossary."""
        glossary = self.edited()
        if glossary is None:
            return False
        incomplete = [e for e in glossary.entries if not e.source or not e.target]
        if incomplete:
            QMessageBox.warning(
                self,
                self.tr("Termes incomplets"),
                self.tr(
                    "Chaque terme doit avoir sa traduction imposée ({count} incomplet(s))."
                ).format(count=len(incomplete)),
            )
            return False
        save_glossary(glossary, self.folder)
        self.glossaries[glossary.glossary_id] = glossary
        self.dirty = False
        self._fill_list(glossary.glossary_id)
        return True

    def import_csv(self) -> None:
        """FR : ajoute des termes depuis un fichier CSV. EN : add terms from a CSV file."""
        path, _filter = QFileDialog.getOpenFileName(
            self, self.tr("Importer un CSV"), str(Path.home()), self.tr("Fichiers CSV (*.csv)")
        )
        if not path:
            return
        data = Path(path).read_bytes()
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = data.decode("cp1252", errors="replace")
        try:
            imported = read_csv(text)
        except GlossaryError as error:
            QMessageBox.warning(self, self.tr("Import impossible"), str(error))
            return
        # FR : un terme déjà présent est remplacé par celui du fichier.
        # EN : a term already present is replaced by the file's one.
        known = {e.source.casefold(): e for e in self.entries()}
        for entry in imported:
            known[entry.source.casefold()] = entry
        self._loading = True
        self.table.setRowCount(0)
        for entry in known.values():
            self.add_row(entry)
        self._loading = False
        self._mark_dirty()
        QMessageBox.information(
            self,
            self.tr("Import terminé"),
            self.tr("{count} terme(s) importé(s). Pense à cliquer sur « Enregistrer ».").format(
                count=len(imported)
            ),
        )

    def export_csv(self) -> None:
        """FR : enregistre les termes dans un fichier CSV. EN : save the terms to a CSV file."""
        glossary = self.edited()
        if glossary is None:
            return
        path, _filter = QFileDialog.getSaveFileName(
            self,
            self.tr("Exporter en CSV"),
            str(Path.home() / f"{glossary.glossary_id}.csv"),
            self.tr("Fichiers CSV (*.csv)"),
        )
        if not path:
            return
        target = Path(path)
        if target.suffix.lower() != ".csv":
            target = target.with_name(target.name + ".csv")
        # FR : avec « BOM » UTF-8 : Excel affiche alors bien les accents.
        # EN : with a UTF-8 "BOM": Excel then shows accents correctly.
        target.write_text(glossary.to_csv(), encoding="utf-8-sig", newline="")

    def translate_and_check(self) -> None:
        """FR : traduit les phrases d'essai avec le glossaire, puis contrôle.

        EN : translate the test sentences with the glossary, then check.
        """
        glossary = self.edited()
        lines = [line for line in self.check_lines.toPlainText().splitlines() if line.strip()]
        if glossary is None or not lines or self.make_chain is None or self.task is not None:
            return
        chain = self.make_chain()
        self.report.setText(self.tr("Traduction en cours…"))

        def work(progress, cancelled):
            return translate_texts(
                lines,
                glossary.source_lang,
                glossary.target_lang,
                chain,
                glossary=glossary,
                should_cancel=cancelled,
            )

        task = TaskThread(work, self)
        task.succeeded.connect(lambda results: self._show_report(glossary, results))
        task.failed.connect(
            lambda error: self.report.setText(self.tr("Échec : {reason}").format(reason=error))
        )
        task.finished.connect(self._task_finished)
        self.task = task
        self.check_button.setEnabled(False)
        task.start()

    def _task_finished(self) -> None:
        self.task = None
        self.check_button.setEnabled(self.make_chain is not None)

    def _show_report(self, glossary: Glossary, results) -> None:
        """FR : affiche traductions et rapport de contrôle. EN : show translations and report."""
        lines = []
        problems = 0
        for result in results:
            if result is None:
                continue
            missing = glossary.check(result.source, result.text)
            flag = "✔" if result.ok and not missing else "✘"
            problems += flag == "✘"
            lines.append(f"{flag} {result.text}")
            for entry in missing:
                lines.append(
                    "   "
                    + self.tr("terme imposé absent : « {source} » → « {target} »").format(
                        source=entry.source, target=entry.target
                    )
                )
        summary = (
            self.tr("Rapport : tous les termes imposés sont respectés.")
            if problems == 0
            else self.tr("Rapport : {count} ligne(s) à vérifier.").format(count=problems)
        )
        self.report.setText("\n".join([*lines, summary]))

    # ------------------------------------------------------------------
    # FR : Fermeture / EN : Closing
    # ------------------------------------------------------------------
    def _handle_unsaved(self) -> bool:
        """FR : propose d'enregistrer. Renvoie False si l'utilisateur annule.

        EN : offer to save. Returns False if the user cancels.
        """
        if not self.dirty or self.current is None:
            return True
        answer = QMessageBox.question(
            self,
            self.tr("Modifications non enregistrées"),
            self.tr(
                "Le glossaire « {name} » a été modifié. Enregistrer les modifications ?"
            ).format(name=self.current.name),
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if answer == QMessageBox.StandardButton.Save:
            return self.save()
        if answer == QMessageBox.StandardButton.Discard:
            self.dirty = False
            return True
        return False

    def reject(self) -> None:
        if self._handle_unsaved():
            if self.task is not None:
                self.task.cancel()
                self.task.wait()
            super().reject()
