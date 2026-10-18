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

"""Met à jour les traductions de l'interface / Update the interface translations.

FR : Deux opérations, avec les outils officiels de Qt (fournis avec PySide6) :
       1. « lupdate » relit tout le code de RuneCast et met à jour les fichiers
          translations/runecast_<langue>.ts : les nouveaux textes y sont
          ajoutés (à traduire), les textes disparus sont retirés, et les
          traductions existantes sont conservées.
       2. « lrelease » compile ces fichiers en .qm, le format rapide que
          RuneCast lit au démarrage (dossier src/runecast/resources/translations).
     Les fichiers .ts sont du texte (XML) : ils peuvent être relus et corrigés
     avec Qt Linguist (« uv run pyside6-linguist ») ou sur une plateforme de
     traduction collaborative comme Weblate.

EN : Two operations, with Qt's official tools (shipped with PySide6):
       1. "lupdate" re-reads all RuneCast code and updates the
          translations/runecast_<language>.ts files: new texts are added (to be
          translated), removed texts are dropped, existing translations kept.
       2. "lrelease" compiles these files into .qm, the fast format RuneCast
          reads at start-up (src/runecast/resources/translations folder).
     .ts files are text (XML): they can be reviewed and fixed with Qt Linguist
     ("uv run pyside6-linguist") or on a collaborative translation platform
     such as Weblate.

Utilisation / Usage :
    uv run python tools/update_translations.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

# FR : Le script est lancé depuis le dossier du projet : on rend le code de
#      RuneCast importable pour lire la liste des langues.
# EN : The script runs from the project folder: make the RuneCast code
#      importable to read the list of languages.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from runecast.core.languages import SOURCE_LANGUAGE, translated_languages  # noqa: E402

SOURCE_DIR = ROOT / "src" / "runecast"
TS_DIR = ROOT / "translations"
QM_DIR = SOURCE_DIR / "resources" / "translations"


def tool(name: str) -> str:
    """FR : chemin d'un outil Qt (pyside6-lupdate…). EN : path of a Qt tool."""
    path = shutil.which(name)
    if path is None:
        raise SystemExit(f"Outil introuvable / Tool not found: {name} (lancer avec « uv run »)")
    return path


def source_files(source_dir: Path = SOURCE_DIR) -> list[str]:
    """FR : tous les fichiers Python de RuneCast. EN : every RuneCast Python file."""
    return [str(path) for path in sorted(source_dir.rglob("*.py"))]


def ts_file(code: str, ts_dir: Path = TS_DIR) -> Path:
    """FR : fichier .ts d'une langue. EN : .ts file of a language."""
    return ts_dir / f"runecast_{code}.ts"


def qm_file(code: str, qm_dir: Path = QM_DIR) -> Path:
    """FR : fichier .qm d'une langue. EN : .qm file of a language."""
    return qm_dir / f"runecast_{code}.qm"


def run_lupdate(ts_dir: Path = TS_DIR) -> None:
    """FR : met à jour les fichiers .ts depuis le code. EN : update .ts files from code."""
    ts_dir.mkdir(parents=True, exist_ok=True)
    for code in translated_languages():
        subprocess.run(
            [
                tool("pyside6-lupdate"),
                *source_files(),
                # FR : pas de numéros de ligne : les .ts ne changent que si les
                #      textes changent. EN : no line numbers, so .ts files only
                #      change when texts change.
                "-locations",
                "none",
                "-no-obsolete",
                "-source-language",
                SOURCE_LANGUAGE,
                "-target-language",
                code,
                "-ts",
                str(ts_file(code, ts_dir)),
            ],
            check=True,
            capture_output=True,
        )


def run_lrelease(ts_dir: Path = TS_DIR, qm_dir: Path = QM_DIR) -> None:
    """FR : compile les .ts en .qm. EN : compile .ts files into .qm."""
    qm_dir.mkdir(parents=True, exist_ok=True)
    for code in translated_languages():
        subprocess.run(
            [
                tool("pyside6-lrelease"),
                str(ts_file(code, ts_dir)),
                "-qm",
                str(qm_file(code, qm_dir)),
            ],
            check=True,
            capture_output=True,
        )


def main() -> int:
    """Point d'entrée du script / Script entry point."""
    print("Mise à jour des traductions / Updating translations...")
    run_lupdate()
    run_lrelease()
    for code in translated_languages():
        print(f"  OK  {ts_file(code).relative_to(ROOT)} -> {qm_file(code).relative_to(ROOT)}")
    print("Terminé / Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
