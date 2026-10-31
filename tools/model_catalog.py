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

"""Outil du catalogue des modèles / Model catalogue tool.

FR : Tient à jour src/runecast/resources/models/argos-catalog.json, la liste
     des modèles Argos que RuneCast propose au téléchargement.
       uv run python tools/model_catalog.py build
           lit l'index officiel d'Argos (sur GitHub) et met à jour la liste,
           en gardant les tailles et empreintes déjà connues ;
       uv run python tools/model_catalog.py check
           télécharge chaque modèle, calcule sa taille et son empreinte
           SHA-256, l'installe dans un dossier temporaire et lui fait
           traduire une phrase avec le moteur local de RuneCast. Lancé
           automatiquement par GitHub (fichier .github/workflows/models.yml) :
           le résultat est publié sous forme de « notices » GitHub ;
       uv run python tools/model_catalog.py apply resultats.json
           ajoute les tailles et empreintes vérifiées au catalogue ;
       uv run python tools/model_catalog.py benchmark en fr
           télécharge un modèle et lance le banc d'essai de l'étape 14
           (vitesse et mémoire) ; résultat publié en « notice » GitHub.

EN : Keeps src/runecast/resources/models/argos-catalog.json up to date, the
     list of Argos models RuneCast offers for download. "build" reads the
     official Argos index (on GitHub) and updates the list, keeping the sizes
     and fingerprints already known; "check" downloads each model, computes
     its size and SHA-256 fingerprint, installs it in a temporary folder and
     makes it translate a sentence with RuneCast's local engine (run by
     GitHub, results published as GitHub "notices"); "apply" adds the checked
     sizes and fingerprints to the catalogue.
"""

import argparse
import json
import sys
import tempfile
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "src" / "runecast" / "resources" / "models" / "argos-catalog.json"
INDEX_URL = "https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json"
# FR : Phrase d'essai pour chaque modèle. EN : Test sentence for each model.
TEST_SENTENCE = "Hello, how are you today?"
# FR : Nombre de résultats par notice GitHub. EN : Results per GitHub notice.
NOTICE_SIZE = 12


def read_catalog() -> dict:
    """FR : catalogue actuel (vide s'il n'existe pas). EN : current catalogue (empty if none)."""
    if CATALOG.exists():
        return json.loads(CATALOG.read_text(encoding="utf-8"))
    return {"format": 1, "packages": []}


def write_catalog(catalog: dict) -> None:
    """FR : écrit le catalogue, trié et lisible. EN : write the catalogue, sorted and readable."""
    catalog["packages"].sort(key=lambda item: (item["from_code"], item["to_code"]))
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    CATALOG.write_text(json.dumps(catalog, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def build() -> None:
    """FR : met à jour la liste depuis l'index d'Argos. EN : update the list from Argos's index."""
    with urllib.request.urlopen(INDEX_URL, timeout=60) as response:
        index = json.loads(response.read().decode("utf-8"))
    known = {item["url"]: item for item in read_catalog()["packages"]}
    packages = []
    for item in index:
        if item.get("type", "translate") != "translate" or not item.get("links"):
            continue
        url = item["links"][0]
        previous = known.get(url, {})
        packages.append(
            {
                "code": item["code"],
                "from_code": item["from_code"],
                "to_code": item["to_code"],
                "from_name": item["from_name"],
                "to_name": item["to_name"],
                "version": item["package_version"],
                "url": url,
                "size": previous.get("size"),
                "sha256": previous.get("sha256"),
                "tokenizer": previous.get("tokenizer"),
            }
        )
    write_catalog(
        {
            "format": 1,
            "source": INDEX_URL,
            "updated": datetime.now(UTC).date().isoformat(),
            "packages": packages,
        }
    )
    print(f"{len(packages)} modèles / models")


def check_one(item: dict, work: Path) -> dict:
    """FR : télécharge, mesure et essaie un modèle. EN : download, measure and try one model."""
    from runecast.engines.argos import LocalEngine
    from runecast.engines.models import ModelStore, file_sha256, load_catalog

    entry = next(e for e in load_catalog(include_unsupported=True) if e.url == item["url"])
    folder = work / item["code"]
    store = ModelStore(folder / "installed", folder / "downloads")
    result = {"url": item["url"], "ok": False}
    try:
        archive = store.download(replace(entry, sha256=None))
        result["size"] = archive.stat().st_size
        result["sha256"] = file_sha256(archive)
        with zipfile.ZipFile(archive) as content:
            names = [PurePosixPath(name).name for name in content.namelist()]
        result["tokenizer"] = (
            "sentencepiece"
            if "sentencepiece.model" in names
            else "bpe"
            if "bpe.model" in names
            else "unknown"
        )
        store.install_archive(archive)
        archive.unlink()
        engine = LocalEngine(store.packages, threads=1)
        translated = engine.translate([TEST_SENTENCE], entry.from_code, entry.to_code)[0]
        result["sample"] = translated[:80]
        result["ok"] = bool(translated.strip())
    except Exception as error:  # noqa: BLE001 (on note toute erreur / record any error)
        result["error"] = f"{type(error).__name__}: {error}"[:200]
    return result


def check(limit: int | None, workers: int, output: Path | None) -> int:
    """FR : vérifie tous les modèles et publie les résultats. EN : check all models, publish."""
    packages = read_catalog()["packages"][:limit]
    with tempfile.TemporaryDirectory() as temporary:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(lambda item: check_one(item, Path(temporary)), packages))
    if output is not None:
        output.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    for start in range(0, len(results), NOTICE_SIZE):
        chunk = json.dumps(results[start : start + NOTICE_SIZE], ensure_ascii=True)
        print(f"::notice title=models {start // NOTICE_SIZE}::{chunk}")
    failed = [result["url"] for result in results if not result["ok"]]
    print(f"{len(results) - len(failed)} OK, {len(failed)} en échec / failed")
    for url in failed:
        print(f"  ÉCHEC / FAILED: {url}")
    return 0


def apply(results_file: Path) -> None:
    """FR : ajoute tailles et empreintes vérifiées. EN : add checked sizes and fingerprints."""
    results = {item["url"]: item for item in json.loads(results_file.read_text(encoding="utf-8"))}
    catalog = read_catalog()
    for item in catalog["packages"]:
        result = results.get(item["url"])
        if result and result.get("sha256"):
            item["size"] = result["size"]
            item["sha256"] = result["sha256"]
            item["tokenizer"] = result.get("tokenizer") or (
                "sentencepiece" if result.get("ok") else "bpe"
            )
    write_catalog(catalog)


def benchmark(source: str, target: str) -> None:
    """FR : banc d'essai sur la machine de GitHub. EN : benchmark on GitHub's machine."""
    from runecast.engines.argos import LocalEngine
    from runecast.engines.benchmark import memory_growth, physical_cores, recommend, run_benchmark
    from runecast.engines.models import ModelStore, load_catalog

    entry = next(e for e in load_catalog() if (e.from_code, e.to_code) == (source, target))
    with tempfile.TemporaryDirectory() as temporary:
        store = ModelStore(Path(temporary) / "installed", Path(temporary) / "downloads")
        store.download_and_install(entry)
        results = run_benchmark(
            lambda threads, beam: LocalEngine(store.packages, threads=threads, beam_size=beam),
            source,
            target,
        )
        best = recommend(results)
        engine = LocalEngine(store.packages, threads=best.threads, beam_size=best.beam_size)
        growth = memory_growth(engine, source, target)
    report = {
        "pair": f"{source}-{target}",
        "physical_cores": physical_cores(),
        "results": [result.as_dict() for result in results],
        "recommended": recommend(results, growth).__dict__,
    }
    print(f"::notice title=benchmark::{json.dumps(report)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("build")
    check_parser = commands.add_parser("check")
    check_parser.add_argument("--limit", type=int)
    check_parser.add_argument("--workers", type=int, default=4)
    check_parser.add_argument("--output", type=Path)
    apply_parser = commands.add_parser("apply")
    apply_parser.add_argument("results", type=Path)
    benchmark_parser = commands.add_parser("benchmark")
    benchmark_parser.add_argument("source")
    benchmark_parser.add_argument("target")
    args = parser.parse_args(argv)
    if args.command == "build":
        build()
    elif args.command == "check":
        return check(args.limit, args.workers, args.output)
    elif args.command == "benchmark":
        benchmark(args.source, args.target)
    else:
        apply(args.results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
