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

"""Page « Traduction » / "Translation" page.

FR : Choix du mode de traduction, et essai de la chaîne complète :
       - « En ligne » : moteurs en ligne cochés, dans l'ordre, avec repli
         automatique vers le suivant, puis vers la traduction locale ;
       - « 100 % local » : tout est traduit sur ce PC, aucune phrase n'est
         envoyée sur internet (internet reste utilisé pour les mises à jour
         et le téléchargement des modèles).
     La page montre l'ordre réellement utilisé, et permet d'essayer : une
     ligne par phrase, « Traduire », et chaque ligne indique le moteur qui
     l'a traduite. Pour vérifier le repli : lancer un long essai, puis
     couper le Wi-Fi en cours de route.

EN : Choice of translation mode, and test of the whole chain: "Online"
     (checked online engines, in order, falling back to the next one, then
     to local translation) or "100 % local" (everything translated on this
     PC, no sentence sent over the internet; internet is still used for
     updates and model downloads). The page shows the order really used, and
     allows a test: one line per sentence, "Translate", and each line says
     which engine translated it. To check the fallback: start a long test,
     then cut the Wi-Fi along the way.
"""

from dataclasses import replace

from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from runecast.core.paths import AppPaths
from runecast.core.settings import Settings
from runecast.engines.benchmark import SAMPLE_LINES
from runecast.engines.chain import (
    FROM_CACHE,
    MODE_LOCAL,
    MODE_ONLINE,
    build_chain,
    translate_texts,
)
from runecast.engines.nllb import NLLB_CODES
from runecast.engines.online import (
    ENGINE_CLASSES,
    REASON_KEY,
    REASON_LIMIT,
    REASON_OFFLINE,
    REASON_SERVICE,
)
from runecast.ui.i18n import language_name
from runecast.ui.settings_base import SettingsPage
from runecast.ui.tasks import TaskThread


class TranslationPage(SettingsPage):
    """Page « Traduction » / "Translation" page."""

    def __init__(self, paths: AppPaths) -> None:
        super().__init__()
        self.setObjectName("translationPage")
        self.paths = paths
        self.settings = Settings()
        self.task: TaskThread | None = None

        self.mode_box = QGroupBox()
        self.online_radio = QRadioButton()
        self.local_radio = QRadioButton()
        self.modes = QButtonGroup(self)
        self.modes.addButton(self.online_radio)
        self.modes.addButton(self.local_radio)
        self.online_radio.toggled.connect(self._update_order)
        self.mode_note = QLabel()
        self.mode_note.setWordWrap(True)
        self.order_label = QLabel()
        self.order_label.setObjectName("orderLabel")
        self.order_label.setWordWrap(True)
        mode_layout = QVBoxLayout(self.mode_box)
        for widget in (self.online_radio, self.local_radio, self.mode_note, self.order_label):
            mode_layout.addWidget(widget)

        self.test_box = QGroupBox()
        self.source_combo = QComboBox()
        self.target_combo = QComboBox()
        for combo in (self.source_combo, self.target_combo):
            for code in sorted(NLLB_CODES):
                combo.addItem(language_name(code), code)
        self.source_combo.setCurrentIndex(self.source_combo.findData("en"))
        self.target_combo.setCurrentIndex(self.target_combo.findData("fr"))
        self.lines_edit = QPlainTextEdit()
        self.lines_edit.setObjectName("testLines")
        self.lines_edit.setMaximumHeight(90)
        self.sample_button = QPushButton()
        self.sample_button.clicked.connect(
            lambda: self.lines_edit.setPlainText("\n".join(SAMPLE_LINES * 4))
        )
        self.translate_button = QPushButton()
        self.translate_button.clicked.connect(self.start_test)
        self.stop_button = QPushButton()
        self.stop_button.clicked.connect(self.stop_test)
        self.stop_button.setEnabled(False)
        self.progress = QProgressBar()
        self.results = QTableWidget(0, 3)
        self.results.setObjectName("testResults")
        self.results.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results.verticalHeader().setVisible(False)
        header = self.results.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.summary = QLabel()
        self.summary.setObjectName("testSummary")
        self.summary.setWordWrap(True)
        languages = QHBoxLayout()
        languages.addWidget(self.source_combo)
        languages.addWidget(QLabel("→"))
        languages.addWidget(self.target_combo)
        languages.addStretch()
        for button in (self.sample_button, self.translate_button, self.stop_button):
            languages.addWidget(button)
        test_layout = QVBoxLayout(self.test_box)
        test_layout.addLayout(languages)
        test_layout.addWidget(self.lines_edit)
        test_layout.addWidget(self.progress)
        test_layout.addWidget(self.results, stretch=1)
        test_layout.addWidget(self.summary)

        layout = QVBoxLayout(self)
        layout.addWidget(self.mode_box)
        layout.addWidget(self.test_box, stretch=1)
        self.retranslate()

    def title(self) -> str:
        return self.tr("Traduction")

    def retranslate(self) -> None:
        self.mode_box.setTitle(self.tr("Mode de traduction"))
        self.online_radio.setText(
            self.tr("En ligne : moteurs en ligne, avec repli automatique vers le local")
        )
        self.local_radio.setText(self.tr("100 % local : aucune phrase n'est envoyée sur internet"))
        self.mode_note.setText(
            self.tr(
                "En mode local, internet ne sert plus qu'aux mises à jour de RuneCast et au "
                "téléchargement des modèles. Installe d'abord les modèles de tes langues "
                "(page « Modèles de traduction »)."
            )
        )
        self.test_box.setTitle(self.tr("Essai (une phrase par ligne)"))
        self.sample_button.setText(self.tr("Exemple"))
        self.translate_button.setText(self.tr("Traduire"))
        self.stop_button.setText(self.tr("Arrêter"))
        self.results.setHorizontalHeaderLabels(
            [self.tr("Original"), self.tr("Traduction"), self.tr("Moteur")]
        )
        self._update_order()

    def engine_name(self, engine_id: str) -> str:
        """FR : nom affiché d'un moteur. EN : display name of an engine."""
        if engine_id in ENGINE_CLASSES:
            return ENGINE_CLASSES[engine_id].info.name
        names = {
            "local": self.tr("Local (Argos)"),
            "nllb": self.tr("Local (NLLB-200)"),
            FROM_CACHE: self.tr("Cache"),
        }
        return names.get(engine_id, engine_id)

    def mode(self) -> str:
        return MODE_LOCAL if self.local_radio.isChecked() else MODE_ONLINE

    def _update_order(self) -> None:
        """FR : affiche l'ordre réellement utilisé. EN : show the order really used."""
        steps = []
        if self.mode() == MODE_ONLINE:
            steps = [
                self.engine_name(engine_id)
                for engine_id in self.settings.engine_order
                if engine_id in self.settings.engines_enabled
            ]
        steps += [self.engine_name("local"), self.engine_name("nllb")]
        self.order_label.setText(self.tr("Ordre utilisé : {order}").format(order=" → ".join(steps)))

    # ------------------------------------------------------------------
    # FR : Essai / EN : Test
    # ------------------------------------------------------------------
    def start_test(self) -> None:
        """FR : traduit les lignes avec la chaîne complète, en arrière-plan.

        EN : translate the lines with the whole chain, in the background.
        """
        lines = [line for line in self.lines_edit.toPlainText().splitlines() if line.strip()]
        if not lines or self.task is not None:
            return
        source, target = self.source_combo.currentData(), self.target_combo.currentData()
        chain = build_chain(replace(self.settings, translation_mode=self.mode()), self.paths)
        self.results.setRowCount(0)
        self.summary.setText(self.tr("Traduction en cours…"))
        self.progress.setRange(0, len(lines))
        self.progress.setValue(0)

        def work(progress, cancelled):
            return chain, translate_texts(
                lines, source, target, chain, progress=progress, should_cancel=cancelled
            )

        task = TaskThread(work, self)
        task.progress.connect(lambda done, _total: self.progress.setValue(done))
        task.succeeded.connect(self._show_results)
        task.failed.connect(
            lambda error: self.summary.setText(self.tr("Échec : {reason}").format(reason=error))
        )
        task.finished.connect(self._finished)
        self.task = task
        self.translate_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        task.start()

    def stop_test(self) -> None:
        if self.task is not None:
            self.task.cancel()

    def _finished(self) -> None:
        self.task = None
        self.translate_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def _show_results(self, outcome) -> None:
        chain, results = outcome
        counts: dict[str, int] = {}
        for result in results:
            if result is None:
                continue
            row = self.results.rowCount()
            self.results.insertRow(row)
            text = (
                result.text
                if result.ok
                else self.tr("À vérifier : {text}").format(text=result.text)
            )
            for column, value in enumerate((result.source, text, self.engine_name(result.engine))):
                self.results.setItem(row, column, QTableWidgetItem(value))
            counts[result.engine] = counts.get(result.engine, 0) + 1
        details = ", ".join(f"{self.engine_name(e)} : {n}" for e, n in counts.items())
        lines = [
            self.tr("{count} ligne(s) traduite(s) — {details}").format(
                count=sum(counts.values()), details=details
            )
        ]
        reasons = {
            REASON_OFFLINE: self.tr("pas de connexion à internet"),
            REASON_KEY: self.tr("clé absente ou refusée"),
            REASON_LIMIT: self.tr("limite atteinte"),
            REASON_SERVICE: self.tr("service en panne"),
        }
        for event in chain.events:
            lines.append(
                self.tr("{engine} mis de côté ({reason}) : relais pris par le suivant.").format(
                    engine=self.engine_name(event.engine),
                    reason=reasons.get(event.reason, event.reason),
                )
            )
        self.summary.setText("\n".join(lines))

    def shutdown(self) -> None:
        if self.task is not None:
            self.task.cancel()
            self.task.wait()

    # ------------------------------------------------------------------
    # FR : Réglages / EN : Settings
    # ------------------------------------------------------------------
    def load(self, settings: Settings) -> None:
        self.settings = settings
        radio = self.local_radio if settings.translation_mode == MODE_LOCAL else self.online_radio
        radio.setChecked(True)
        self._update_order()

    def store(self, settings: Settings) -> None:
        settings.translation_mode = self.mode()

    def show_paths(self, paths: AppPaths) -> None:
        self.paths = paths
