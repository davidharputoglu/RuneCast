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

"""Glossaires par jeu / Per-game glossaries.

FR : Un glossaire impose la traduction de certains termes (noms de
     personnages, lieux, objets…) pour UN jeu et UNE paire de langues.
     Application forcée : avant d'envoyer une ligne au moteur, chaque terme
     du glossaire est remplacé par un repère protégé (comme les balises
     Ren'Py, étape 11) ; le moteur ne le voit donc jamais, et RuneCast remet
     lui-même la traduction imposée. Résultat : le terme est identique
     partout. Le « rapport de contrôle » vérifie chaque ligne.
     Les termes sont reconnus en mots entiers (« Ann » ne touche pas
     « Anna »), sans tenir compte des majuscules sauf si demandé, les plus
     longs d'abord (« Old Tom » avant « Tom »).
     Rangement : un fichier JSON par glossaire (dossier « glossaires » des
     réglages), avec numéro de format. Import et export en CSV (compatible
     Excel et LibreOffice).

EN : A glossary imposes the translation of some terms (character names,
     places, items…) for ONE game and ONE language pair. Forced application:
     before a line is sent to the engine, each glossary term is replaced by a
     protected marker (like Ren'Py tags, step 11); the engine never sees it,
     and RuneCast puts the imposed translation back itself. Result: the term
     is identical everywhere. The "control report" checks every line. Terms
     match whole words ("Ann" does not touch "Anna"), ignoring case unless
     asked, longest first ("Old Tom" before "Tom"). Storage: one JSON file
     per glossary ("glossaires" folder of the settings), with a format
     number. CSV import and export (Excel and LibreOffice compatible).

     Ce module ne dépend pas de Qt. / This module does not depend on Qt.
"""

import csv
import io
import json
import os
import re
from dataclasses import dataclass, field, replace
from pathlib import Path

from runecast.core.protect import Protected, marker, protect
from runecast.core.themes import make_theme_id

# FR : Format des fichiers de glossaire. EN : Glossary file format.
GLOSSARY_FORMAT = 1
# FR : Dossier des glossaires (dans le dossier des réglages). EN : Glossaries folder.
GLOSSARY_FOLDER = "glossaires"
# FR : Colonnes du fichier CSV. EN : CSV file columns.
CSV_COLUMNS = ("source", "target", "note", "case_sensitive")
# FR : Repères déjà présents (à ne pas toucher). EN : Markers already there (left alone).
_ANY_MARKER = re.compile(r'\[\d+\]|<x id="\d+"/>')


class GlossaryError(ValueError):
    """FR : glossaire ou fichier CSV incorrect. EN : wrong glossary or CSV file."""


@dataclass
class GlossaryEntry:
    """Un terme imposé / An imposed term."""

    source: str
    target: str
    note: str = ""
    case_sensitive: bool = False

    def pattern(self) -> re.Pattern[str]:
        """FR : recherche du terme en mot entier. EN : whole-word search of the term."""
        flags = 0 if self.case_sensitive else re.IGNORECASE
        return re.compile(rf"(?<!\w){re.escape(self.source)}(?!\w)", flags)


@dataclass
class Glossary:
    """Un glossaire / A glossary."""

    glossary_id: str
    name: str
    source_lang: str = "en"
    target_lang: str = "fr"
    entries: list[GlossaryEntry] = field(default_factory=list)

    def usable_entries(self) -> list[GlossaryEntry]:
        """FR : termes complets, les plus longs d'abord. EN : complete terms, longest first."""
        entries = [e for e in self.entries if e.source.strip() and e.target.strip()]
        return sorted(entries, key=lambda e: len(e.source), reverse=True)

    def applies_to(self, source_lang: str, target_lang: str) -> bool:
        """FR : glossaire fait pour ces langues ? EN : glossary made for these languages?"""
        return (self.source_lang, self.target_lang) == (source_lang, target_lang)

    def matches(self, text: str) -> bool:
        """FR : la ligne contient-elle un terme du glossaire ? EN : does the line hold a term?"""
        return any(entry.pattern().search(text) for entry in self.usable_entries())

    def apply(self, protected: Protected) -> Protected:
        """Remplace les termes par des repères / Replace terms by markers.

        FR : Les termes sont cherchés hors des repères déjà posés (balises,
             variables) ; chaque terme trouvé devient un nouveau repère dont la
             valeur restaurée est la traduction imposée.
        EN : Terms are searched outside markers already set (tags, variables);
             each found term becomes a new marker whose restored value is the
             imposed translation.
        """
        tokens = list(protected.tokens)
        masked = protected.masked
        for entry in self.usable_entries():
            pieces = _ANY_MARKER.split(masked)
            markers = _ANY_MARKER.findall(masked)

            def put_marker(_match: re.Match[str], entry: GlossaryEntry = entry) -> str:
                tokens.append(entry.target)
                return marker(len(tokens) - 1, protected.style)

            pieces = [entry.pattern().sub(put_marker, piece) for piece in pieces]
            masked = "".join(p for pair in zip(pieces, [*markers, ""], strict=True) for p in pair)
        return replace(protected, masked=masked, tokens=tuple(tokens))

    def check(self, source: str, translation: str) -> list[GlossaryEntry]:
        """Rapport de contrôle d'une ligne / Control report of one line.

        FR : Termes imposés dans l'original (comptés comme lors de
             l'application : hors balises et variables, plus longs d'abord)
             dont la traduction imposée manque dans la traduction.
        EN : Imposed terms of the original (counted as when applying: outside
             tags and variables, longest first) whose imposed translation is
             missing from the translation.
        """
        before = protect(source)
        added = self.apply(before).tokens[len(before.tokens) :]
        missing = []
        for entry in self.usable_entries():
            expected = added.count(entry.target)
            if expected and translation.count(entry.target) < expected and entry not in missing:
                missing.append(entry)
        return missing

    # ------------------------------------------------------------------
    # FR : Fichiers / EN : Files
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "format": GLOSSARY_FORMAT,
            "id": self.glossary_id,
            "name": self.name,
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
            "entries": [entry.__dict__ for entry in self.entries],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Glossary":
        if not isinstance(data, dict) or data.get("format") != GLOSSARY_FORMAT:
            raise GlossaryError("format de glossaire inconnu / unknown glossary format")
        try:
            return cls(
                glossary_id=str(data["id"]),
                name=str(data["name"]),
                source_lang=str(data.get("source_lang", "en")),
                target_lang=str(data.get("target_lang", "fr")),
                entries=[
                    GlossaryEntry(
                        str(item["source"]),
                        str(item["target"]),
                        str(item.get("note", "")),
                        bool(item.get("case_sensitive", False)),
                    )
                    for item in data.get("entries", [])
                ],
            )
        except (KeyError, TypeError) as error:
            raise GlossaryError(f"glossaire incomplet / incomplete glossary: {error}") from error

    def to_csv(self) -> str:
        """FR : contenu CSV (en-tête + une ligne par terme). EN : CSV content."""
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(CSV_COLUMNS)
        for entry in self.entries:
            writer.writerow(
                [entry.source, entry.target, entry.note, "1" if entry.case_sensitive else ""]
            )
        return buffer.getvalue()


def read_csv(text: str) -> list[GlossaryEntry]:
    """Lit des termes au format CSV / Read terms in CSV format.

    FR : Accepte la virgule ou le point-virgule (Excel en français), avec ou
         sans ligne d'en-tête. Colonnes : terme, traduction, note, casse.
    EN : Accepts comma or semicolon (French Excel), with or without a header
         row. Columns: term, translation, note, case.
    """
    text = text.lstrip("﻿")
    if not text.strip():
        return []
    first_line = text.splitlines()[0]
    delimiter = ";" if first_line.count(";") > first_line.count(",") else ","
    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    if rows and [cell.strip().lower() for cell in rows[0][:2]] == ["source", "target"]:
        rows = rows[1:]
    entries = []
    for number, row in enumerate(rows, start=1):
        if not any(cell.strip() for cell in row):
            continue
        if len(row) < 2 or not row[0].strip() or not row[1].strip():
            raise GlossaryError(f"ligne {number} incomplète / line {number} incomplete: {row}")
        entries.append(
            GlossaryEntry(
                row[0].strip(),
                row[1].strip(),
                row[2].strip() if len(row) > 2 else "",
                len(row) > 3 and row[3].strip().lower() in ("1", "oui", "yes", "true", "x"),
            )
        )
    return entries


def glossary_folder(config_dir: Path) -> Path:
    """FR : dossier des glossaires. EN : glossaries folder."""
    return config_dir / GLOSSARY_FOLDER


def load_glossaries(folder: Path) -> dict[str, Glossary]:
    """FR : tous les glossaires (un fichier abîmé est ignoré, jamais effacé).

    EN : all glossaries (a damaged file is skipped, never deleted).
    """
    glossaries: dict[str, Glossary] = {}
    if folder.is_dir():
        for path in sorted(folder.glob("*.json")):
            try:
                glossary = Glossary.from_dict(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                continue
            glossaries[glossary.glossary_id] = glossary
    return glossaries


def save_glossary(glossary: Glossary, folder: Path) -> Path:
    """FR : enregistre un glossaire (écriture atomique). EN : save a glossary (atomic write)."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{glossary.glossary_id}.json"
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(glossary.to_dict(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)
    return path


def delete_glossary(glossary_id: str, folder: Path) -> None:
    """FR : supprime un glossaire. EN : delete a glossary."""
    (folder / f"{glossary_id}.json").unlink(missing_ok=True)


def new_glossary(name: str, taken: set[str], source_lang: str, target_lang: str) -> Glossary:
    """FR : nouveau glossaire vide, avec un identifiant libre. EN : new empty glossary."""
    return Glossary(make_theme_id(name, taken), name.strip(), source_lang, target_lang)
