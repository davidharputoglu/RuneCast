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

"""Tests des dossiers dans l'interface / Folder tests in the interface.

FR : Vérifie la mémorisation de la fenêtre, la fenêtre « Dossiers de RuneCast »
     et le changement d'emplacement des données, de bout en bout. Les questions
     posées à l'utilisateur sont simulées (réponses automatiques).
EN : Checks that the window is remembered, the "RuneCast folders" window and
     the data location change, end to end. The questions asked to the user are
     simulated (automatic answers).
"""

from pathlib import Path

import pytest
from PySide6.QtWidgets import QFileDialog, QMessageBox

from runecast import __main__ as cli
from runecast.core import paths
from runecast.core.logs import stop_file_logging
from runecast.core.settings import Settings, load_settings
from runecast.ui import folders_dialog, main_window

YES = QMessageBox.StandardButton.Yes
NO = QMessageBox.StandardButton.No


@pytest.fixture(autouse=True)
def close_log_files():
    """FR : ferme le journal après chaque test (Windows refuse d'effacer un
    fichier ouvert). EN : close the log after each test (Windows refuses
    to delete an open file).
    """
    yield
    stop_file_logging()


def _answer(monkeypatch: pytest.MonkeyPatch, *answers: QMessageBox.StandardButton) -> list:
    """FR : simule les réponses de l'utilisateur, dans l'ordre.

    EN : simulate the user's answers, in order.
    """
    asked: list[str] = []
    queue = list(answers)

    def question(*args, **kwargs):
        asked.append(args[1])
        return queue.pop(0)

    monkeypatch.setattr(QMessageBox, "question", question)
    for name in ("warning", "critical", "information"):
        monkeypatch.setattr(QMessageBox, name, lambda *a, **k: asked.append(a[1]))
    return asked


def _fill(app_paths: paths.AppPaths) -> None:
    """FR : quelques fichiers RuneCast. EN : a few RuneCast files."""
    app_paths.create()
    app_paths.settings_file.write_text('{"theme": "sombre"}', encoding="utf-8")
    (app_paths.data_dir / "historique.db").write_text("historique", encoding="utf-8")


def test_window_size_and_position_are_remembered(qtbot, custom_paths) -> None:
    """FR : la fenêtre se rouvre à la même taille. EN : window reopens at same size."""
    window = main_window.MainWindow(custom_paths, Settings())
    qtbot.addWidget(window)
    # FR : taille qui tient dans l'écran virtuel des tests (800 × 600).
    # EN : a size that fits the tests' virtual screen (800 × 600).
    window.resize(800, 520)
    window.show()
    window.close()
    saved = load_settings(custom_paths.settings_file)
    assert saved.window_geometry

    reopened = main_window.MainWindow(custom_paths, saved)
    qtbot.addWidget(reopened)
    assert (reopened.width(), reopened.height()) == (800, 520)


def test_folders_window_shows_the_folders(qtbot, custom_paths) -> None:
    """FR : la fenêtre « Dossiers » montre les 4 dossiers. EN : shows the 4 folders."""
    dialog = folders_dialog.FoldersDialog(custom_paths)
    qtbot.addWidget(dialog)
    for name, folder in custom_paths.folders().items():
        assert dialog.path_labels[name].text() == str(folder)
    assert str(custom_paths.root) in dialog.mode_label.text()


def test_portable_mode_hides_location_buttons(qtbot, tmp_path) -> None:
    """FR : en mode portable, on ne peut pas changer d'emplacement.

    EN : in portable mode, the location cannot be changed.
    """
    portable = paths.single_folder_paths(tmp_path / "portable", paths.MODE_PORTABLE)
    dialog = folders_dialog.FoldersDialog(portable)
    qtbot.addWidget(dialog)
    assert not dialog.change_button.isVisibleTo(dialog)
    assert not dialog.reset_button.isVisibleTo(dialog)


def test_move_data_copies_verifies_then_deletes_on_request(
    qtbot, monkeypatch, standard_like_paths, custom_paths
) -> None:
    """FR : changement d'emplacement complet, avec suppression acceptée.

    EN : full location change, with deletion accepted.
    """
    _fill(standard_like_paths)
    window = main_window.MainWindow(standard_like_paths, Settings())
    qtbot.addWidget(window)
    dialog = folders_dialog.FoldersDialog(standard_like_paths, window)
    qtbot.addWidget(dialog)
    dialog.paths_changed.connect(window.use_paths)
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *a, **k: str(custom_paths.root))
    asked = _answer(monkeypatch, YES, YES)  # FR : copier ? oui ; supprimer ? oui

    dialog.choose_folder()

    assert len(asked) == 2
    assert window.paths.mode == paths.MODE_CUSTOM
    assert window.paths.root == custom_paths.root
    assert window.settings.theme == "sombre"
    assert (custom_paths.data_dir / "historique.db").read_text(encoding="utf-8") == "historique"
    assert paths.read_custom_root() == custom_paths.root
    assert not standard_like_paths.settings_file.exists()


def test_old_files_are_kept_when_user_says_no(
    qtbot, monkeypatch, standard_like_paths, custom_paths
) -> None:
    """FR : si l'utilisateur refuse la suppression, les anciens fichiers restent.

    EN : if the user declines the deletion, the old files stay.
    """
    _fill(standard_like_paths)
    dialog = folders_dialog.FoldersDialog(standard_like_paths)
    qtbot.addWidget(dialog)
    _answer(monkeypatch, YES, NO)
    assert dialog.move_data(custom_paths)
    assert standard_like_paths.settings_file.is_file()
    assert custom_paths.settings_file.is_file()


def test_non_empty_folder_is_refused_with_a_message(
    qtbot, monkeypatch, standard_like_paths, custom_paths
) -> None:
    """FR : dossier non vide : message, et rien ne bouge. EN : refused, nothing moves."""
    _fill(standard_like_paths)
    custom_paths.root.mkdir(parents=True)
    (custom_paths.root / "autre-chose.txt").write_text("x", encoding="utf-8")
    dialog = folders_dialog.FoldersDialog(standard_like_paths)
    qtbot.addWidget(dialog)
    asked = _answer(monkeypatch)
    assert not dialog.move_data(custom_paths)
    assert asked == ["Dossier impossible"]
    assert dialog.paths == standard_like_paths


def test_existing_runecast_folder_can_be_reused(
    qtbot, monkeypatch, standard_like_paths, custom_paths
) -> None:
    """FR : un dossier RuneCast existant est réutilisé sans copie ni suppression.

    EN : an existing RuneCast folder is reused without copying or deleting.
    """
    _fill(standard_like_paths)
    _fill(custom_paths)
    dialog = folders_dialog.FoldersDialog(standard_like_paths)
    qtbot.addWidget(dialog)
    asked = _answer(monkeypatch, YES)
    assert dialog.move_data(custom_paths)
    assert asked == ["Données déjà présentes"]
    assert standard_like_paths.settings_file.is_file()
    assert dialog.paths.root == custom_paths.root


def test_back_to_standard_location(qtbot, monkeypatch, standard_like_paths, custom_paths) -> None:
    """FR : retour à l'emplacement standard. EN : back to the standard location."""
    _fill(custom_paths)
    paths.write_custom_root(custom_paths.root)
    dialog = folders_dialog.FoldersDialog(custom_paths)
    qtbot.addWidget(dialog)
    _answer(monkeypatch, YES, YES)
    assert dialog.move_data(standard_like_paths)
    assert paths.read_custom_root() is None
    assert standard_like_paths.settings_file.is_file()
    assert not custom_paths.settings_file.exists()


def test_command_line_paths_option(capsys) -> None:
    """FR : « runecast --paths » affiche les dossiers. EN : --paths prints the folders."""
    assert cli.main(["--paths", "--portable"]) == 0
    printed = capsys.readouterr().out
    assert "Mode : portable" in printed
    assert str(Path(paths.application_folder() / paths.DEV_PORTABLE_FOLDER)) in printed
