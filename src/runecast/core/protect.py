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

"""Protection des balises et des variables / Protecting tags and variables.

FR : Avant d'envoyer une réplique à un moteur de traduction, tout ce qui ne
     doit PAS être traduit est remplacé par un repère numéroté, par exemple :

         {b}Bonjour{/b} [player] !   →   [0]Bonjour[1] [2] !

     Le moteur traduit le texte en gardant les repères ; RuneCast remet
     ensuite chaque élément d'origine à sa place, puis CONTRÔLE le résultat.
     Si un repère a disparu, est en double, si les balises sont dans le
     désordre, ou si la traduction contient un caractère spécial de Ren'Py
     qui ferait planter le jeu (« [ », « { »…), la ligne est marquée
     « à vérifier » au lieu d'être écrite dans le jeu.

     Sont protégés :
       - les balises de texte Ren'Py : {b}, {i}, {u}, {s}, {color=…},
         {size=…}, {font=…}, {a=…}, {w}, {p}, {nw}, {fast}, {cps=…},
         {image=…}, {rb}/{rt}… et leurs fermetures {/b}… ;
       - les variables (interpolations) : [player], [player!t], [obj.attr],
         [items[0]] ;
       - les échappements : {{, [[, %%, \\n, \\" … ;
       - les formats Python : %s, %d, %(nom)s, %.2f, {0}, {nom} ;
       - les retours à la ligne et les espaces au début et à la fin.

EN : Before a line is sent to a translation engine, everything that must NOT
     be translated is replaced by a numbered marker (see the example above).
     The engine translates the text and keeps the markers; RuneCast then puts
     every original element back and CHECKS the result. If a marker is
     missing or duplicated, if the tags are out of order, or if the
     translation contains a Ren'Py special character that would crash the
     game ("[", "{"…), the line is marked "to check" instead of being written
     into the game. Protected items are listed above.

     Ce module ne dépend pas de Qt. / This module does not depend on Qt.
"""

import re
from dataclasses import dataclass, field

# FR : Deux façons d'écrire les repères :
#        - « crochets » : [0], [1]… (bien gardés par la plupart des moteurs) ;
#        - « xml » : <x id="0"/>… (pour les moteurs qui comprennent le HTML).
# EN : Two ways to write the markers: "brackets" [0], [1]… (kept well by most
#      engines); "xml" <x id="0"/>… (for engines that understand HTML).
STYLE_BRACKETS = "brackets"
STYLE_XML = "xml"
STYLES = (STYLE_BRACKETS, STYLE_XML)

# FR : Codes des problèmes détectés au contrôle. EN : Problem codes found by the check.
PROBLEM_MISSING = "missing"  # FR : repère disparu / EN : marker lost
PROBLEM_DUPLICATED = "duplicated"  # FR : repère en double / EN : marker twice
PROBLEM_UNKNOWN = "unknown"  # FR : repère inventé par le moteur / EN : marker made up
PROBLEM_TAG_ORDER = "tag_order"  # FR : balises dans le désordre / EN : tags out of order
PROBLEM_SPECIAL = "special"  # FR : « [ », « { »… isolé / EN : stray "[", "{"…
PROBLEM_EMPTY = "empty"  # FR : traduction vide / EN : empty translation

# FR : Les éléments à protéger, du plus long au plus court. L'ordre compte :
#      « {{ » doit être reconnu avant une balise « {…} ».
# EN : The items to protect, longest first. Order matters: "{{" must be
#      recognised before a "{…}" tag.
_PROTECTED = re.compile(
    r"""
      \{\{ | \}\} | \[\[ | \]\] | %%               # échappements / escapes
    | \\[nt"'\\]                                  # \n, \t, \", \', \\ écrits tels quels
    | \{[^{}\n]*\}                                # balise Ren'Py ou {0} / tag or {0}
    | \[(?:[^\[\]\n]|\[[^\[\]\n]*\])*\]           # variable [nom], [a[0]] / variable
    | %(?:\([^()\n]*\))?[-#0+]*(?:\d+|\*)?(?:\.\d+)?[sdifouxXeEgGcr]  # %s, %(nom)s
    | \n                                          # vrai retour à la ligne / real newline
    """,
    re.VERBOSE,
)

# FR : Balise de texte Ren'Py qui s'ouvre ou se ferme : {b}, {/b}, {color=#f00}…
# EN : Ren'Py text tag that opens or closes: {b}, {/b}, {color=#f00}…
_TAG = re.compile(r"^\{(/?)([a-z#][a-z_]*)(?:=[^{}]*)?\}$")

# FR : Balises Ren'Py qui ne se ferment pas (elles agissent à un endroit précis).
# EN : Ren'Py tags that are not closed (they act at one precise point).
SELF_CLOSING_TAGS = frozenset(
    {"w", "p", "nw", "fast", "image", "space", "vspace", "done", "clear", "#"}
)

# FR : Repères tels que les moteurs peuvent les renvoyer : « [ 0 ] », « ［0］ »
#      (crochets chinois/japonais), « <x id='0'> »…
# EN : Markers as engines may send them back: "[ 0 ]", "［0］" (CJK
#      brackets), "<x id='0'>"…
_MARKERS = {
    STYLE_BRACKETS: re.compile(r"[\[［]\s*(\d{1,4})\s*[\]］]"),
    STYLE_XML: re.compile(
        r"""<\s*x\s+id\s*=\s*["']?(\d{1,4})["']?\s*/?\s*>(?:\s*<\s*/\s*x\s*>)?"""
    ),
}

# FR : Caractères spéciaux de Ren'Py qui ne doivent jamais rester isolés.
# EN : Ren'Py special characters that must never be left alone.
_SPECIAL = re.compile(r"[\[\]{}]")


@dataclass(frozen=True)
class Protected:
    """Une réplique protégée / A protected line.

    FR : « masked » est le texte envoyé au moteur ; « tokens » sont les
         éléments d'origine, dans l'ordre des repères 0, 1, 2…
    EN : "masked" is the text sent to the engine; "tokens" are the original
         items, in the order of markers 0, 1, 2…
    """

    source: str
    masked: str
    tokens: tuple[str, ...]
    leading: str = ""  # FR : espaces du début / EN : leading spaces
    trailing: str = ""  # FR : espaces de la fin / EN : trailing spaces
    style: str = STYLE_BRACKETS

    @property
    def translatable(self) -> bool:
        """FR : reste-t-il des mots à traduire ? (« {w} » seul : non).

        EN : is there anything left to translate? ("{w}" alone: no).
        """
        without_markers = _MARKERS[self.style].sub("", self.masked)
        return any(character.isalpha() for character in without_markers)


@dataclass
class Restored:
    """Résultat de la restauration / Result of the restoration."""

    text: str
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """FR : True si la ligne peut être écrite dans le jeu.

        EN : True if the line can be written into the game.
        """
        return not self.problems


def marker(index: int, style: str = STYLE_BRACKETS) -> str:
    """FR : repère numéro « index ». EN : marker number "index"."""
    if style == STYLE_XML:
        return f'<x id="{index}"/>'
    return f"[{index}]"


def protect(text: str, style: str = STYLE_BRACKETS) -> Protected:
    """Protège une réplique / Protect a line.

    FR : Exemple : protect("{i}Salut{/i} [mc] !").masked == "[0]Salut[1] [2] !"
    EN : Example: see above.
    """
    if style not in STYLES:
        raise ValueError(f"style inconnu / unknown style: {style}")
    core = text.strip()
    start = text.find(core) if core else len(text)
    leading, trailing = text[:start], text[start + len(core) :]
    tokens: list[str] = []

    def replace(match: re.Match[str]) -> str:
        tokens.append(match.group(0))
        return marker(len(tokens) - 1, style)

    masked = _PROTECTED.sub(replace, core)
    return Protected(text, masked, tuple(tokens), leading, trailing, style)


def _tag_order_ok(tokens: list[str]) -> bool:
    """FR : les balises ouvertes sont-elles fermées dans le bon ordre ?

    EN : are opened tags closed in the right order?
    """
    stack: list[str] = []
    for token in tokens:
        match = _TAG.match(token)
        if not match:
            continue
        closing, name = match.groups()
        if name in SELF_CLOSING_TAGS:
            continue
        if not closing:
            stack.append(name)
        elif not stack or stack.pop() != name:
            return False
    return True


def restore(translated: str, protected: Protected) -> Restored:
    """Remet les éléments protégés et contrôle / Put protected items back and check.

    FR : Renvoie le texte final et la liste des problèmes trouvés (vide si
         tout va bien). Une ligne avec un problème ne doit pas être écrite
         dans le jeu : elle est à vérifier par l'utilisateur.
    EN : Returns the final text and the list of problems found (empty if all
         is well). A line with a problem must not be written into the game:
         the user has to check it.
    """
    problems: list[str] = []
    pattern = _MARKERS[protected.style]
    found = [int(index) for index in pattern.findall(translated)]
    expected = range(len(protected.tokens))

    if any(index not in expected for index in found):
        problems.append(PROBLEM_UNKNOWN)
    if any(found.count(index) > 1 for index in expected):
        problems.append(PROBLEM_DUPLICATED)
    if any(index not in found for index in expected):
        problems.append(PROBLEM_MISSING)

    # FR : un « [ » ou un « { » AJOUTÉ par le moteur ferait planter Ren'Py
    #      (ceux déjà présents dans l'original, comme le « ] » de « [[x] », sont normaux).
    # EN : a "[" or "{" ADDED by the engine would crash Ren'Py (those already
    #      in the original, like the "]" of "[[x]", are normal).
    before = _SPECIAL.findall(pattern.sub("", protected.masked))
    after = _SPECIAL.findall(pattern.sub("", translated))
    if any(after.count(character) > before.count(character) for character in set(after)):
        problems.append(PROBLEM_SPECIAL)

    def put_back(match: re.Match[str]) -> str:
        index = int(match.group(1))
        return protected.tokens[index] if index < len(protected.tokens) else match.group(0)

    core = pattern.sub(put_back, translated.strip())
    if protected.translatable and not core.strip():
        problems.append(PROBLEM_EMPTY)

    order = [protected.tokens[i] for i in found if i < len(protected.tokens)]
    if _tag_order_ok(list(protected.tokens)) and not _tag_order_ok(order):
        problems.append(PROBLEM_TAG_ORDER)

    return Restored(protected.leading + core + protected.trailing, problems)
