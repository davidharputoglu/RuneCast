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

"""Tests des thèmes personnels / Custom theme tests.

FR : Vérifie la création, l'enregistrement, le rechargement (après un
     redémarrage), l'import, l'export et la suppression des thèmes
     personnels, l'aperçu en direct et l'avertissement de lisibilité, et que
     les thèmes intégrés ne sont jamais modifiés. Les fenêtres de Qt qui
     attendent une réponse (questions, choix de fichier ou de couleur) sont
     remplacées par des réponses automatiques.
EN : Checks creating, saving, reloading (after a restart), importing,
     exporting and deleting custom themes, the live preview and the
     readability warning, and that built-in themes are never modified. Qt
     windows waiting for an answer (questions, file or colour choice) are
     replaced by automatic answers.
"""

import json
from pathlib import Path

import pytest
from PySide6.QtCore import QLocale
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QColorDialog, QFileDialog, QMessageBox

from runecast.core import themes
from runecast.core.settings import Settings, load_settings
from runecast.ui import main_window
from runecast.ui.i18n import LanguageManager
from runecast.ui.theme import THEME_PROPERTY, apply_theme
from runecast.ui.theme_editor import ThemeEditorDialog

BUILTIN = themes.builtin_themes()
YES = QMessageBox.StandardButton.Yes
NO = QMessageBox.StandardButton.No
SAVE = QMessageBox.StandardButton.Save
DISCARD = QMessageBox.StandardButton.Discard
CANCEL = QMessageBox.StandardButton.Cancel


@pytest.fixture(autouse=True)
def back_to_turquoise(qapp: QApplication):
    """FR : remet le thème Turquoise après chaque test. EN : restore Turquoise after each test."""
    yield
    apply_theme(qapp, BUILTIN[themes.DEFAULT_THEME])


@pytest.fixture
def folder(custom_paths) -> Path:
    """FR : dossier des thèmes personnels. EN : custom themes folder."""
    return themes.custom_themes_folder(custom_paths.config_dir)


def _custom(theme_id: str = "mon-theme", name: str = "Mon thème") -> themes.Theme:
    """FR : un thème personnel tiré de Turquoise. EN : a custom theme based on Turquoise."""
    return themes.Theme(id=theme_id, name=name, dark=True, colors=dict(BUILTIN["turquoise"].colors))


def _answers(monkeypatch: pytest.MonkeyPatch, *answers) -> list[str]:
    """FR : réponses automatiques aux questions ; renvoie les titres affichés.

    EN : automatic answers to questions; returns the titles shown.
    """
    queue = list(answers)
    shown: list[str] = []

    def question(_parent, title, *_args, **_kwargs):
        shown.append(title)
        return queue.pop(0)

    monkeypatch.setattr(QMessageBox, "question", question)
    for name in ("information", "warning"):
        monkeypatch.setattr(QMessageBox, name, lambda _p, title, *a, **k: shown.append(title))
    return shown


# ----------------------------------------------------------------------
# FR : Fonctions de base (sans fenêtre) / EN : Core functions (no window)
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    ("name", "taken", "expected"),
    [
        ("Mon Thème Été", set(), "mon-theme-ete"),
        ("Noir", {"noir"}, "noir-2"),
        ("Noir", {"noir", "noir-2"}, "noir-3"),
        ("سمة زرقاء", set(), "theme"),
        ("!!!", {"theme"}, "theme-2"),
    ],
)
def test_theme_identifier(name: str, taken: set[str], expected: str) -> None:
    """FR : identifiant fabriqué à partir du nom. EN : identifier built from the name."""
    theme_id = themes.make_theme_id(name, taken)
    assert theme_id == expected
    assert themes.ID_PATTERN.match(theme_id)


def test_custom_theme_is_saved_and_read_back(folder: Path) -> None:
    """FR : un thème enregistré est relu à l'identique. EN : a saved theme reads back the same."""
    theme = _custom()
    path = themes.save_custom_theme(theme, folder)
    assert path == folder / "mon-theme.json"
    assert not list(folder.glob("*.tmp"))
    assert themes.load_custom_themes(folder) == {"mon-theme": theme}


def test_all_themes_lists_builtin_first(custom_paths, folder: Path) -> None:
    """FR : thèmes intégrés d'abord, puis personnels. EN : built-in first, then custom."""
    themes.save_custom_theme(_custom(), folder)
    assert list(themes.all_themes(custom_paths.config_dir)) == [
        *themes.BUILTIN_THEME_IDS,
        "mon-theme",
    ]


def test_builtin_themes_are_protected(folder: Path) -> None:
    """FR : un thème intégré ne peut être ni écrasé ni supprimé.

    EN : a built-in theme can be neither overwritten nor deleted.
    """
    with pytest.raises(themes.ThemeError):
        themes.save_custom_theme(BUILTIN["noir"], folder)
    with pytest.raises(themes.ThemeError):
        themes.save_custom_theme(_custom(theme_id="noir"), folder)
    with pytest.raises(themes.ThemeError):
        themes.delete_custom_theme("clair", folder)
    assert themes.builtin_themes() == BUILTIN


def test_damaged_theme_file_is_skipped_but_kept(folder: Path) -> None:
    """FR : un fichier abîmé est ignoré, mais jamais supprimé.

    EN : a damaged file is skipped, but never deleted.
    """
    themes.save_custom_theme(_custom(), folder)
    broken = folder / "abime.json"
    broken.write_text("{ pas du json", encoding="utf-8")
    same_as_builtin = folder / "faux-noir.json"
    same_as_builtin.write_text(json.dumps(themes.theme_to_dict(BUILTIN["noir"])), encoding="utf-8")
    assert list(themes.load_custom_themes(folder)) == ["mon-theme"]
    assert broken.is_file() and same_as_builtin.is_file()


def test_delete_custom_theme(folder: Path) -> None:
    """FR : suppression d'un thème personnel. EN : deleting a custom theme."""
    themes.save_custom_theme(_custom(), folder)
    themes.delete_custom_theme("mon-theme", folder)
    assert themes.load_custom_themes(folder) == {}


def test_import_renames_a_taken_identifier(tmp_path: Path, folder: Path) -> None:
    """FR : un thème importé dont l'identifiant est déjà pris en reçoit un autre ;
         le fichier d'origine n'est pas modifié.
    EN : an imported theme whose identifier is taken gets another one; the
         original file is not modified.
    """
    themes.save_custom_theme(_custom(), folder)
    source = tmp_path / "partage.json"
    themes.export_theme(_custom(name="Thème d'un ami"), source)
    before = source.read_bytes()

    imported = themes.import_theme(source, folder, {*themes.BUILTIN_THEME_IDS, "mon-theme"})
    assert imported.id == "theme-d-un-ami"
    assert imported.name == "Thème d'un ami"
    assert (folder / "theme-d-un-ami.json").is_file()
    assert (folder / "mon-theme.json").is_file()
    assert source.read_bytes() == before


def test_import_of_a_builtin_copy_never_replaces_it(tmp_path: Path, folder: Path) -> None:
    """FR : importer une copie de « Noir » crée un thème personnel à part.

    EN : importing a copy of "Black" creates a separate custom theme.
    """
    source = tmp_path / "noir.json"
    themes.export_theme(BUILTIN["noir"], source)
    imported = themes.import_theme(source, folder, set(themes.BUILTIN_THEME_IDS))
    assert imported.id == "noir-2" and not imported.builtin
    assert themes.builtin_themes()["noir"] == BUILTIN["noir"]


def test_invalid_import_is_refused(tmp_path: Path, folder: Path) -> None:
    """FR : un fichier incorrect est refusé et rien n'est ajouté.

    EN : a wrong file is refused and nothing is added.
    """
    source = tmp_path / "faux.json"
    source.write_text(json.dumps({"format": 1, "id": "faux"}), encoding="utf-8")
    with pytest.raises(themes.ThemeError):
        themes.import_theme(source, folder, set())
    assert themes.load_custom_themes(folder) == {}


def test_export_then_import_gives_the_same_theme(tmp_path: Path, folder: Path) -> None:
    """FR : exporter puis importer redonne le même thème. EN : export then import round-trips."""
    theme = _custom()
    target = tmp_path / "export.json"
    themes.export_theme(theme, target)
    assert themes.import_theme(target, folder, set()) == theme


def test_readability_problems() -> None:
    """FR : texte de la même couleur que le fond : signalé.

    EN : text of the same colour as the background: flagged.
    """
    for theme in BUILTIN.values():
        assert themes.readability_problems(theme.colors) == []
    colors = dict(BUILTIN["clair"].colors)
    colors["text"] = colors["window"]
    flagged = {(fg, bg) for fg, bg, _ratio in themes.readability_problems(colors)}
    assert ("text", "window") in flagged


# ----------------------------------------------------------------------
# FR : Fenêtre « Thèmes personnels » / EN : "Custom themes" window
# ----------------------------------------------------------------------
@pytest.fixture
def editor(qtbot, custom_paths) -> ThemeEditorDialog:
    """FR : éditeur ouvert sur le thème Turquoise. EN : editor opened on Turquoise."""
    dialog = ThemeEditorDialog(custom_paths.config_dir, "turquoise")
    qtbot.addWidget(dialog)
    return dialog


def test_builtin_theme_is_read_only_in_editor(editor: ThemeEditorDialog) -> None:
    """FR : un thème intégré s'affiche, mais ne peut pas être modifié.

    EN : a built-in theme is displayed but cannot be changed.
    """
    assert editor.current.id == "turquoise"
    assert editor.theme_combo.currentText() == "Turquoise (intégré)"
    assert not editor.builtin_note.isHidden()
    assert not editor.name_edit.isEnabled()
    assert not editor.save_button.isEnabled()
    assert not editor.delete_button.isEnabled()
    assert not any(edit.isEnabled() for edit in editor.hex_edits.values())
    assert editor.duplicate_button.isEnabled() and editor.use_button.isEnabled()
    assert editor.readability_label.text() == "Lisibilité : bonne"


def test_duplicate_creates_an_editable_theme(editor: ThemeEditorDialog, qtbot, folder) -> None:
    """FR : « Dupliquer » crée et enregistre aussitôt un thème modifiable.

    EN : "Duplicate" creates and saves an editable theme right away.
    """
    with qtbot.waitSignal(editor.themes_changed):
        editor.duplicate()
    assert editor.current.id == "turquoise-copie"
    assert editor.current.name == "Turquoise (copie)"
    assert (folder / "turquoise-copie.json").is_file()
    assert editor.theme_combo.currentText() == "Turquoise (copie)"
    assert editor.builtin_note.isHidden()
    assert editor.name_edit.isEnabled() and editor.delete_button.isEnabled()


def test_colour_change_updates_preview_and_saves(editor: ThemeEditorDialog, folder) -> None:
    """FR : une couleur changée apparaît dans l'aperçu, puis est enregistrée.

    EN : a changed colour shows in the preview, then is saved.
    """
    editor.duplicate()
    editor.hex_edits["window"].setText("#123456")
    editor.hex_edits["window"].editingFinished.emit()
    assert editor.dirty
    assert editor.preview.palette().color(QPalette.ColorRole.Window) == QColor("#123456")

    editor.name_edit.setText("Bleu nuit")
    editor.name_edit.textEdited.emit("Bleu nuit")
    assert editor.save()
    saved = json.loads((folder / "turquoise-copie.json").read_text(encoding="utf-8"))
    assert saved["colors"]["window"] == "#123456"
    assert saved["name"] == "Bleu nuit"
    assert not editor.dirty
    assert editor.theme_combo.currentText() == "Bleu nuit"


def test_hex_code_without_hash_and_incomplete_code(editor: ThemeEditorDialog) -> None:
    """FR : « 3ccfc7 » est accepté ; un code incomplet est annulé.

    EN : "3ccfc7" is accepted; an incomplete code is reverted.
    """
    editor.duplicate()
    editor.hex_edits["accent"].setText("abcdef")
    editor.hex_edits["accent"].editingFinished.emit()
    assert editor.edited_colors["accent"] == "#ABCDEF"
    editor.hex_edits["accent"].setText("#12")
    editor.hex_edits["accent"].editingFinished.emit()
    assert editor.edited_colors["accent"] == "#ABCDEF"
    assert editor.hex_edits["accent"].text() == "#ABCDEF"


def test_colour_picker(editor: ThemeEditorDialog, monkeypatch) -> None:
    """FR : le sélecteur de couleurs change la couleur. EN : the colour picker changes it."""
    editor.duplicate()
    monkeypatch.setattr(QColorDialog, "getColor", lambda *a, **k: QColor("#00ff00"))
    editor.swatches["link"].click()
    assert editor.edited_colors["link"] == "#00FF00"
    monkeypatch.setattr(QColorDialog, "getColor", lambda *a, **k: QColor())  # FR : annulé
    editor.swatches["link"].click()
    assert editor.edited_colors["link"] == "#00FF00"


@pytest.fixture
def french_numbers():
    """FR : nombres écrits à la française (« 4,5 »), comme dans RuneCast en français.

    EN : numbers written the French way ("4,5"), as in RuneCast in French.
    """
    previous = QLocale()
    QLocale.setDefault(QLocale("fr"))
    yield
    QLocale.setDefault(previous)


def test_hard_to_read_colours_are_reported(editor: ThemeEditorDialog, french_numbers) -> None:
    """FR : un texte peu lisible est signalé. EN : hard-to-read text is reported."""
    editor.duplicate()
    editor.set_color("text", editor.edited_colors["window"])
    text = editor.readability_label.text()
    assert "Attention" in text and "« Texte » sur « Fond des fenêtres »" in text
    assert "1,0:1" in text and "4,5:1" in text


def test_delete_asks_first(editor: ThemeEditorDialog, monkeypatch, folder) -> None:
    """FR : la suppression demande confirmation ; « Non » ne supprime rien.

    EN : deletion asks for confirmation; "No" deletes nothing.
    """
    editor.duplicate()
    shown = _answers(monkeypatch, NO, YES)
    editor.delete_current()
    assert (folder / "turquoise-copie.json").is_file()
    editor.delete_current()
    assert not (folder / "turquoise-copie.json").exists()
    assert shown == ["Supprimer le thème ?", "Supprimer le thème ?"]
    assert editor.current.id == "turquoise"
    assert editor.theme_combo.findData("turquoise-copie") == -1


def test_import_from_file(editor: ThemeEditorDialog, monkeypatch, tmp_path, folder) -> None:
    """FR : « Importer… » ajoute le thème et l'affiche. EN : "Import…" adds and shows it."""
    source = tmp_path / "ami.json"
    themes.export_theme(_custom(theme_id="ami", name="Thème ami"), source)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(source), ""))
    shown = _answers(monkeypatch)
    editor.import_file()
    assert editor.current.id == "ami"
    assert (folder / "ami.json").is_file()
    assert shown == ["Thème importé"]


def test_invalid_import_shows_a_message(editor: ThemeEditorDialog, monkeypatch, tmp_path) -> None:
    """FR : un fichier incorrect affiche un message, rien n'est ajouté.

    EN : a wrong file shows a message, nothing is added.
    """
    source = tmp_path / "faux.json"
    source.write_text("pas un thème", encoding="utf-8")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(source), ""))
    shown = _answers(monkeypatch)
    count = editor.theme_combo.count()
    editor.import_file()
    assert shown == ["Import impossible"]
    assert editor.theme_combo.count() == count


def test_export_to_file(editor: ThemeEditorDialog, monkeypatch, tmp_path) -> None:
    """FR : « Exporter… » écrit un thème valide ; « .json » est ajouté s'il manque.

    EN : "Export…" writes a valid theme; ".json" is added when missing.
    """
    target = tmp_path / "mon-export"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(target), ""))
    editor.export_file()
    exported = themes.load_theme_file(tmp_path / "mon-export.json")
    assert exported.colors == BUILTIN["turquoise"].colors


def test_export_asks_before_replacing(editor: ThemeEditorDialog, monkeypatch, tmp_path) -> None:
    """FR : un fichier existant n'est remplacé qu'avec l'accord de l'utilisateur.

    EN : an existing file is replaced only with the user's consent.
    """
    existing = tmp_path / "garde.json"
    existing.write_text("ancien contenu", encoding="utf-8")
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *a, **k: (str(tmp_path / "garde"), "")
    )
    shown = _answers(monkeypatch, NO)
    editor.export_file()
    assert existing.read_text(encoding="utf-8") == "ancien contenu"
    assert shown == ["Remplacer le fichier ?"]


@pytest.mark.parametrize(
    ("answer", "closed", "saved"),
    [(CANCEL, False, False), (DISCARD, True, False), (SAVE, True, True)],
)
def test_unsaved_changes_on_close(
    editor: ThemeEditorDialog, monkeypatch, folder, answer, closed: bool, saved: bool
) -> None:
    """FR : en fermant avec des modifications, on propose de les enregistrer.

    EN : when closing with changes, saving them is offered.
    """
    editor.duplicate()
    editor.show()
    editor.set_color("border", "#FF0000")
    shown = _answers(monkeypatch, answer)
    editor.reject()
    assert shown == ["Modifications non enregistrées"]
    assert editor.isVisible() is not closed
    on_disk = json.loads((folder / "turquoise-copie.json").read_text(encoding="utf-8"))
    assert (on_disk["colors"]["border"] == "#FF0000") is saved
    editor.dirty = False  # FR : pour la fermeture en fin de test / EN : for closing at the end


def test_discarded_changes_are_not_duplicated(editor: ThemeEditorDialog, monkeypatch) -> None:
    """FR : après « Ne pas enregistrer », la copie part de la version enregistrée.

    EN : after "Discard", the copy starts from the saved version.
    """
    editor.duplicate()
    original = editor.edited_colors["border"]
    editor.set_color("border", "#FF0000")
    _answers(monkeypatch, DISCARD)
    editor.duplicate()
    assert editor.current.colors["border"] == original


# ----------------------------------------------------------------------
# FR : Intégration à la fenêtre principale / EN : Main window integration
# ----------------------------------------------------------------------
def _run_editor(monkeypatch, actions) -> None:
    """FR : remplace l'attente de la fenêtre par des actions automatiques.

    EN : replace waiting on the window by automatic actions.
    """
    monkeypatch.setattr(ThemeEditorDialog, "exec", lambda dialog: actions(dialog) or 0)


def test_custom_theme_used_and_kept_after_restart(qtbot, monkeypatch, custom_paths, qapp) -> None:
    """FR : un thème personnel créé et utilisé s'applique, s'enregistre, apparaît
         dans le menu et est toujours là au prochain lancement.
    EN : a custom theme created and used applies, is saved, shows in the menu
         and is still there at the next launch.
    """
    window = main_window.MainWindow(custom_paths, Settings())
    qtbot.addWidget(window)

    def actions(dialog: ThemeEditorDialog) -> None:
        dialog.duplicate()
        dialog.set_color("window", "#203040")
        dialog.use_current()

    _run_editor(monkeypatch, actions)
    window.manage_themes_action.trigger()

    assert qapp.property(THEME_PROPERTY) == "turquoise-copie"
    assert qapp.palette().color(QPalette.ColorRole.Window) == QColor("#203040")
    assert window.theme_actions["turquoise-copie"].isChecked()
    assert window.theme_actions["turquoise-copie"].text() == "Turquoise (copie)"
    assert window.manage_themes_action in window.theme_menu.actions()

    # FR : « redémarrage » : nouveaux réglages lus sur le disque, nouvelle fenêtre.
    # EN : "restart": settings read from disk again, new window.
    settings = load_settings(custom_paths.settings_file)
    assert settings.theme == "turquoise-copie"
    restarted = main_window.MainWindow(custom_paths, settings)
    qtbot.addWidget(restarted)
    assert restarted.theme_actions["turquoise-copie"].isChecked()


def test_deleting_the_active_theme_goes_back_to_turquoise(
    qtbot, monkeypatch, custom_paths, qapp
) -> None:
    """FR : si le thème utilisé est supprimé, RuneCast revient au thème Turquoise.

    EN : if the theme in use is deleted, RuneCast goes back to Turquoise.
    """
    themes.save_custom_theme(_custom(), themes.custom_themes_folder(custom_paths.config_dir))
    window = main_window.MainWindow(custom_paths, Settings())
    qtbot.addWidget(window)
    window.theme_actions["mon-theme"].trigger()
    assert qapp.property(THEME_PROPERTY) == "mon-theme"

    def actions(dialog: ThemeEditorDialog) -> None:
        assert dialog.current.id == "mon-theme"
        _answers(monkeypatch, YES)
        dialog.delete_current()

    _run_editor(monkeypatch, actions)
    window.manage_themes_action.trigger()
    assert qapp.property(THEME_PROPERTY) == "turquoise"
    assert "mon-theme" not in window.theme_actions
    assert window.theme_actions["turquoise"].isChecked()
    assert load_settings(custom_paths.settings_file).theme == "turquoise"


def test_saving_the_active_theme_applies_it_live(qtbot, monkeypatch, custom_paths, qapp) -> None:
    """FR : modifier et enregistrer le thème utilisé l'applique aussitôt.

    EN : changing and saving the theme in use applies it at once.
    """
    themes.save_custom_theme(_custom(), themes.custom_themes_folder(custom_paths.config_dir))
    window = main_window.MainWindow(custom_paths, Settings(theme="mon-theme"))
    qtbot.addWidget(window)

    def actions(dialog: ThemeEditorDialog) -> None:
        dialog.set_color("window", "#0A0B0C")
        dialog.save()

    _run_editor(monkeypatch, actions)
    window.manage_themes_action.trigger()
    assert qapp.palette().color(QPalette.ColorRole.Window) == QColor("#0A0B0C")


def test_moved_data_brings_its_custom_themes(qtbot, custom_paths, standard_like_paths) -> None:
    """FR : quand les données changent de dossier, le menu montre les thèmes du
         nouveau dossier (ils voyagent avec les réglages).
    EN : when the data moves to another folder, the menu shows the themes of
         the new folder (they travel with the settings).
    """
    window = main_window.MainWindow(standard_like_paths, Settings())
    qtbot.addWidget(window)
    assert "mon-theme" not in window.theme_actions
    themes.save_custom_theme(_custom(), themes.custom_themes_folder(custom_paths.config_dir))
    window.use_paths(custom_paths)
    assert "mon-theme" in window.theme_actions


def test_editor_is_translated(qtbot, custom_paths, qapp) -> None:
    """FR : l'éditeur s'affiche dans la langue choisie. EN : the editor follows the language."""
    languages = LanguageManager(qapp)
    languages.apply("en")
    try:
        dialog = ThemeEditorDialog(custom_paths.config_dir, "noir")
        qtbot.addWidget(dialog)
        assert dialog.windowTitle() == "Custom themes"
        assert dialog.theme_combo.currentText() == "Black (built-in)"
        assert dialog.name_edit.text() == "Black"
        assert dialog.readability_label.text() == "Readability: good"
    finally:
        languages.apply("fr")


def test_preview_keeps_the_edited_colours(qtbot, custom_paths, qapp) -> None:
    """FR : l'aperçu montre les couleurs du thème édité, même si RuneCast utilise
         un autre thème (ici : RuneCast en Clair, aperçu du thème Noir).
    EN : the preview shows the edited theme's colours, even when RuneCast uses
         another theme (here: RuneCast in Light, preview of the Black theme).
    """
    apply_theme(qapp, BUILTIN["clair"])
    dialog = ThemeEditorDialog(custom_paths.config_dir, "noir")
    qtbot.addWidget(dialog)
    dialog.show()
    field = dialog.preview_field.grab().toImage()
    middle = field.pixelColor(field.width() - 8, field.height() // 2)
    assert middle == QColor(BUILTIN["noir"].colors["base"])
    whole = dialog.preview.grab().toImage()
    assert whole.pixelColor(whole.width() // 2, 4) == QColor(BUILTIN["noir"].colors["window"])
