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

"""Tests du banc d'essai et des réglages de performance (étape 14).

FR : Les vraies mesures se font sur tes PC (« runecast --benchmark ») et sur
     la machine de GitHub (test « Modèles »). Ici, on vérifie la méthode avec
     un faux moteur dont on connaît la vitesse : les bons réglages doivent
     être conseillés, la mesure doit pouvoir s'annuler, et les réglages
     choisis doivent être enregistrés et utilisés par le moteur local.
EN : Real measures happen on your PCs ("runecast --benchmark") and on
     GitHub's machine ("Models" check). Here, the method is checked with a
     fake engine of known speed: the right settings must be recommended, the
     measure must be cancellable, and the chosen settings must be saved and
     used by the local engine.
"""

import json
import time

import pytest
from PySide6.QtWidgets import QMessageBox

from runecast import __main__ as cli
from runecast.core.settings import Settings, load_settings
from runecast.engines import benchmark
from runecast.engines.argos import LocalEngine, default_threads
from runecast.engines.benchmark import (
    BenchmarkResult,
    memory_growth,
    recommend,
    run_benchmark,
    thread_options,
)
from runecast.ui import main_window
from runecast.ui import models_page as models_page_module
from runecast.ui.i18n import LanguageManager
from runecast.ui.models_page import ModelsPage


class FakeEngine:
    """FR : faux moteur : plus de cœurs = plus rapide, largeur 4 = plus lent.

    EN : fake engine: more cores = faster, width 4 = slower.
    """

    made: list[tuple[int, int]] = []

    def __init__(self, threads: int, beam: int) -> None:
        self.delay = 0.0004 * beam / min(threads, 2)
        FakeEngine.made.append((threads, beam))

    def translate(self, texts, source, target):
        time.sleep(self.delay * len(texts))
        return list(texts)

    def unload(self) -> None:
        pass


def test_benchmark_tries_every_setting() -> None:
    """FR : chaque réglage est essayé, avec la progression. EN : every setting is tried."""
    FakeEngine.made = []
    steps: list[tuple[int, int]] = []
    results = run_benchmark(
        FakeEngine, "en", "fr", threads=[1, 2, 4], progress=lambda d, t: steps.append((d, t))
    )
    assert [(r.threads, r.beam_size) for r in results] == FakeEngine.made
    assert len(results) == 9 and steps[-1] == (9, 9)
    assert all(r.sentences == len(benchmark.SAMPLE_LINES) and r.memory_mb > 0 for r in results)
    fast = next(r for r in results if (r.threads, r.beam_size) == (2, 1))
    slow = next(r for r in results if (r.threads, r.beam_size) == (1, 4))
    assert fast.sentences_per_second > slow.sentences_per_second


def test_benchmark_can_be_cancelled() -> None:
    """FR : la mesure s'arrête si on l'annule. EN : the measure stops when cancelled."""
    calls = []
    results = run_benchmark(
        FakeEngine,
        "en",
        "fr",
        threads=[1, 2],
        should_cancel=lambda: calls.append(1) or len(calls) > 2,
    )
    assert len(results) == 2


def _result(threads: int, beam: int, speed: float) -> BenchmarkResult:
    return BenchmarkResult(threads, beam, 100, 100 / speed, 500.0)


@pytest.mark.parametrize(
    ("results", "expected"),
    [
        # FR : largeur 2 assez rapide ; 2 cœurs suffisent (≥ 90 % du meilleur)
        ([_result(1, 2, 5), _result(2, 2, 9.5), _result(4, 2, 10), _result(4, 1, 20)], (2, 2)),
        # FR : largeur 2 trop lente (< 4 phrases/s) : largeur 1
        ([_result(1, 2, 2), _result(2, 2, 3), _result(1, 1, 5), _result(2, 1, 6)], (2, 1)),
        # FR : un seul cœur suffit / one core is enough
        ([_result(1, 2, 10), _result(2, 2, 10.5)], (1, 2)),
    ],
)
def test_recommendation(results, expected) -> None:
    """FR : les réglages conseillés suivent la règle. EN : recommended settings follow the rule."""
    advice = recommend(results)
    assert (advice.threads, advice.beam_size) == expected


def test_memory_stability() -> None:
    """FR : mémoire dite stable si elle grandit peu. EN : memory stable if it grows little."""
    assert recommend([_result(1, 2, 5)], growth_mb=12).memory_stable
    assert not recommend([_result(1, 2, 5)], growth_mb=300).memory_stable
    assert isinstance(memory_growth(FakeEngine(1, 1), "en", "fr", rounds=2), float)
    with pytest.raises(ValueError):
        recommend([])


def test_thread_options() -> None:
    """FR : nombres de cœurs essayés, jusqu'aux cœurs physiques. EN : core counts tried."""
    options = thread_options()
    assert options == sorted(set(options))
    assert options[-1] == benchmark.physical_cores()
    assert 1 <= default_threads() <= 4


def test_engine_configure() -> None:
    """FR : changer les réglages libère les modèles chargés. EN : changing settings frees models."""
    engine = LocalEngine(lambda: {}, threads=2, beam_size=2)
    engine._loaded[object()] = object()
    engine.configure(2, 2)
    assert len(engine._loaded) == 1  # FR : rien n'a changé / EN : nothing changed
    engine.configure(1, 4)
    assert (engine.threads, engine.beam_size) == (1, 4) and not engine._loaded
    engine.configure(None, 4)
    assert engine.threads == default_threads()


def test_command_line_without_model(monkeypatch, custom_paths) -> None:
    """FR : « runecast --benchmark » sans modèle installé : explication claire.

    EN : "runecast --benchmark" with no installed model: clear explanation.
    """
    monkeypatch.setattr(cli, "resolve_paths", lambda force_portable=False: custom_paths)
    assert "Aucun modèle installé" in cli.benchmark_text([])


def test_command_line_with_model(monkeypatch, custom_paths, capsys) -> None:
    """FR : avec un modèle : tableau, réglages conseillés et rapport enregistré.

    EN : with a model: table, recommended settings and saved report.
    """
    from runecast.engines import argos

    folder = custom_paths.data_dir / "models" / "argos" / "en_fr"
    (folder / "model").mkdir(parents=True)
    (folder / "model" / "model.bin").write_bytes(b"x")
    (folder / "sentencepiece.model").write_bytes(b"x")
    (folder / "metadata.json").write_text(json.dumps({"from_code": "en", "to_code": "fr"}))
    (folder / "runecast-install.json").write_text(
        json.dumps({"size": 1, "sha256": "0" * 64, "installed_at": "2026-10-31"})
    )

    class Echo:
        def __init__(self, package, threads, beam, factory=None):
            self.beam = beam

        def translate(self, texts):
            return list(texts)

    monkeypatch.setattr(argos, "ArgosTranslator", Echo)
    monkeypatch.setattr(cli, "resolve_paths", lambda force_portable=False: custom_paths)
    text = cli.main(["--benchmark", "en", "fr"])
    output = capsys.readouterr().out
    assert text == 0
    assert "Conseillé / Recommended" in output and "Mémoire stable" in output
    reports = list(custom_paths.log_dir.glob("banc-essai-*.json"))
    assert len(reports) == 1
    report = json.loads(reports[0].read_text(encoding="utf-8"))
    assert report["source"] == "en" and report["results"]


# ----------------------------------------------------------------------
# FR : Réglages de performance dans les Paramètres / EN : Performance settings
# ----------------------------------------------------------------------
@pytest.fixture
def page(qtbot, custom_paths) -> ModelsPage:
    widget = ModelsPage(custom_paths)
    qtbot.addWidget(widget)
    yield widget
    widget.shutdown()


def test_page_shows_and_stores_performance(page: ModelsPage) -> None:
    """FR : la page affiche et enregistre les réglages. EN : the page shows and stores settings."""
    page.load(Settings(local_threads=1, local_beam_size=4))
    assert page.threads_combo.currentData() == 1
    assert page.beam_combo.currentData() == 4
    assert page.engine.threads == 1 and page.engine.beam_size == 4
    page.beam_combo.setCurrentIndex(page.beam_combo.findData(1))
    page.threads_combo.setCurrentIndex(0)
    settings = Settings()
    page.store(settings)
    assert (settings.local_threads, settings.local_beam_size) == (0, 1)
    assert page.threads_combo.itemText(0).startswith("Automatique")


def test_page_measure_selects_recommendation(page: ModelsPage, qtbot, monkeypatch) -> None:
    """FR : « Mesurer la vitesse… » choisit les réglages conseillés et les explique.

    EN : "Measure the speed…" selects the recommended settings and explains them.
    """
    shown: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "information", lambda _p, _t, text, *a, **k: shown.append(text)
    )
    monkeypatch.setattr(page, "benchmark_pair", lambda: ("en", "fr"))
    monkeypatch.setattr(
        models_page_module,
        "run_benchmark",
        lambda *a, **k: [_result(1, 2, 3), _result(1, 1, 8), _result(2, 1, 8.5)],
    )
    monkeypatch.setattr(models_page_module, "memory_growth", lambda *a, **k: 5.0)
    page.measure_speed()
    qtbot.waitUntil(lambda: page.task is None, timeout=10_000)
    assert page.threads_combo.currentData() == 1
    assert page.beam_combo.currentData() == 1
    assert shown and "1 cœur(s)" in shown[0] and "stable" in shown[0]


def test_settings_saved_from_dialog(qtbot, custom_paths, qapp) -> None:
    """FR : « OK » dans les Paramètres enregistre les réglages de performance.

    EN : "OK" in the Settings saves the performance settings.
    """
    languages = LanguageManager(qapp)
    window = main_window.MainWindow(custom_paths, Settings(), languages)
    qtbot.addWidget(window)
    dialog = window.create_settings_dialog()
    qtbot.addWidget(dialog)
    page = dialog.models_page
    page.beam_combo.setCurrentIndex(page.beam_combo.findData(4))
    page.threads_combo.setCurrentIndex(page.threads_combo.findData(1))
    dialog.accept()
    saved = load_settings(custom_paths.settings_file)
    assert (saved.local_threads, saved.local_beam_size) == (1, 4)
