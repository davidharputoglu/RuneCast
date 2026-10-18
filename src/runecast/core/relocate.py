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

"""Déplacement des données de RuneCast / Moving RuneCast data.

FR : Quand l'utilisateur choisit un autre dossier pour ses données, RuneCast
     suit toujours la même méthode prudente (décision du 18 octobre 2026) :
       1. vérifier le dossier choisi (vide, en dehors des dossiers actuels,
          accessible en écriture, assez de place) ;
       2. COPIER chaque fichier, sans jamais écraser un fichier existant ;
       3. VÉRIFIER la copie : même taille et même empreinte SHA-256 ;
       4. seulement ensuite, utiliser le nouveau dossier ;
       5. PROPOSER de supprimer les anciens fichiers : rien n'est supprimé
          sans l'accord de l'utilisateur, et seuls les fichiers copiés et
          vérifiés peuvent l'être.

EN : When the user picks another folder for their data, RuneCast always uses
     the same careful method (decision of 18 October 2026): check the chosen
     folder, COPY every file without overwriting anything, VERIFY the copy
     (same size and SHA-256 fingerprint), only then use the new folder, and
     OFFER to delete the old files (nothing is deleted without the user's
     consent, and only copied and verified files can be).
"""

import hashlib
import logging
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from runecast.core.paths import LOCATION_FILE_NAME, AppPaths

logger = logging.getLogger(__name__)

# FR : Problèmes possibles avec un dossier de destination. Ce sont des codes :
#      l'interface les transforme en phrases, dans la langue de l'utilisateur.
# EN : Possible problems with a destination folder. These are codes: the
#      interface turns them into sentences, in the user's language.
PROBLEM_SAME = "same"  # FR : déjà utilisé / EN : already in use
PROBLEM_OVERLAP = "overlap"  # FR : mélangé aux dossiers actuels / EN : overlaps current ones
PROBLEM_NOT_A_FOLDER = "not_a_folder"  # FR : pas un dossier / EN : not a folder
PROBLEM_NOT_EMPTY = "not_empty"  # FR : pas vide / EN : not empty
PROBLEM_NOT_WRITABLE = "not_writable"  # FR : écriture impossible / EN : cannot write

# FR : Ces fichiers ne sont jamais copiés : le fichier d'emplacement reste à sa
#      place, et les fichiers « .tmp » sont des écritures inachevées.
# EN : These files are never copied: the location file stays where it is, and
#      ".tmp" files are unfinished writes.
SKIPPED_NAMES = {LOCATION_FILE_NAME}
SKIPPED_SUFFIXES = {".tmp"}


@dataclass
class CopyPlan:
    """Ce qu'il faut copier / What has to be copied."""

    # FR : paires (fichier d'origine, fichier de destination).
    # EN : (source file, destination file) pairs.
    files: list[tuple[Path, Path]] = field(default_factory=list)
    # FR : fichiers qui existent déjà dans la destination (on n'écrase jamais).
    # EN : files that already exist at the destination (never overwritten).
    conflicts: list[Path] = field(default_factory=list)
    total_bytes: int = 0


@dataclass
class CopyReport:
    """Résultat d'une copie / Result of a copy."""

    copied: list[tuple[Path, Path]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """FR : vrai si tout a été copié et vérifié. EN : true if all copied and verified."""
        return not self.errors


def human_size(size: int) -> str:
    """FR : taille lisible (« 12,3 Mo »). EN : readable size ("12,3 Mo")."""
    value = float(size)
    for unit in ("octets", "Ko", "Mo", "Go"):
        if value < 1024 or unit == "Go":
            text = f"{value:.0f}" if unit == "octets" else f"{value:.1f}"
            return f"{text.replace('.', ',')} {unit}"
        value /= 1024
    return f"{size} octets"  # pragma: no cover


def _normalized(path: Path) -> str:
    """FR : chemin comparable (Windows ne distingue pas majuscules et minuscules).

    EN : comparable path (Windows does not distinguish upper and lower case).
    """
    return os.path.normcase(str(path.resolve()))


def is_same_or_inside(path: Path, other: Path) -> bool:
    """FR : vrai si « path » est « other » ou se trouve dedans.

    EN : true if "path" is "other" or lies inside it.
    """
    path_text, other_text = _normalized(path), _normalized(other)
    return path_text == other_text or path_text.startswith(other_text.rstrip(os.sep) + os.sep)


def has_runecast_data(target: AppPaths) -> bool:
    """FR : vrai si la destination contient déjà des réglages RuneCast.

    EN : true if the destination already holds RuneCast settings.
    """
    return target.settings_file.is_file()


def check_destination(target: AppPaths, current: AppPaths) -> str | None:
    """Vérifie un dossier de destination / Check a destination folder.

    FR : Renvoie None si tout va bien, sinon un code PROBLEM_… (voir plus haut).
    EN : Returns None if all is well, otherwise a PROBLEM_… code (see above).
    """
    new_folders = list(target.folders().values())
    old_folders = list(current.folders().values())

    # FR : 1. Même emplacement qu'aujourd'hui. EN : 1. Same location as today.
    if [_normalized(f) for f in new_folders] == [_normalized(f) for f in old_folders]:
        return PROBLEM_SAME

    # FR : 2. Un dossier ne doit pas se trouver dans un autre (sinon la copie
    #      tournerait en rond). EN : 2. No folder may sit inside another one
    #      (otherwise the copy would loop).
    for new_folder in new_folders:
        for old_folder in old_folders:
            if is_same_or_inside(new_folder, old_folder) or is_same_or_inside(
                old_folder, new_folder
            ):
                return PROBLEM_OVERLAP

    # FR : 3. Dossier choisi : vide (ou déjà un dossier RuneCast) et accessible.
    # EN : 3. Chosen folder: empty (or already a RuneCast folder) and writable.
    root = target.root
    if root is not None:
        if root.exists() and not root.is_dir():
            return PROBLEM_NOT_A_FOLDER
        if root.is_dir() and any(root.iterdir()) and not has_runecast_data(target):
            return PROBLEM_NOT_EMPTY
        try:
            root.mkdir(parents=True, exist_ok=True)
            probe = root / ".runecast-test-ecriture"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
        except OSError:
            return PROBLEM_NOT_WRITABLE
    return None


def _source_files(folder: Path, other_folders: list[Path]) -> list[Path]:
    """FR : fichiers à copier dans un dossier.

         Sous Windows, le cache et les journaux sont rangés DANS le dossier des
         gros fichiers : on les saute ici, car ils sont copiés à part.
    EN : files to copy in a folder. On Windows, the cache and logs live INSIDE
         the large-files folder: they are skipped here because they are copied
         separately.
    """
    if not folder.is_dir():
        return []
    nested = [
        other for other in other_folders if other != folder and is_same_or_inside(other, folder)
    ]
    return sorted(
        path
        for path in folder.rglob("*")
        if path.is_file()
        and path.name not in SKIPPED_NAMES
        and path.suffix not in SKIPPED_SUFFIXES
        and not any(is_same_or_inside(path, other) for other in nested)
    )


def plan_copy(current: AppPaths, target: AppPaths) -> CopyPlan:
    """Prépare la copie, sans rien écrire / Prepare the copy, writing nothing."""
    plan = CopyPlan()
    current_folders = current.folders()
    all_current = list(current_folders.values())
    for name, target_folder in target.folders().items():
        source_folder = current_folders[name]
        for source in _source_files(source_folder, all_current):
            destination = target_folder / source.relative_to(source_folder)
            if destination.exists():
                plan.conflicts.append(destination)
            plan.files.append((source, destination))
            plan.total_bytes += source.stat().st_size
    return plan


def free_space(folder: Path) -> int:
    """FR : place libre sur le disque du dossier. EN : free space on the folder's disk."""
    existing = folder
    while not existing.exists() and existing.parent != existing:
        existing = existing.parent
    return shutil.disk_usage(existing).free


def _sha256(path: Path) -> str:
    """FR : empreinte SHA-256 d'un fichier. EN : SHA-256 fingerprint of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def copy_and_verify(plan: CopyPlan) -> CopyReport:
    """Copie puis vérifie chaque fichier / Copy then verify every file.

    FR : En cas d'échec, les fichiers déjà copiés (créés par cette copie) sont
         retirés de la destination : les fichiers d'origine, eux, ne sont
         jamais touchés.
    EN : On failure, the files already copied (created by this copy) are
         removed from the destination: the original files are never touched.
    """
    report = CopyReport()
    if plan.conflicts:
        report.errors.append("Des fichiers existent déjà dans la destination.")
        return report
    for source, destination in plan.files:
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            report.copied.append((source, destination))
            if source.stat().st_size != destination.stat().st_size or _sha256(source) != _sha256(
                destination
            ):
                report.errors.append(f"Copie différente de l'original : {source}")
                break
        except OSError as error:
            report.errors.append(f"{source} : {error}")
            break
    if not report.ok:
        logger.error("Copie annulée / Copy cancelled: %s", report.errors)
        for _source, destination in report.copied:
            destination.unlink(missing_ok=True)
        report.copied.clear()
    else:
        logger.info("Copie vérifiée / Copy verified: %s fichiers / files", len(report.copied))
    return report


def delete_sources(report: CopyReport, old: AppPaths) -> int:
    """Supprime les anciens fichiers copiés / Delete the copied old files.

    FR : À n'appeler qu'avec l'accord de l'utilisateur. Seuls les fichiers
         copiés ET vérifiés sont supprimés ; les dossiers devenus vides sont
         retirés. Renvoie le nombre de fichiers supprimés.
    EN : Only call with the user's consent. Only copied AND verified files are
         deleted; folders left empty are removed. Returns the number of
         deleted files.
    """
    deleted = 0
    for source, _destination in report.copied:
        try:
            source.unlink()
            deleted += 1
        except OSError as error:
            logger.warning("Ancien fichier conservé / Old file kept: %s (%s)", source, error)
    # FR : on retire les dossiers devenus vides, du plus profond au moins profond.
    # EN : remove folders left empty, deepest first.
    folders: set[Path] = set()
    for folder in old.folders().values():
        if folder.is_dir():
            folders.add(folder)
            folders.update(p for p in folder.rglob("*") if p.is_dir())
    for folder in sorted(folders, key=lambda p: len(p.parts), reverse=True):
        if folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()
    logger.info("Anciens fichiers supprimés / Old files deleted: %s", deleted)
    return deleted
