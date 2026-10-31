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

"""Page « Moteurs en ligne » / "Online engines" page.

FR : Page des Paramètres pour les moteurs de traduction en ligne :
       - liste des moteurs, à cocher, dans l'ordre où RuneCast les essaie
         (boutons « Monter » et « Descendre ») ;
       - pour le moteur choisi : clé et réglages (dossier Yandex Cloud,
         adresse LibreTranslate, région Microsoft), prix indicatif et
         estimation pour un jeu, avertissement pour les accès non officiels ;
       - bouton « Tester » : traduit une phrase pour de vrai avec ces réglages.
     Les clés sont rangées dans le trousseau sécurisé du système.

EN : Settings page for online translation engines: list of engines to check,
     in the order RuneCast tries them ("Up" and "Down" buttons); for the
     chosen engine: key and settings (Yandex Cloud folder, LibreTranslate
     address, Microsoft region), indicative price and estimate for a game,
     warning for unofficial accesses; "Test" button: really translates a
     sentence with these settings. Keys are stored in the system's secure
     keyring.
"""

from PySide6.QtCore import QLocale, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from runecast.core.paths import AppPaths
from runecast.core.secrets import KeyStore
from runecast.core.settings import Settings
from runecast.engines.online import (
    DEFAULT_ORDER,
    ENGINE_CLASSES,
    REASON_KEY,
    REASON_LIMIT,
    REASON_OFFLINE,
    OnlineError,
    create_engine,
    estimate_cost,
)
from runecast.ui.settings_base import SettingsPage
from runecast.ui.tasks import TaskThread

# FR : Phrase et taille d'exemple. EN : Sample sentence and size.
TEST_SENTENCE = "Hello, how are you today?"
GAME_CHARACTERS = 1_000_000  # FR : un jeu moyen / EN : an average game


def normalized_order(order: list[str]) -> list[str]:
    """FR : ordre enregistré, complété par les moteurs ajoutés depuis.

    EN : saved order, completed with engines added since.
    """
    known = [engine for engine in order if engine in ENGINE_CLASSES]
    return known + [engine for engine in DEFAULT_ORDER if engine not in known]


class OnlineEnginesPage(SettingsPage):
    """Page « Moteurs en ligne » / "Online engines" page."""

    def __init__(self, paths: AppPaths) -> None:
        super().__init__()
        self.setObjectName("onlineEnginesPage")
        self.paths = paths
        self.keys = KeyStore(paths.config_dir, portable=paths.portable)
        self.edited_keys: dict[str, str] = {}
        self.edited_options: dict[str, dict[str, str]] = {}
        self.task: TaskThread | None = None
        self._showing = ""

        self.explanation = QLabel()
        self.explanation.setWordWrap(True)
        self.engine_list = QListWidget()
        self.engine_list.setObjectName("engineList")
        self.engine_list.setFixedWidth(230)
        self.engine_list.currentRowChanged.connect(self._show_engine)
        self.up_button = QPushButton()
        self.up_button.clicked.connect(lambda: self.move(-1))
        self.down_button = QPushButton()
        self.down_button.clicked.connect(lambda: self.move(1))
        move_row = QHBoxLayout()
        move_row.addWidget(self.up_button)
        move_row.addWidget(self.down_button)
        left = QVBoxLayout()
        left.addWidget(self.engine_list)
        left.addLayout(move_row)

        self.details = QGroupBox()
        self.description = QLabel()
        self.description.setWordWrap(True)
        self.description.setOpenExternalLinks(True)
        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.textEdited.connect(self._key_edited)
        self.show_key = QCheckBox()
        self.show_key.toggled.connect(
            lambda shown: self.key_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if shown else QLineEdit.EchoMode.Password
            )
        )
        self.option_edits: dict[str, QLineEdit] = {}
        for name in ("folder_id", "url", "region"):
            edit = QLineEdit()
            edit.textEdited.connect(lambda text, n=name: self._option_edited(n, text))
            self.option_edits[name] = edit
        self.labels: dict[str, QLabel] = {
            name: QLabel() for name in ("key", "folder_id", "url", "region")
        }
        self.form = QFormLayout()
        key_row = QHBoxLayout()
        key_row.addWidget(self.key_edit, stretch=1)
        key_row.addWidget(self.show_key)
        self.form.addRow(self.labels["key"], key_row)
        for name, edit in self.option_edits.items():
            self.form.addRow(self.labels[name], edit)
        self.test_button = QPushButton()
        self.test_button.clicked.connect(self.test_engine)
        self.test_result = QLabel()
        self.test_result.setObjectName("testResult")
        self.test_result.setWordWrap(True)
        self.test_result.setTextFormat(Qt.TextFormat.PlainText)
        test_row = QHBoxLayout()
        test_row.addWidget(self.test_button)
        test_row.addWidget(self.test_result, stretch=1)
        details_layout = QVBoxLayout(self.details)
        details_layout.addWidget(self.description)
        details_layout.addLayout(self.form)
        details_layout.addLayout(test_row)
        details_layout.addStretch()

        self.keyring_note = QLabel()
        self.keyring_note.setWordWrap(True)
        body = QHBoxLayout()
        body.addLayout(left)
        body.addWidget(self.details, stretch=1)
        layout = QVBoxLayout(self)
        layout.addWidget(self.explanation)
        layout.addLayout(body, stretch=1)
        layout.addWidget(self.keyring_note)
        self.retranslate()

    # ------------------------------------------------------------------
    # FR : Textes / EN : Texts
    # ------------------------------------------------------------------
    def title(self) -> str:
        return self.tr("Moteurs en ligne")

    def engine_label(self, engine_id: str) -> str:
        """FR : nom affiché d'un moteur. EN : display name of an engine."""
        info = ENGINE_CLASSES[engine_id].info
        if info.unofficial:
            return self.tr("{name} (gratuit, non officiel)").format(name=info.name)
        if info.needs_key:
            return self.tr("{name} (clé)").format(name=info.name)
        return info.name

    def retranslate(self) -> None:
        self.explanation.setText(
            self.tr(
                "Les moteurs cochés sont utilisés dans l'ordre de la liste : si l'un ne "
                "répond pas (pas d'internet, limite atteinte, clé refusée), RuneCast passe "
                "au suivant, puis à la traduction locale."
            )
        )
        self.up_button.setText(self.tr("Monter"))
        self.down_button.setText(self.tr("Descendre"))
        self.show_key.setText(self.tr("Afficher"))
        self.labels["key"].setText(self.tr("Clé :"))
        self.labels["folder_id"].setText(self.tr("Identifiant du dossier :"))
        self.labels["url"].setText(self.tr("Adresse du serveur :"))
        self.labels["region"].setText(self.tr("Région Azure :"))
        self.option_edits["url"].setPlaceholderText("https://libretranslate.com")
        self.option_edits["region"].setPlaceholderText("westeurope")
        self.test_button.setText(self.tr("Tester"))
        self.keyring_note.setText(
            self.tr("Les clés sont rangées dans le trousseau sécurisé du système.")
            if self.keys.secure
            else self.tr(
                "Attention : pas de trousseau sécurisé ici (mode portable ou système sans "
                "trousseau) : les clés sont gardées dans un fichier du dossier des réglages."
            )
        )
        for row in range(self.engine_list.count()):
            item = self.engine_list.item(row)
            item.setText(self.engine_label(item.data(Qt.ItemDataRole.UserRole)))
        if self._showing:
            self._show_engine(self.engine_list.currentRow())

    # ------------------------------------------------------------------
    # FR : Liste des moteurs / EN : Engine list
    # ------------------------------------------------------------------
    def order(self) -> list[str]:
        """FR : moteurs dans l'ordre de la liste. EN : engines in list order."""
        return [
            self.engine_list.item(row).data(Qt.ItemDataRole.UserRole)
            for row in range(self.engine_list.count())
        ]

    def enabled(self) -> list[str]:
        """FR : moteurs cochés, dans l'ordre. EN : checked engines, in order."""
        return [
            self.engine_list.item(row).data(Qt.ItemDataRole.UserRole)
            for row in range(self.engine_list.count())
            if self.engine_list.item(row).checkState() == Qt.CheckState.Checked
        ]

    def current_engine(self) -> str:
        item = self.engine_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else ""

    def move(self, step: int) -> None:
        """FR : déplace le moteur choisi d'une place. EN : move the chosen engine by one."""
        row = self.engine_list.currentRow()
        target = row + step
        if row < 0 or not 0 <= target < self.engine_list.count():
            return
        item = self.engine_list.takeItem(row)
        self.engine_list.insertItem(target, item)
        self.engine_list.setCurrentRow(target)

    def _show_engine(self, row: int) -> None:
        """FR : affiche les réglages du moteur choisi. EN : show the chosen engine's settings."""
        if row < 0:
            return
        engine_id = self.engine_list.item(row).data(Qt.ItemDataRole.UserRole)
        self._showing = engine_id
        info = ENGINE_CLASSES[engine_id].info
        self.details.setTitle(info.name)
        self.description.setText(self.describe(engine_id))
        self.key_edit.setText(self.edited_keys.get(engine_id, ""))
        for name, edit in self.option_edits.items():
            edit.setText(self.edited_options.get(engine_id, {}).get(name, ""))
        for name, label in self.labels.items():
            visible = name in info.fields
            label.setVisible(visible)
            field = self.option_edits.get(name)
            for widget in (field,) if field else (self.key_edit, self.show_key):
                widget.setVisible(visible)
        self.test_result.setText("")
        self.up_button.setEnabled(row > 0)
        self.down_button.setEnabled(row < self.engine_list.count() - 1)

    def describe(self, engine_id: str) -> str:
        """FR : description d'un moteur (prix, avertissements, lien). EN : engine description."""
        info = ENGINE_CLASSES[engine_id].info
        locale = QLocale()
        parts = []
        if info.unofficial:
            parts.append(
                self.tr(
                    "Gratuit, sans compte. Accès NON OFFICIEL : le service peut le limiter "
                    "ou l'arrêter à tout moment ; RuneCast passera alors au moteur suivant."
                )
            )
        elif info.price_per_million is not None:
            parts.append(
                self.tr(
                    "Payant. Prix indicatif : environ {price} $ par million de caractères. "
                    "Un jeu moyen (environ 1 million de caractères) : environ {game} $."
                ).format(
                    price=locale.toString(info.price_per_million, "f", 2),
                    game=locale.toString(estimate_cost(info, GAME_CHARACTERS), "f", 2),
                )
            )
            if info.free_characters:
                parts.append(
                    self.tr("Part gratuite : {count} caractères par mois.").format(
                        count=locale.toString(info.free_characters)
                    )
                )
            parts.append(
                self.tr("Prix relevés en octobre 2026 : vérifie-les sur le site du service.")
            )
        else:
            parts.append(
                self.tr(
                    "Libre : utilise ton propre serveur LibreTranslate, ou une instance "
                    "publique (souvent avec une clé)."
                )
            )
        link = self.tr("Site du service")
        parts.append(f'<a href="{info.signup_url}">{link}</a>')
        return "<br>".join(parts)

    def _key_edited(self, text: str) -> None:
        self.edited_keys[self._showing] = text.strip()

    def _option_edited(self, name: str, text: str) -> None:
        self.edited_options.setdefault(self._showing, {})[name] = text.strip()

    # ------------------------------------------------------------------
    # FR : Tester / EN : Test
    # ------------------------------------------------------------------
    def test_engine(self) -> None:
        """FR : traduit une phrase avec le moteur choisi, en arrière-plan.

        EN : translate a sentence with the chosen engine, in the background.
        """
        engine_id = self.current_engine()
        if not engine_id or self.task is not None:
            return
        engine = create_engine(
            engine_id,
            self.edited_keys.get(engine_id, ""),
            dict(self.edited_options.get(engine_id, {})),
        )
        target = QLocale().name().split("_")[0]
        target = target if target not in ("en", "C") else "fr"

        def work(_progress, _cancelled):
            try:
                return engine.translate([TEST_SENTENCE], "en", target)[0]
            finally:
                engine.close()

        self.test_result.setText(self.tr("Essai en cours…"))
        self.test_button.setEnabled(False)
        task = TaskThread(work, self)
        task.succeeded.connect(
            lambda text: self.test_result.setText(
                self.tr("Ça marche : « {text} »").format(text=text)
            )
        )
        task.failed.connect(self._test_failed)
        task.finished.connect(self._test_finished)
        self.task = task
        task.start()

    def _test_failed(self, error: Exception) -> None:
        reasons = {
            REASON_OFFLINE: self.tr("pas de connexion à internet"),
            REASON_KEY: self.tr("clé absente ou refusée"),
            REASON_LIMIT: self.tr("limite atteinte (réessaie plus tard)"),
        }
        reason = reasons.get(getattr(error, "reason", ""), str(error))
        if isinstance(error, OnlineError) and error.reason not in reasons:
            reason = str(error)
        self.test_result.setText(self.tr("Échec : {reason}").format(reason=reason))

    def _test_finished(self) -> None:
        self.task = None
        self.test_button.setEnabled(True)

    def shutdown(self) -> None:
        if self.task is not None:
            self.task.wait()

    # ------------------------------------------------------------------
    # FR : Réglages / EN : Settings
    # ------------------------------------------------------------------
    def load(self, settings: Settings) -> None:
        self.engine_list.clear()
        self.edited_options = {k: dict(v) for k, v in settings.engine_options.items()}
        self.edited_keys = {}
        for engine_id in normalized_order(settings.engine_order):
            item = QListWidgetItem(self.engine_label(engine_id))
            item.setData(Qt.ItemDataRole.UserRole, engine_id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            checked = engine_id in settings.engines_enabled
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            self.engine_list.addItem(item)
            if (
                ENGINE_CLASSES[engine_id].info.needs_key
                or "key" in ENGINE_CLASSES[engine_id].info.fields
            ):
                self.edited_keys[engine_id] = self.keys.get(engine_id)
        self.engine_list.setCurrentRow(0)

    def store(self, settings: Settings) -> None:
        settings.engine_order = self.order()
        settings.engines_enabled = self.enabled()
        settings.engine_options = {
            k: dict(v) for k, v in self.edited_options.items() if any(v.values())
        }
        for engine_id, key in self.edited_keys.items():
            if key != self.keys.get(engine_id):
                self.keys.set(engine_id, key)

    def show_paths(self, paths: AppPaths) -> None:
        """FR : les données ont changé de dossier. EN : the data moved."""
        self.paths = paths
        self.keys = KeyStore(paths.config_dir, portable=paths.portable)
