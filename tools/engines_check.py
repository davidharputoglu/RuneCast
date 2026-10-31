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

"""Essai réel des moteurs en ligne gratuits / Real test of the free online engines.

FR : Lancé par GitHub (fichier .github/workflows/online.yml) quand le code des
     moteurs en ligne change : Yandex gratuit et Google gratuit traduisent
     quelques phrases (avec des repères de protection [0], [1]…) vers le
     français, le turc, le kazakh et l'arabe. Le résultat est publié en
     « notice » GitHub. Les moteurs à clé ne sont pas essayés ici (il faudrait
     des clés) : ils le sont avec le bouton « Tester » des Paramètres.
       uv run python tools/engines_check.py
EN : Run by GitHub when the online engine code changes: Yandex free and
     Google free translate a few sentences (with protection markers [0],
     [1]…) into French, Turkish, Kazakh and Arabic. The result is published
     as a GitHub "notice". Key engines are not tried here (keys would be
     needed): they are, with the "Test" button of the Settings.
"""

import json
import sys

from runecast.core.protect import protect, restore
from runecast.engines.online import OnlineError, create_engine

SENTENCES = ["Hello, how are you today?", "{b}Welcome{/b}, [player]! You have %d coins."]
TARGETS = ("fr", "tr", "kk", "ar", "ru")


def main() -> int:
    report: dict = {}
    for engine_id in ("yandex_free", "google_free"):
        engine = create_engine(engine_id)
        results: dict = {}
        for target in TARGETS:
            protected = [protect(text, engine.marker_style) for text in SENTENCES]
            try:
                translated = engine.translate([p.masked for p in protected], "en", target)
                restored = [restore(t, p) for t, p in zip(translated, protected, strict=True)]
                results[target] = [
                    {"text": r.text, "ok": r.ok, "problems": r.problems} for r in restored
                ]
            except OnlineError as error:
                results[target] = {"error": f"{error.reason}: {error}"}
            except Exception as error:  # noqa: BLE001 (on note toute erreur / record any error)
                results[target] = {"error": f"{type(error).__name__}: {error}"[:200]}
        results["method"] = getattr(engine, "method", "")
        try:
            results["languages"] = len(engine.fetch_languages())
        except Exception as error:  # noqa: BLE001
            results["languages"] = f"{type(error).__name__}: {error}"[:120]
        report[engine_id] = results
        engine.close()
    print(f"::notice title=online::{json.dumps(report, ensure_ascii=True)}")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
