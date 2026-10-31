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

"""Gestionnaire des modèles locaux / Local model manager.

FR : S'occupe des modèles de traduction installés sur le PC :
       - CATALOGUE : la liste des modèles disponibles (fichier
         resources/models/argos-catalog.json, tenu à jour dans le dépôt
         GitHub de RuneCast), avec l'adresse, la taille et l'empreinte
         SHA-256 de chacun ;
       - TÉLÉCHARGEMENT : avec reprise après coupure (le fichier « .part »
         est gardé et complété), puis vérification de l'empreinte : un
         fichier abîmé ou modifié est refusé ;
       - INSTALLATION : le modèle est d'abord décompressé à part, vérifié,
         puis mis en place d'un coup ; un fichier piégé (chemins « ../ »,
         taille démesurée) est refusé ;
       - SUPPRESSION d'un modèle ;
       - PACK HORS-LIGNE : télécharger les fichiers de modèles sur un PC
         connecté, les copier (clé USB…), puis les importer sur un PC sans
         internet.
     Les modèles sont rangés dans le dossier des données : models/argos/.

EN : Takes care of the translation models installed on the PC: CATALOGUE of
     available models (resources/models/argos-catalog.json, kept up to date
     in RuneCast's GitHub repository) with the address, size and SHA-256
     fingerprint of each; DOWNLOAD with resume after a cut (the ".part" file
     is kept and completed), then fingerprint check: a damaged or altered
     file is refused; INSTALLATION: the model is first unpacked aside,
     checked, then put in place at once; a booby-trapped file ("../" paths,
     huge size) is refused; DELETION of a model; OFFLINE PACK: download
     model files on a connected PC, copy them (USB stick…), then import them
     on a PC without internet. Models live in the data folder: models/argos/.

     Ce module ne dépend pas de Qt. / This module does not depend on Qt.
"""

import hashlib
import json
import logging
import shutil
import uuid
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from runecast.engines.argos import METADATA_FILE, ArgosPackage, ModelFormatError, from_argos
from runecast.engines.base import TranslationError
from runecast.resources import resource_path

logger = logging.getLogger(__name__)

# FR : Format du fichier catalogue. EN : Catalogue file format.
CATALOG_FORMAT = 1
# FR : Fichier ajouté par RuneCast dans chaque modèle installé.
# EN : File added by RuneCast in each installed model.
INSTALL_FILE = "runecast-install.json"
# FR : Extension des fichiers de modèles Argos. EN : Argos model file extension.
ARCHIVE_SUFFIX = ".argosmodel"
# FR : Taille maximale d'un modèle décompressé (protection). EN : Max unpacked size.
MAX_UNPACKED_BYTES = 4 * 1024**3
# FR : Taille des morceaux lus ou téléchargés. EN : Size of read or downloaded chunks.
CHUNK = 1024 * 1024
# FR : Découpeurs de texte des modèles Argos. RuneCast lit les modèles
#      « sentencepiece » ; les modèles « bpe » (15 sur 100 en octobre 2026 :
#      tchèque, danois, hongrois, indonésien…) demanderaient 5 bibliothèques
#      de plus : ils ne sont pas proposés pour l'instant.
# EN : Text splitters of Argos models. RuneCast reads "sentencepiece"
#      models; "bpe" models (15 out of 100 in October 2026: Czech, Danish,
#      Hungarian, Indonesian…) would need 5 more libraries: they are not
#      offered for now.
TOKENIZER_SENTENCEPIECE = "sentencepiece"
TOKENIZER_BPE = "bpe"

# FR : Fonction de progression : (octets faits, octets au total ou 0).
# EN : Progress function: (bytes done, total bytes or 0).
Progress = Callable[[int, int], None]


class ModelError(TranslationError):
    """FR : problème avec un modèle (téléchargement, empreinte, installation).

    EN : problem with a model (download, fingerprint, installation).
    """


class ChecksumError(ModelError):
    """FR : l'empreinte SHA-256 ne correspond pas. EN : the SHA-256 fingerprint differs."""


class DownloadCancelled(ModelError):
    """FR : téléchargement annulé par l'utilisateur. EN : download cancelled by the user."""


@dataclass(frozen=True)
class CatalogEntry:
    """Un modèle du catalogue / A catalogue model."""

    code: str  # FR : ex. « translate-en_fr » / EN : e.g. "translate-en_fr"
    from_code: str  # FR : code RuneCast / EN : RuneCast code
    to_code: str
    from_name: str
    to_name: str
    version: str
    url: str
    size: int | None = None
    sha256: str | None = None
    # FR : découpeur de texte du modèle : « sentencepiece » (pris en charge)
    #      ou « bpe » (pas encore). EN : the model's text splitter:
    #      "sentencepiece" (supported) or "bpe" (not yet).
    tokenizer: str | None = None

    @property
    def supported(self) -> bool:
        """FR : RuneCast sait-il utiliser ce modèle ? EN : can RuneCast use this model?"""
        return self.tokenizer != TOKENIZER_BPE

    @property
    def file_name(self) -> str:
        """FR : nom du fichier téléchargé. EN : downloaded file name."""
        return PurePosixPath(self.url).name


@dataclass(frozen=True)
class InstalledModel:
    """Un modèle installé / An installed model."""

    package: ArgosPackage
    size: int
    sha256: str
    installed_at: str

    @property
    def key(self) -> tuple[str, str]:
        return (self.package.from_code, self.package.to_code)


def load_catalog(path: Path | None = None, include_unsupported: bool = False) -> list[CatalogEntry]:
    """FR : lit le catalogue (celui livré avec RuneCast par défaut). Les
         modèles que RuneCast ne sait pas encore lire sont écartés, sauf
         avec « include_unsupported ».
    EN : read the catalogue (the one shipped with RuneCast by default).
         Models RuneCast cannot read yet are left out, unless
         "include_unsupported".
    """
    path = path or resource_path("models", "argos-catalog.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("format") != CATALOG_FORMAT:
        raise ModelError(f"catalogue de format inconnu / unknown catalogue format: {path}")
    entries = []
    for item in data["packages"]:
        entries.append(
            CatalogEntry(
                code=item["code"],
                from_code=from_argos(item["from_code"]),
                to_code=from_argos(item["to_code"]),
                from_name=item["from_name"],
                to_name=item["to_name"],
                version=item["version"],
                url=item["url"],
                size=item.get("size"),
                sha256=item.get("sha256"),
                tokenizer=item.get("tokenizer"),
            )
        )
    return [entry for entry in entries if include_unsupported or entry.supported]


def file_sha256(path: Path) -> str:
    """FR : empreinte SHA-256 d'un fichier. EN : SHA-256 fingerprint of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def folder_size(folder: Path) -> int:
    """FR : taille totale d'un dossier. EN : total size of a folder."""
    return sum(item.stat().st_size for item in folder.rglob("*") if item.is_file())


def models_folder(data_dir: Path) -> Path:
    """FR : dossier des modèles Argos. EN : Argos models folder."""
    return data_dir / "models" / "argos"


def _safe_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    """Vérifie le contenu d'une archive / Check an archive's content.

    FR : Refuse les chemins absolus ou qui remontent (« ../ »), et les
         archives qui prendraient une place démesurée une fois décompressées.
    EN : Refuses absolute paths or paths going up ("../"), and archives that
         would take a huge space once unpacked.
    """
    members = archive.infolist()
    total = 0
    for member in members:
        name = PurePosixPath(member.filename.replace("\\", "/"))
        if name.is_absolute() or ".." in name.parts or ":" in member.filename:
            raise ModelError(f"chemin refusé dans l'archive / refused path: {member.filename}")
        total += member.file_size
    if total > MAX_UNPACKED_BYTES:
        raise ModelError("archive trop grande une fois décompressée / archive too large")
    return members


class ModelStore:
    """Les modèles installés sur le PC / The models installed on the PC."""

    def __init__(self, folder: Path, download_folder: Path) -> None:
        self.folder = folder
        self.download_folder = download_folder

    # ------------------------------------------------------------------
    # FR : Modèles installés / EN : Installed models
    # ------------------------------------------------------------------
    def installed(self) -> dict[tuple[str, str], InstalledModel]:
        """FR : modèles installés, par sens de traduction. EN : installed models, by direction."""
        models: dict[tuple[str, str], InstalledModel] = {}
        if not self.folder.is_dir():
            return models
        for folder in sorted(self.folder.iterdir()):
            if not folder.is_dir() or folder.name.startswith("."):
                continue
            try:
                package = ArgosPackage.read(folder)
                info = json.loads((folder / INSTALL_FILE).read_text(encoding="utf-8"))
            except (ModelFormatError, OSError, ValueError) as error:
                logger.warning("Modèle ignoré / Model skipped: %s (%s)", folder, error)
                continue
            model = InstalledModel(package, info["size"], info["sha256"], info["installed_at"])
            models[model.key] = model
        return models

    def packages(self) -> dict[tuple[str, str], ArgosPackage]:
        """FR : modèles installés, pour le moteur local. EN : installed models, for the engine."""
        return {key: model.package for key, model in self.installed().items()}

    def remove(self, from_code: str, to_code: str) -> None:
        """FR : supprime un modèle installé. EN : delete an installed model."""
        model = self.installed().get((from_code, to_code))
        if model is None:
            return
        shutil.rmtree(model.package.folder)
        logger.info("Modèle supprimé / Model deleted: %s → %s", from_code, to_code)

    # ------------------------------------------------------------------
    # FR : Installation / EN : Installation
    # ------------------------------------------------------------------
    def install_archive(
        self, archive_path: Path, expected_sha256: str | None = None, source: str = ""
    ) -> InstalledModel:
        """Installe un fichier .argosmodel / Install an .argosmodel file.

        FR : Vérifie l'empreinte (si elle est connue), le contenu de
             l'archive et les fichiers du modèle, puis met le modèle en place.
             Un modèle déjà installé pour le même sens est remplacé
             seulement si tout a réussi.
        EN : Checks the fingerprint (when known), the archive content and the
             model files, then puts the model in place. A model already
             installed for the same direction is replaced only if everything
             succeeded.
        """
        sha256 = file_sha256(archive_path)
        if expected_sha256 and sha256 != expected_sha256.lower():
            raise ChecksumError(
                f"empreinte incorrecte / wrong fingerprint: {archive_path.name} "
                f"({sha256} au lieu de / instead of {expected_sha256})"
            )
        self.folder.mkdir(parents=True, exist_ok=True)
        work = self.folder / f".installation-{uuid.uuid4().hex}"
        try:
            try:
                with zipfile.ZipFile(archive_path) as archive:
                    members = _safe_members(archive)
                    if archive.testzip() is not None:
                        raise ModelError(f"archive abîmée / damaged archive: {archive_path}")
                    archive.extractall(work, members)
            except zipfile.BadZipFile as error:
                raise ModelError(f"ce n'est pas un modèle / not a model: {archive_path}") from error
            roots = [path.parent for path in work.rglob(METADATA_FILE)]
            if len(roots) != 1:
                raise ModelFormatError(f"modèle introuvable dans / no model in {archive_path}")
            package = ArgosPackage.read(roots[0])
            size = folder_size(roots[0])
            installed_at = datetime.now(UTC).isoformat(timespec="seconds")
            (roots[0] / INSTALL_FILE).write_text(
                json.dumps(
                    {
                        "sha256": sha256,
                        "size": size,
                        "installed_at": installed_at,
                        "source": source or archive_path.name,
                        "version": package.version,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            final = self.folder / f"{package.from_code}_{package.to_code}"
            old = self.folder / f".ancien-{uuid.uuid4().hex}"
            if final.exists():
                final.rename(old)
            try:
                roots[0].rename(final)
            except OSError:
                # FR : échec : l'ancien modèle est remis en place.
                # EN : failure: the previous model is put back.
                if old.exists():
                    old.rename(final)
                raise
        finally:
            shutil.rmtree(work, ignore_errors=True)
        shutil.rmtree(old, ignore_errors=True)
        logger.info(
            "Modèle installé / Model installed: %s → %s (version %s)",
            package.from_code,
            package.to_code,
            package.version,
        )
        return InstalledModel(ArgosPackage.read(final), size, sha256, installed_at)

    # ------------------------------------------------------------------
    # FR : Téléchargement / EN : Download
    # ------------------------------------------------------------------
    def download(
        self,
        entry: CatalogEntry,
        destination: Path | None = None,
        progress: Progress | None = None,
        should_cancel: Callable[[], bool] | None = None,
        client=None,
    ) -> Path:
        """Télécharge un modèle, avec reprise / Download a model, with resume.

        FR : Le fichier en cours s'appelle « nom.part » : s'il existe déjà
             (téléchargement coupé), on demande seulement la suite. À la fin,
             l'empreinte est vérifiée.
        EN : The file in progress is called "name.part": if it already exists
             (interrupted download), only the rest is requested. At the end,
             the fingerprint is checked.
        """
        import httpx

        folder = destination or self.download_folder
        folder.mkdir(parents=True, exist_ok=True)
        final = folder / entry.file_name
        partial = folder / (entry.file_name + ".part")
        own_client = client is None
        client = client or httpx.Client(follow_redirects=True, timeout=60)
        try:
            done = partial.stat().st_size if partial.exists() else 0
            headers = {"Range": f"bytes={done}-"} if done else {}
            with client.stream("GET", entry.url, headers=headers) as response:
                if response.status_code == 416:  # FR : déjà complet / EN : already complete
                    pass
                else:
                    if response.status_code not in (200, 206):
                        raise ModelError(
                            f"téléchargement refusé / download refused ({response.status_code}): "
                            f"{entry.url}"
                        )
                    if response.status_code == 200:
                        done = 0  # FR : le serveur recommence au début / EN : restarted
                    length = int(response.headers.get("Content-Length") or 0)
                    total = entry.size or (done + length if length else 0)
                    with partial.open("ab" if done else "wb") as handle:
                        for block in response.iter_bytes(CHUNK):
                            if should_cancel is not None and should_cancel():
                                raise DownloadCancelled(entry.file_name)
                            handle.write(block)
                            done += len(block)
                            if progress is not None:
                                progress(done, total)
        except httpx.HTTPError as error:
            raise ModelError(
                f"téléchargement interrompu / download interrupted: {error}"
            ) from error
        finally:
            if own_client:
                client.close()
        sha256 = file_sha256(partial)
        if entry.sha256 and sha256 != entry.sha256.lower():
            partial.unlink()
            raise ChecksumError(f"empreinte incorrecte / wrong fingerprint: {entry.file_name}")
        partial.replace(final)
        logger.info("Modèle téléchargé / Model downloaded: %s", entry.file_name)
        return final

    def download_and_install(
        self,
        entry: CatalogEntry,
        progress: Progress | None = None,
        should_cancel: Callable[[], bool] | None = None,
        client=None,
    ) -> InstalledModel:
        """FR : télécharge puis installe ; le fichier téléchargé est ensuite effacé.

        EN : download then install; the downloaded file is then erased.
        """
        archive = self.download(entry, None, progress, should_cancel, client)
        try:
            return self.install_archive(archive, entry.sha256, source=entry.url)
        finally:
            archive.unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # FR : Pack hors-ligne / EN : Offline pack
    # ------------------------------------------------------------------
    def import_files(
        self, archives: list[Path], catalog: list[CatalogEntry]
    ) -> list[InstalledModel]:
        """Importe des fichiers .argosmodel (pack hors-ligne) / Import offline pack files.

        FR : Si un fichier est connu du catalogue, son empreinte est vérifiée.
             Les fichiers d'origine ne sont ni modifiés ni effacés.
        EN : When a file is known to the catalogue, its fingerprint is
             checked. The original files are neither changed nor erased.
        """
        known = {entry.file_name: entry.sha256 for entry in catalog}
        return [
            self.install_archive(path, known.get(path.name), source=str(path)) for path in archives
        ]
