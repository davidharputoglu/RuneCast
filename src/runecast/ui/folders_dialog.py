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

"""Fenêtre « Dossiers de RuneCast » / "RuneCast folders" window.

FR : Montre où RuneCast range ses fichiers et le mode utilisé, avec un bouton
     « Ouvrir » par dossier. Permet aussi de CHOISIR un autre dossier pour
     toutes les données, ou de revenir à l'emplacement standard. Le changement
     suit la méthode prudente de runecast/core/relocate.py : vérifier, copier,
     contrôler la copie, puis seulement proposer de supprimer l'ancien.

EN : Shows where RuneCast stores its files and the mode in use, with an "Open"
     button per folder. Also lets the user CHOOSE another folder for all the
     data, or go back to the standard location. The change follows the careful
     method of runecast/core/relocate.py: check, copy, verify the copy, and
     only then offer to delete the old one.
"""

import logging
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from runecast.core import relocate
from runecast.core.logs import setup_logging, stop_file_logging
from runecast.core.paths import (
    MODE_CUSTOM,
    AppPaths,
    single_folder_paths,
    system_paths,
    write_custom_root,
)
from runecast.ui.i18n import keep_left_to_right

logger = logging.getLogger(__name__)


def open_folder(folder: Path) -> bool:
    """Ouvre un dossier dans l'explorateur / Open a folder in the file manager.

    FR : Le dossier est créé s'il n'existe pas encore. Renvoie True si le
         système a accepté de l'ouvrir.
    EN : The folder is created if it does not exist yet. Returns True if the
         system agreed to open it.
    """
    folder.mkdir(parents=True, exist_ok=True)
    return QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))


class FoldersDialog(QDialog):
    """Fenêtre « Dossiers de RuneCast » / "RuneCast folders" window."""

    # FR : signal envoyé quand les données ont changé de dossier.
    # EN : signal sent when the data moved to another folder.
    paths_changed = Signal(object)

    def __init__(self, paths: AppPaths, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("foldersDialog")
        self.setWindowTitle(self.tr("Dossiers de RuneCast"))
        self.paths = paths

        self.mode_label = QLabel()
        self.mode_label.setObjectName("modeLabel")
        self.mode_label.setWordWrap(True)

        # FR : Une ligne par dossier : description, chemin, bouton « Ouvrir ».
        # EN : One row per folder: description, path, "Open" button.
        descriptions = {
            "config": self.tr("Réglages, thèmes, glossaires"),
            "data": self.tr("Modèles, sauvegardes, historique"),
            "cache": self.tr("Fichiers temporaires"),
            "logs": self.tr("Journaux (logs)"),
        }
        grid = QGridLayout()
        self.path_labels: dict[str, QLabel] = {}
        self.open_buttons: dict[str, QPushButton] = {}
        for row, name in enumerate(paths.folders()):
            path_label = QLabel()
            path_label.setTextFormat(Qt.TextFormat.PlainText)
            # FR : le chemin peut être sélectionné et copié. EN : the path can be copied.
            path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            button = QPushButton(self.tr("Ouvrir"))
            button.clicked.connect(
                lambda _checked=False, n=name: open_folder(self.paths.folders()[n])
            )
            grid.addWidget(QLabel(descriptions[name]), row, 0)
            grid.addWidget(path_label, row, 1)
            grid.addWidget(button, row, 2)
            self.path_labels[name] = path_label
            self.open_buttons[name] = button
        grid.setColumnStretch(1, 1)

        # FR : Boutons pour changer d'emplacement (absents en mode portable,
        #      où les données doivent rester à côté de l'application).
        # EN : Buttons to change location (absent in portable mode, where the
        #      data must stay next to the application).
        self.change_button = QPushButton(self.tr("Choisir un autre dossier…"))
        self.change_button.clicked.connect(self.choose_folder)
        self.reset_button = QPushButton(self.tr("Revenir à l'emplacement standard"))
        self.reset_button.clicked.connect(self.reset_to_standard)
        location_row = QHBoxLayout()
        location_row.addWidget(self.change_button)
        location_row.addWidget(self.reset_button)
        location_row.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText(self.tr("Fermer"))
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.mode_label)
        layout.addLayout(grid)
        layout.addLayout(location_row)
        layout.addWidget(buttons)
        self.setMinimumWidth(680)
        self._refresh()

    # ------------------------------------------------------------------
    # FR : Affichage / EN : Display
    # ------------------------------------------------------------------
    def _refresh(self) -> None:
        """FR : met à jour les textes et les boutons. EN : update texts and buttons."""
        if self.paths.portable:
            text = self.tr("Mode portable : toutes les données restent à côté de l'application.")
        elif self.paths.mode == MODE_CUSTOM:
            text = self.tr("Dossier choisi : {folder}").format(
                folder=keep_left_to_right(self.paths.root)
            )
        else:
            text = self.tr("Emplacement standard du système.")
        self.mode_label.setText(text)
        for name, folder in self.paths.folders().items():
            self.path_labels[name].setText(str(folder))
        self.change_button.setVisible(not self.paths.portable)
        self.reset_button.setVisible(self.paths.mode == MODE_CUSTOM)

    # ------------------------------------------------------------------
    # FR : Changement d'emplacement / EN : Location change
    # ------------------------------------------------------------------
    def choose_folder(self) -> None:
        """FR : l'utilisateur choisit un nouveau dossier. EN : user picks a new folder."""
        chosen = QFileDialog.getExistingDirectory(
            self, self.tr("Choisir le dossier des données de RuneCast"), str(Path.home())
        )
        if chosen:
            self.move_data(single_folder_paths(Path(chosen), MODE_CUSTOM))

    def reset_to_standard(self) -> None:
        """FR : retour à l'emplacement standard. EN : back to the standard location."""
        self.move_data(system_paths())

    def problem_text(self, problem: str) -> str:
        """FR : phrase expliquant un problème de dossier. EN : sentence for a folder problem."""
        texts = {
            relocate.PROBLEM_SAME: self.tr("RuneCast utilise déjà cet emplacement."),
            relocate.PROBLEM_OVERLAP: self.tr(
                "Le dossier choisi se mélange avec les dossiers actuels de RuneCast. "
                "Choisis un dossier séparé."
            ),
            relocate.PROBLEM_NOT_A_FOLDER: self.tr("Le chemin choisi n'est pas un dossier."),
            relocate.PROBLEM_NOT_EMPTY: self.tr(
                "Le dossier choisi n'est pas vide. Choisis un dossier vide "
                "(tu peux en créer un nouveau dans la fenêtre de choix)."
            ),
            relocate.PROBLEM_NOT_WRITABLE: self.tr(
                "RuneCast ne peut pas écrire dans le dossier choisi."
            ),
        }
        return texts[problem]

    def move_data(self, target: AppPaths) -> bool:
        """Déplace les données vers « target » / Move the data to "target".

        FR : Renvoie True si RuneCast utilise maintenant le nouvel emplacement.
        EN : Returns True if RuneCast now uses the new location.
        """
        problem = relocate.check_destination(target, self.paths)
        if problem:
            QMessageBox.warning(self, self.tr("Dossier impossible"), self.problem_text(problem))
            return False

        # FR : Le dossier contient déjà des données RuneCast : on propose de
        #      les utiliser telles quelles, sans rien copier ni supprimer.
        # EN : The folder already holds RuneCast data: offer to use it as is,
        #      without copying or deleting anything.
        if relocate.has_runecast_data(target):
            answer = QMessageBox.question(
                self,
                self.tr("Données déjà présentes"),
                self.tr(
                    "Ce dossier contient déjà des données RuneCast.\n\n"
                    "Les utiliser ? Tes données actuelles ne seront ni copiées "
                    "ni supprimées."
                ),
            )
            if answer != QMessageBox.StandardButton.Yes:
                return False
            self._switch_to(target)
            return True

        plan = relocate.plan_copy(self.paths, target)
        if plan.conflicts:
            QMessageBox.warning(
                self,
                self.tr("Dossier impossible"),
                self.tr("Des fichiers existent déjà dans le dossier choisi."),
            )
            return False
        destination = target.root or target.config_dir
        if relocate.free_space(destination) < plan.total_bytes:
            QMessageBox.warning(
                self,
                self.tr("Place insuffisante"),
                self.tr("Il n'y a pas assez de place sur le disque choisi."),
            )
            return False

        answer = QMessageBox.question(
            self,
            self.tr("Déplacer les données"),
            self.tr(
                "RuneCast va copier {count} fichiers ({size}) vers :\n{folder}\n\n"
                "La copie sera vérifiée avant d'utiliser le nouveau dossier. Continuer ?"
            ).format(
                count=len(plan.files),
                size=relocate.human_size(plan.total_bytes),
                folder=keep_left_to_right(destination),
            ),
        )
        if answer != QMessageBox.StandardButton.Yes:
            return False

        # FR : le journal est fermé pendant la copie pour qu'il ne change pas en route.
        # EN : the log is closed during the copy so that it does not change meanwhile.
        old_paths = self.paths
        stop_file_logging()
        QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            report = relocate.copy_and_verify(plan)
        finally:
            QGuiApplication.restoreOverrideCursor()
        if not report.ok:
            setup_logging(old_paths.log_dir)
            logger.error("Déplacement annulé / Move cancelled: %s", report.errors)
            QMessageBox.critical(
                self,
                self.tr("Déplacement annulé"),
                self.tr(
                    "La copie n'a pas pu être vérifiée. RuneCast garde l'ancien "
                    "emplacement, et rien n'a été supprimé.\n\n{details}"
                ).format(details="\n".join(report.errors)),
            )
            return False

        self._switch_to(target)
        logger.info("Données copiées vers / Data copied to: %s", destination)

        # FR : Seulement maintenant, on PROPOSE de supprimer les anciens fichiers.
        # EN : Only now do we OFFER to delete the old files.
        answer = QMessageBox.question(
            self,
            self.tr("Supprimer les anciens fichiers ?"),
            self.tr(
                "La copie est terminée et vérifiée. RuneCast utilise maintenant le "
                "nouveau dossier.\n\nSupprimer les {count} anciens fichiers ? "
                "Si tu réponds Non, ils restent en place."
            ).format(count=len(report.copied)),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            relocate.delete_sources(report, old_paths)
        return True

    def _switch_to(self, target: AppPaths) -> None:
        """FR : utilise désormais « target ». EN : use "target" from now on."""
        write_custom_root(target.root if target.mode == MODE_CUSTOM else None)
        target.create()
        setup_logging(target.log_dir)
        logger.info("Nouvel emplacement / New location: %s", target.mode)
        self.paths = target
        self._refresh()
        self.paths_changed.emit(target)
