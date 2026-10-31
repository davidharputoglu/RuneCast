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

"""Point d'entrée en ligne de commande / Command-line entry point.

FR : Permet de lancer RuneCast depuis un terminal, avec « runecast » ou
     « python -m runecast ».
       - sans option : ouvre la fenêtre de RuneCast ;
       - --version   : affiche la version et les crédits, sans ouvrir de fenêtre ;
       - --paths     : affiche les dossiers utilisés, sans ouvrir de fenêtre ;
       - --portable  : range toutes les données dans le dossier « portable-data »
                       à côté de l'application (pour tester le mode portable) ;
       - --protect « texte » : montre comment une réplique est protégée avant
                       d'être envoyée à un moteur de traduction (étape 11) ;
       - --benchmark [de vers] : mesure la vitesse et la mémoire de la
                       traduction locale sur ce PC, et conseille les meilleurs
                       réglages (étape 14). Exemple : --benchmark en fr

EN : Lets you start RuneCast from a terminal, with "runecast" or
     "python -m runecast".
       - no option  : opens the RuneCast window;
       - --version  : prints the version and credits, without opening a window;
       - --paths    : prints the folders in use, without opening a window;
       - --portable : stores all data in the "portable-data" folder next to the
                      application (to test portable mode);
       - --protect "text" : shows how a line is protected before being sent to
                      a translation engine (step 11);
       - --benchmark [from to] : measures local translation speed and memory
                      on this PC, and recommends the best settings (step 14).
                      Example: --benchmark en fr
"""

import argparse
import sys

from runecast import about
from runecast.core.paths import MODE_CUSTOM, MODE_NORMAL, MODE_PORTABLE, resolve_paths
from runecast.core.protect import protect, restore


def build_parser() -> argparse.ArgumentParser:
    """Décrit les options acceptées / Describe the accepted options."""
    parser = argparse.ArgumentParser(
        prog="runecast",
        description="RuneCast : traduction de jeux vidéo / video game translation",
    )
    # FR : --version affiche la version et les mentions « À propos ».
    # EN : --version prints the version and the "About" mentions.
    parser.add_argument(
        "--version",
        action="store_true",
        help="affiche la version et les crédits / show version and credits",
    )
    # FR : --paths affiche les dossiers utilisés. EN : --paths prints the folders in use.
    parser.add_argument(
        "--paths",
        action="store_true",
        help="affiche les dossiers de données / show the data folders",
    )
    # FR : --portable active le mode portable. EN : --portable enables portable mode.
    parser.add_argument(
        "--portable",
        action="store_true",
        help="mode portable : données à côté de l'application / portable mode",
    )
    # FR : --protect montre la protection des balises d'une réplique.
    # EN : --protect shows the tag protection of a line.
    parser.add_argument(
        "--protect",
        metavar="TEXTE",
        help="montre la protection des balises d'une réplique / show tag protection",
    )
    # FR : --benchmark mesure la traduction locale. EN : --benchmark measures local translation.
    parser.add_argument(
        "--benchmark",
        nargs="*",
        metavar="LANGUE",
        help="mesure la vitesse de la traduction locale / measure local translation speed "
        "(ex. --benchmark en fr)",
    )
    return parser


def benchmark_text(languages: list[str], portable: bool = False) -> str:
    """Banc d'essai de la traduction locale (étape 14) / Local translation benchmark.

    FR : Utilise les modèles déjà installés (Paramètres → Modèles de
         traduction). Le résultat est aussi enregistré dans le dossier du
         journal (banc-essai-DATE.json), pour pouvoir me le transmettre.
    EN : Uses the models already installed. The result is also saved in the
         log folder (banc-essai-DATE.json), so it can be sent to me.
    """
    import json
    from datetime import datetime

    from runecast.engines.argos import LocalEngine
    from runecast.engines.benchmark import (
        memory_growth,
        physical_cores,
        recommend,
        run_benchmark,
    )
    from runecast.engines.models import ModelStore, models_folder

    paths = resolve_paths(force_portable=portable)
    store = ModelStore(models_folder(paths.data_dir), paths.cache_dir / "downloads")
    installed = sorted(store.installed())
    if not installed:
        return (
            "Aucun modèle installé. Installe d'abord un modèle : Paramètres → Modèles de "
            "traduction.\nNo model installed. First install one: Settings → Translation models."
        )
    if len(languages) == 2:
        source, target = languages
    else:
        source, target = ("en", "fr") if ("en", "fr") in installed else installed[0]
    probe = LocalEngine(store.packages)
    if not probe.supports(source, target):
        return f"Aucun modèle pour / No model for {source} → {target}"

    print(f"Banc d'essai / Benchmark: {source} → {target}, {physical_cores()} cœurs / cores")

    def progress(done: int, total: int) -> None:
        print(f"  essai / trial {done}/{total}", flush=True)

    results = run_benchmark(
        lambda threads, beam: LocalEngine(store.packages, threads=threads, beam_size=beam),
        source,
        target,
        progress=progress,
    )
    best = recommend(results)
    engine = LocalEngine(store.packages, threads=best.threads, beam_size=best.beam_size)
    growth = memory_growth(engine, source, target)
    advice = recommend(results, growth)
    lines = ["", "Cœurs  Largeur  Phrases/s  Mémoire (Mo) / Cores  Width  Sentences/s  Memory (MB)"]
    for result in results:
        lines.append(
            f"{result.threads:>5}  {result.beam_size:>7}  {result.sentences_per_second:>9.1f}"
            f"  {result.memory_mb:>12.0f}"
        )
    lines += [
        "",
        f"Conseillé / Recommended: {advice.threads} cœur(s) / core(s), "
        f"largeur / width {advice.beam_size}",
        f"Mémoire stable / Memory stable: {'oui / yes' if advice.memory_stable else 'NON / NO'} "
        f"({advice.memory_growth_mb:+.0f} Mo / MB en 3 tours / over 3 rounds)",
        "Pour appliquer / To apply: Paramètres → Modèles de traduction → Performance",
    ]
    report = paths.log_dir / f"banc-essai-{datetime.now():%Y%m%d-%H%M%S}.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "source": source,
                "target": target,
                "physical_cores": physical_cores(),
                "results": [result.as_dict() for result in results],
                "recommended": advice.__dict__,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    lines.append(f"Rapport / Report: {report}")
    return "\n".join(lines)


def protect_text(text: str) -> str:
    """FR : explique la protection d'une réplique (démonstration de l'étape 11).

    EN : explain the protection of a line (step 11 demonstration).
    """
    protected = protect(text)
    lines = [
        "Texte envoyé au moteur / Text sent to the engine:",
        f"  {protected.masked}",
        "Éléments protégés / Protected items:",
    ]
    for index, token in enumerate(protected.tokens):
        shown = "(retour à la ligne / line break)" if token == "\n" else token
        lines.append(f"  [{index}] = {shown}")
    if not protected.tokens:
        lines.append("  (aucun / none)")
    restored = restore(protected.masked, protected)
    check = "OK" if restored.ok and restored.text == text else "ÉCHEC / FAILED"
    lines.append(f"Contrôle du retour / Round-trip check: {check}")
    return "\n".join(lines)


def paths_text(portable: bool = False) -> str:
    """FR : texte décrivant les dossiers utilisés. EN : text describing the folders."""
    paths = resolve_paths(force_portable=portable)
    modes = {
        MODE_NORMAL: "normal (emplacement standard / standard location)",
        MODE_CUSTOM: f"personnalisé / custom ({paths.root})",
        MODE_PORTABLE: "portable",
    }
    lines = [f"Mode : {modes[paths.mode]}"]
    labels = {
        "config": "Réglages / Settings",
        "data": "Données / Data",
        "cache": "Cache",
        "logs": "Journaux / Logs",
    }
    for name, folder in paths.folders().items():
        lines.append(f"{labels[name]} : {folder}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Lance RuneCast / Start RuneCast.

    FR : Renvoie 0 si tout s'est bien passé (convention des programmes).
    EN : Returns 0 when everything went fine (standard program convention).
    """
    args = build_parser().parse_args(argv)

    if args.version:
        print(about.about_text())
        return 0

    if args.paths:
        print(paths_text(portable=args.portable))
        return 0

    if args.benchmark is not None:
        print(benchmark_text(args.benchmark, portable=args.portable))
        return 0

    if args.protect is not None:
        # FR : sortie en UTF-8, pour afficher toutes les langues (même sous Windows).
        # EN : UTF-8 output, to show every language (even on Windows).
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(protect_text(args.protect))
        return 0

    # FR : L'interface n'est chargée qu'ici : « --version » reste ainsi
    #      instantané et fonctionne même sans affichage graphique.
    # EN : The interface is only loaded here, so "--version" stays instant and
    #      works even without a graphical display.
    from runecast.ui.app import run

    return run(portable=args.portable)


# FR : Ce bloc s'exécute seulement quand on lance « python -m runecast ».
# EN : This block only runs when "python -m runecast" is used.
if __name__ == "__main__":
    sys.exit(main())
