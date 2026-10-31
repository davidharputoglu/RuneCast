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

"""Tests des glossaires (étape 18).

FR : Un terme imposé doit être identique partout : on le vérifie avec un
     faux moteur qui « traduit » mal les noms. Aussi : mots entiers, plus
     longs d'abord, majuscules, balises et variables jamais touchées, CSV
     (virgule ou point-virgule, avec ou sans en-tête, BOM d'Excel), fichiers
     abîmés, et la fenêtre « Glossaires ».
EN : An imposed term must be identical everywhere: checked with a fake
     engine that mistranslates names. Also: whole words, longest first,
     case, tags and variables never touched, CSV (comma or semicolon, with or
     without header, Excel BOM), damaged files, and the "Glossaries" window.
"""

import json
from pathlib import Path

import pytest
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from runecast.core.cache import TranslationCache
from runecast.core.glossary import (
    Glossary,
    GlossaryEntry,
    GlossaryError,
    delete_glossary,
    load_glossaries,
    new_glossary,
    read_csv,
    save_glossary,
)
from runecast.core.protect import STYLE_XML, protect, restore
from runecast.core.settings import Settings
from runecast.engines.base import Engine
from runecast.engines.chain import PROBLEM_GLOSSARY, EngineChain, translate_texts
from runecast.ui import main_window
from runecast.ui.glossary_dialog import GlossaryDialog
from runecast.ui.i18n import LanguageManager

TOM = Glossary(
    "jeu",
    "Mon jeu",
    "en",
    "fr",
    [
        GlossaryEntry("Tom", "Thomas"),
        GlossaryEntry("Old Tom", "Vieux Tom"),
        GlossaryEntry("Ann", "Anne"),
        GlossaryEntry("ACME", "ACMÉ", case_sensitive=True),
    ],
)


def _apply(line: str, style=None) -> tuple[str, str]:
    protected = TOM.apply(protect(line, style) if style else protect(line))
    return protected.masked, restore(protected.masked, protected).text


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("Tom is here.", "Thomas is here."),
        ("tom! TOM?", "Thomas! Thomas?"),
        ("Old Tom and Tom", "Vieux Tom and Thomas"),
        ("Anna and Ann", "Anna and Anne"),  # FR : mot entier / EN : whole word
        ("Tomato soup", "Tomato soup"),
        ("Hi [Tom]!", "Hi [Tom]!"),  # FR : variable intacte / EN : variable intact
        ("{b}Tom{/b}", "{b}Thomas{/b}"),
        ("acme and ACME", "acme and ACMÉ"),  # FR : casse respectée / EN : case matched
        ("Tom's hat", "Thomas's hat"),
        ("", ""),
    ],
)
def test_apply(line: str, expected: str) -> None:
    """FR : les termes deviennent leur traduction imposée. EN : terms get their imposed one."""
    assert _apply(line)[1] == expected


def test_apply_with_xml_markers() -> None:
    """FR : fonctionne aussi avec les repères XML (DeepL). EN : also works with XML markers."""
    masked, restored = _apply("{b}Tom{/b} meets Ann", STYLE_XML)
    assert masked == '<x id="0"/><x id="2"/><x id="1"/> meets <x id="3"/>'
    assert restored == "{b}Thomas{/b} meets Anne"


def test_check_report() -> None:
    """FR : le rapport signale un terme imposé absent. EN : the report flags a missing term."""
    assert TOM.check("Tom and Old Tom", "Thomas et Vieux Tom") == []
    assert TOM.check("Tom and Tom", "Thomas et Tom")[0].source == "Tom"
    assert TOM.check("Hi [Tom]", "Salut [Tom]") == []  # FR : variable, pas un terme


def test_incomplete_terms_are_ignored() -> None:
    """FR : terme sans traduction : pas appliqué. EN : a term without translation is ignored."""
    glossary = Glossary("x", "x", entries=[GlossaryEntry("Tom", "")])
    assert glossary.apply(protect("Tom")).masked == "Tom"
    assert not glossary.matches("Tom")


@pytest.mark.parametrize(
    "text",
    [
        "source,target,note,case_sensitive\nTom,Thomas,héros,\nACME,ACMÉ,,1\n",
        "﻿source;target;note;case_sensitive\nTom;Thomas;héros;\nACME;ACMÉ;;oui\n",
        "Tom,Thomas,héros\nACME,ACMÉ,,x\n\n",
    ],
)
def test_read_csv(text: str) -> None:
    """FR : CSV avec virgule ou point-virgule, avec ou sans en-tête. EN : comma or semicolon CSV."""
    entries = read_csv(text)
    assert [(e.source, e.target, e.note, e.case_sensitive) for e in entries] == [
        ("Tom", "Thomas", "héros", False),
        ("ACME", "ACMÉ", "", True),
    ]


def test_csv_round_trip_and_errors() -> None:
    """FR : exporter puis relire redonne les mêmes termes ; ligne incomplète refusée.

    EN : export then read gives the same terms; incomplete line refused.
    """
    assert read_csv(TOM.to_csv()) == TOM.entries
    with pytest.raises(GlossaryError, match="2"):
        read_csv("Tom,Thomas\nAnn\n")
    assert read_csv("") == []


def test_files(tmp_path: Path) -> None:
    """FR : enregistrer, relire, supprimer ; fichier abîmé ignoré mais gardé.

    EN : save, read back, delete; damaged file skipped but kept.
    """
    save_glossary(TOM, tmp_path)
    (tmp_path / "abime.json").write_text("{pas du json", encoding="utf-8")
    loaded = load_glossaries(tmp_path)
    assert loaded == {"jeu": TOM}
    assert (tmp_path / "abime.json").exists()
    created = new_glossary("Mon Jeu Été", set(loaded), "en", "tr")
    assert created.glossary_id == "mon-jeu-ete" and created.entries == []
    delete_glossary("jeu", tmp_path)
    assert load_glossaries(tmp_path) == {}


# ----------------------------------------------------------------------
# FR : Le terme imposé est identique partout / EN : The imposed term is identical everywhere
# ----------------------------------------------------------------------
class NameMangler(Engine):
    """FR : faux moteur qui traduit les noms de travers (Tom → Tomás, Tommy…).

    EN : fake engine that mistranslates names (Tom → Tomás, Tommy…).
    """

    engine_id = "mangler"
    online = False

    def __init__(self) -> None:
        self.received: list[str] = []

    def supports(self, source_lang, target_lang):
        return True

    def translate(self, texts, source_lang, target_lang):
        self.received.extend(texts)
        variants = ["Tomás", "Tommy", "Thom"]
        return [text.replace("Tom", variants[i % 3]) for i, text in enumerate(texts)]


LINES = [
    "Tom opens the door.",
    "Where is Tom?",
    "{i}Tom{/i}, wait for me!",
    "I told Tom and Ann about it.",
    "Old Tom lives by the sea.",
    "TOM! Come back!",
    "Tom.",
    "Hello, [player]. Tom says hi.",
] * 4


def test_imposed_term_identical_everywhere() -> None:
    """FR : critère de l'étape 18 : le terme imposé est identique partout.

    EN : step 18 criterion: the imposed term is identical everywhere.
    """
    engine = NameMangler()
    results = translate_texts(LINES, "en", "fr", EngineChain([], [engine]), glossary=TOM)
    for result in results:
        assert result.ok, result
        assert TOM.check(result.source, result.text) == []
        assert "Tomás" not in result.text and "Tommy" not in result.text
    assert results[0].text == "Thomas opens the door."
    assert results[3].text == "I told Thomas and Anne about it."
    assert results[4].text == "Vieux Tom lives by the sea."
    assert results[6].text == "Thomas."  # FR : rien d'autre à traduire / EN : nothing else
    assert all("Tom" not in text for text in engine.received)  # FR : jamais vu / EN : never seen


def test_without_glossary_names_drift() -> None:
    """FR : sans glossaire, le faux moteur abîme les noms (preuve du test ci-dessus).

    EN : without glossary, the fake engine damages names (proof for the test above).
    """
    results = translate_texts(LINES[:3], "en", "fr", EngineChain([], [NameMangler()]))
    assert {r.text.split()[0] for r in results} != {"Thomas"}


def test_glossary_only_for_its_languages() -> None:
    """FR : un glossaire en → fr ne s'applique pas à en → tr. EN : only for its languages."""
    results = translate_texts(["Tom"], "en", "tr", EngineChain([], [NameMangler()]), glossary=TOM)
    assert results[0].text == "Tomás"


def test_glossary_lines_skip_the_cache(tmp_path: Path) -> None:
    """FR : une ligne avec un terme imposé ne passe pas par le cache.

    EN : a line with an imposed term does not go through the cache.
    """
    with TranslationCache(tmp_path / "c.sqlite3") as cache:
        cache.put("Tom opens the door.", "Tomás ouvre la porte.", "en", "fr", "old")
        results = translate_texts(
            ["Tom opens the door.", "No name here."],
            "en",
            "fr",
            EngineChain([], [NameMangler()]),
            cache,
            glossary=TOM,
        )
        assert results[0].text == "Thomas opens the door."
        assert cache.get("Tom opens the door.", "en", "fr") == "Tomás ouvre la porte."
        assert cache.get("No name here.", "en", "fr") == "No name here."


def test_lost_glossary_marker_is_flagged() -> None:
    """FR : un moteur qui perd le repère d'un terme : ligne « à vérifier ».

    EN : an engine losing a term's marker: line "to check".
    """

    class Loser(NameMangler):
        def translate(self, texts, source_lang, target_lang):
            return ["Quelqu'un ouvre la porte." for _ in texts]

    result = translate_texts(
        ["Tom opens the door."], "en", "fr", EngineChain([], [Loser()]), glossary=TOM
    )[0]
    assert not result.ok and "missing" in result.problems
    assert PROBLEM_GLOSSARY == "glossary"


# ----------------------------------------------------------------------
# FR : Fenêtre « Glossaires » / EN : "Glossaries" window
# ----------------------------------------------------------------------
@pytest.fixture
def dialog(qtbot, custom_paths) -> GlossaryDialog:
    widget = GlossaryDialog(custom_paths.config_dir, lambda: EngineChain([], [NameMangler()]))
    qtbot.addWidget(widget)
    return widget


@pytest.fixture(autouse=True)
def quiet_messages(monkeypatch) -> list[str]:
    shown: list[str] = []
    for name in ("information", "warning"):
        monkeypatch.setattr(QMessageBox, name, lambda _p, title, *a, **k: shown.append(title))
    return shown


def _new(dialog: GlossaryDialog, monkeypatch, name: str = "Mon jeu") -> None:
    monkeypatch.setattr(QInputDialog, "getText", lambda *a, **k: (name, True))
    dialog.new_button.click()


def test_create_edit_save(dialog, monkeypatch, custom_paths) -> None:
    """FR : créer un glossaire, ajouter des termes, enregistrer. EN : create, add terms, save."""
    assert not dialog.editor.isEnabled()
    _new(dialog, monkeypatch)
    assert dialog.current.glossary_id == "mon-jeu" and dialog.editor.isEnabled()
    dialog.add_row(GlossaryEntry("Tom", "Thomas", "héros"))
    dialog.add_row(GlossaryEntry("ACME", "ACMÉ", case_sensitive=True))
    dialog.target_combo.setCurrentIndex(dialog.target_combo.findData("tr"))
    assert dialog.dirty
    assert dialog.save()
    saved = json.loads((custom_paths.config_dir / "glossaires" / "mon-jeu.json").read_text("utf-8"))
    assert saved["target_lang"] == "tr"
    assert saved["entries"][1] == {
        "source": "ACME",
        "target": "ACMÉ",
        "note": "",
        "case_sensitive": True,
    }
    assert dialog.glossary_list.item(0).text().startswith("⁦Mon jeu (en → tr)")


def test_incomplete_term_not_saved(dialog, monkeypatch, quiet_messages) -> None:
    """FR : terme sans traduction : pas d'enregistrement. EN : incomplete term blocks saving."""
    _new(dialog, monkeypatch)
    dialog.add_row(GlossaryEntry("Tom", ""))
    assert not dialog.save()
    assert quiet_messages == ["Termes incomplets"]


def test_csv_import_and_export(dialog, monkeypatch, tmp_path) -> None:
    """FR : importer un CSV d'Excel (point-virgule, BOM), puis l'exporter.

    EN : import an Excel CSV (semicolon, BOM), then export it.
    """
    _new(dialog, monkeypatch)
    dialog.add_row(GlossaryEntry("Tom", "Tomasz"))
    source = tmp_path / "termes.csv"
    source.write_bytes("source;target\nTom;Thomas\nAnn;Anne\n".encode("utf-8-sig"))
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(source), ""))
    dialog.import_button.click()
    assert [(e.source, e.target) for e in dialog.entries()] == [("Tom", "Thomas"), ("Ann", "Anne")]
    target = tmp_path / "export"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(target), ""))
    dialog.export_button.click()
    data = (tmp_path / "export.csv").read_bytes()
    assert data.startswith(b"\xef\xbb\xbf")  # FR : BOM pour Excel / EN : BOM for Excel
    assert read_csv(data.decode("utf-8-sig")) == dialog.entries()


def test_translate_and_check(dialog, qtbot, monkeypatch) -> None:
    """FR : « Traduire et contrôler » affiche les traductions et le rapport.

    EN : "Translate and check" shows the translations and the report.
    """
    _new(dialog, monkeypatch)
    dialog.add_row(GlossaryEntry("Tom", "Thomas"))
    dialog.check_lines.setPlainText("Tom is here.\nWhere is Tom?")
    dialog.check_button.click()
    qtbot.waitUntil(lambda: dialog.task is None, timeout=10_000)
    report = dialog.report.text()
    assert "✔ Thomas is here." in report and "✔ Where is Thomas?" in report
    assert report.endswith("Rapport : tous les termes imposés sont respectés.")


def test_delete_and_unsaved(dialog, monkeypatch) -> None:
    """FR : suppression après confirmation ; modifications non enregistrées signalées.

    EN : deletion after confirmation; unsaved changes flagged.
    """
    _new(dialog, monkeypatch)
    dialog.add_row(GlossaryEntry("Tom", "Thomas"))
    asked = []
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda _p, title, *a, **k: asked.append(title) or QMessageBox.StandardButton.Cancel,
    )
    dialog.reject()
    assert asked == ["Modifications non enregistrées"]
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    dialog.delete_button.click()
    assert dialog.glossaries == {} and not dialog.editor.isEnabled()
    dialog.dirty = False


def test_tools_menu_opens_glossaries(qtbot, custom_paths, qapp, monkeypatch) -> None:
    """FR : Outils → Glossaires… ouvre la fenêtre. EN : Tools → Glossaries… opens the window."""
    window = main_window.MainWindow(custom_paths, Settings(), LanguageManager(qapp))
    qtbot.addWidget(window)
    opened = []
    monkeypatch.setattr(GlossaryDialog, "exec", lambda d: opened.append(d.make_chain) or 0)
    assert window.glossaries_action in window.tools_menu.actions()
    window.glossaries_action.trigger()
    assert len(opened) == 1 and opened[0] is not None
