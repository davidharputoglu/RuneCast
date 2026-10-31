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

"""Tests de la protection des balises et variables (étape 11).

FR : Une centaine de cas tirés de vrais jeux Ren'Py : chaque élément protégé
     doit revenir intact, et chaque erreur possible d'un moteur de traduction
     doit être détectée (la ligne est alors « à vérifier »).
EN : About a hundred cases taken from real Ren'Py games: every protected item
     must come back intact, and every possible mistake of a translation
     engine must be detected (the line is then "to check").
"""

import subprocess
import sys

import pytest

from runecast.core.protect import (
    PROBLEM_DUPLICATED,
    PROBLEM_EMPTY,
    PROBLEM_MISSING,
    PROBLEM_SPECIAL,
    PROBLEM_TAG_ORDER,
    PROBLEM_UNKNOWN,
    STYLE_XML,
    protect,
    restore,
)

# FR : (texte d'origine, texte envoyé au moteur, éléments protégés)
# EN : (original text, text sent to the engine, protected items)
PROTECT_CASES = [
    # FR : texte simple / EN : plain text
    ("Hello.", "Hello.", ()),
    ("Bonjour, comment ça va ?", "Bonjour, comment ça va ?", ()),
    ("Привет, мир!", "Привет, мир!", ()),
    ("مرحبا بالعالم", "مرحبا بالعالم", ()),
    ("100% sure", "100% sure", ()),
    ("It's 50% off!", "It's 50% off!", ()),
    ("Email me at a@b.c", "Email me at a@b.c", ()),
    # FR : balises de mise en forme / EN : formatting tags
    ("{b}Bold{/b}", "[0]Bold[1]", ("{b}", "{/b}")),
    ("{i}Italic{/i} text", "[0]Italic[1] text", ("{i}", "{/i}")),
    ("{u}Under{/u}", "[0]Under[1]", ("{u}", "{/u}")),
    ("{s}Strike{/s}", "[0]Strike[1]", ("{s}", "{/s}")),
    ("{plain}Plain{/plain}", "[0]Plain[1]", ("{plain}", "{/plain}")),
    ("{color=#f00}Red{/color}", "[0]Red[1]", ("{color=#f00}", "{/color}")),
    ("{color=#ff000080}Alpha{/color}", "[0]Alpha[1]", ("{color=#ff000080}", "{/color}")),
    ("{size=+10}Big{/size}", "[0]Big[1]", ("{size=+10}", "{/size}")),
    ("{size=-5}small{/size}", "[0]small[1]", ("{size=-5}", "{/size}")),
    ("{size=30}Thirty{/size}", "[0]Thirty[1]", ("{size=30}", "{/size}")),
    ("{font=DejaVuSans.ttf}Font{/font}", "[0]Font[1]", ("{font=DejaVuSans.ttf}", "{/font}")),
    ("{outlinecolor=#000}O{/outlinecolor}", "[0]O[1]", ("{outlinecolor=#000}", "{/outlinecolor}")),
    ("{alpha=0.5}Ghost{/alpha}", "[0]Ghost[1]", ("{alpha=0.5}", "{/alpha}")),
    ("{k=-.5}Tight{/k}", "[0]Tight[1]", ("{k=-.5}", "{/k}")),
    ("{a=https://renpy.org}site{/a}", "[0]site[1]", ("{a=https://renpy.org}", "{/a}")),
    ("{a=jump:start}Restart{/a}", "[0]Restart[1]", ("{a=jump:start}", "{/a}")),
    ("{cps=20}Slow{/cps}", "[0]Slow[1]", ("{cps=20}", "{/cps}")),
    ("{cps=*2}Fast{/cps}", "[0]Fast[1]", ("{cps=*2}", "{/cps}")),
    ("{b}{i}Both{/i}{/b}", "[0][1]Both[2][3]", ("{b}", "{i}", "{/i}", "{/b}")),
    (
        "{rb}東京{/rb}{rt}とうきょう{/rt}",
        "[0]東京[1][2]とうきょう[3]",
        ("{rb}", "{/rb}", "{rt}", "{/rt}"),
    ),
    ("{alt}Heart{/alt}♥", "[0]Heart[1]♥", ("{alt}", "{/alt}")),
    ("{noalt}♥{/noalt}", "[0]♥[1]", ("{noalt}", "{/noalt}")),
    ("{shader=jitter}Shake{/shader}", "[0]Shake[1]", ("{shader=jitter}", "{/shader}")),
    # FR : balises sans fermeture / EN : tags without closing
    ("Wait{w} for it.", "Wait[0] for it.", ("{w}",)),
    ("Wait{w=0.5} a bit.", "Wait[0] a bit.", ("{w=0.5}",)),
    ("Line one.{p}Line two.", "Line one.[0]Line two.", ("{p}",)),
    ("Line one.{p=1.0}Two.", "Line one.[0]Two.", ("{p=1.0}",)),
    ("Interrupted{nw}", "Interrupted[0]", ("{nw}",)),
    ("{fast}Shown at once.", "[0]Shown at once.", ("{fast}",)),
    ("Look {image=heart.png} here", "Look [0] here", ("{image=heart.png}",)),
    ("A{space=20}B", "A[0]B", ("{space=20}",)),
    ("Top{vspace=10}Bottom", "Top[0]Bottom", ("{vspace=10}",)),
    ("Part one{done} part two", "Part one[0] part two", ("{done}",)),
    ("{clear}New page", "[0]New page", ("{clear}",)),
    ("Text{#this is a comment}", "Text[0]", ("{#this is a comment}",)),
    # FR : variables / EN : variables (interpolation)
    ("Hello, [player]!", "Hello, [0]!", ("[player]",)),
    ("Hi [player_name].", "Hi [0].", ("[player_name]",)),
    ("[mc!t] arrives.", "[0] arrives.", ("[mc!t]",)),
    ("[mc!u] SHOUTS.", "[0] SHOUTS.", ("[mc!u]",)),
    ("[mc!c] starts.", "[0] starts.", ("[mc!c]",)),
    ("[name!q] said.", "[0] said.", ("[name!q]",)),
    ("Score: [points:03d]", "Score: [0]", ("[points:03d]",)),
    ("You have [inventory.gold] gold.", "You have [0] gold.", ("[inventory.gold]",)),
    ("First item: [items[0]]", "First item: [0]", ("[items[0]]",)),
    ("[a] and [b]", "[0] and [1]", ("[a]", "[b]")),
    ("[day_names[weekday]] morning", "[0] morning", ("[day_names[weekday]]",)),
    ("{b}[player]{/b} wins", "[0][1][2] wins", ("{b}", "[player]", "{/b}")),
    # FR : échappements / EN : escapes
    ("Use {{braces}}", "Use [0]braces[1]", ("{{", "}}")),
    ("Literal [[bracket]", "Literal [0]bracket]", ("[[",)),
    ("Old style 100%%", "Old style 100[0]", ("%%",)),
    ("First\\nSecond", "First[0]Second", ("\\n",)),
    ('He said \\"hi\\"', "He said [0]hi[1]", ('\\"', '\\"')),
    ("Tab\\there", "Tab[0]here", ("\\t",)),
    ("Back\\\\slash", "Back[0]slash", ("\\\\",)),
    ("Real\nnewline", "Real[0]newline", ("\n",)),
    # FR : formats Python / EN : Python formats
    ("You have %d coins.", "You have [0] coins.", ("%d",)),
    ("Hello %s!", "Hello [0]!", ("%s",)),
    ("Ratio %.2f", "Ratio [0]", ("%.2f",)),
    ("Width %5d", "Width [0]", ("%5d",)),
    ("Left %-10s|", "Left [0]|", ("%-10s",)),
    ("Hi %(name)s, you have %(count)d", "Hi [0], you have [1]", ("%(name)s", "%(count)d")),
    ("Value {0}", "Value [0]", ("{0}",)),
    ("Pair {0} and {1}", "Pair [0] and [1]", ("{0}", "{1}")),
    ("Named {player}", "Named [0]", ("{player}",)),
    ("Empty {}", "Empty [0]", ("{}",)),
    # FR : mélanges réalistes / EN : realistic mixes
    (
        "{i}[mc]{/i}: I need %d more{w=.3}... {b}now{/b}!",
        "[0][1][2]: I need [3] more[4]... [5]now[6]!",
        ("{i}", "[mc]", "{/i}", "%d", "{w=.3}", "{b}", "{/b}"),
    ),
    (
        "{color=[accent]}Warning{/color}",
        "[0]Warning[1]",
        ("{color=[accent]}", "{/color}"),
    ),
    ("{size=+5}{b}TITLE{/b}{/size}", "[0][1]TITLE[2][3]", ("{size=+5}", "{b}", "{/b}", "{/size}")),
    ("Choice: [[A] or [[B]", "Choice: [0]A] or [1]B]", ("[[", "[[")),
]


@pytest.mark.parametrize(("source", "masked", "tokens"), PROTECT_CASES)
def test_protect(source: str, masked: str, tokens: tuple[str, ...]) -> None:
    """FR : ce qui est envoyé au moteur. EN : what is sent to the engine."""
    protected = protect(source)
    assert protected.masked == masked
    assert protected.tokens == tokens


@pytest.mark.parametrize(("source", "masked", "tokens"), PROTECT_CASES)
def test_round_trip_gives_back_the_original(
    source: str, masked: str, tokens: tuple[str, ...]
) -> None:
    """FR : sans traduction, on retrouve exactement l'original.

    EN : without translation, the original comes back exactly.
    """
    protected = protect(source)
    result = restore(protected.masked, protected)
    assert result.ok, result.problems
    assert result.text == source


# FR : (original, traduction renvoyée par le moteur, résultat attendu)
# EN : (original, translation returned by the engine, expected result)
TRANSLATION_CASES = [
    ("{b}Hello{/b} [player]!", "[0]Bonjour[1] [2] !", "{b}Bonjour{/b} [player] !"),
    ("Hello, [player]!", "Привет, [0]!", "Привет, [player]!"),
    ("Hello, [player]!", "[0]، مرحبا!", "[player]، مرحبا!"),
    # FR : le moteur change l'ordre des mots / EN : the engine reorders words
    ("[a] likes [b].", "[1] est aimé par [0].", "[b] est aimé par [a]."),
    # FR : espaces ajoutés dans les repères / EN : spaces added inside markers
    ("Hi [player]", "Salut [ 0 ]", "Salut [player]"),
    # FR : crochets japonais/chinois / EN : CJK brackets
    ("Hi [player]", "こんにちは［0］", "こんにちは[player]"),
    # FR : espaces du début et de la fin gardés / EN : leading/trailing spaces kept
    ("  indented  ", "indenté", "  indenté  "),
    (" {w}Hi", "[0]Salut", " {w}Salut"),
    ("Go{nw}", "Vas-y[0]", "Vas-y{nw}"),
    ("You have %d coins.", "Tu as [0] pièces.", "Tu as %d pièces."),
    ("First\\nSecond", "Premier[0]Second", "Premier\\nSecond"),
    ("{{x}}", "[0]x[1]", "{{x}}"),
]


@pytest.mark.parametrize(("source", "translated", "expected"), TRANSLATION_CASES)
def test_translation_is_restored(source: str, translated: str, expected: str) -> None:
    """FR : la traduction retrouve ses balises et variables. EN : tags and variables come back."""
    result = restore(translated, protect(source))
    assert result.ok, result.problems
    assert result.text == expected


# FR : (original, traduction fautive, problème attendu)
# EN : (original, faulty translation, expected problem)
PROBLEM_CASES = [
    ("Hello, [player]!", "Bonjour !", PROBLEM_MISSING),
    ("{b}Hi{/b}", "[0]Salut", PROBLEM_MISSING),
    ("Hello, [player]!", "Bonjour [0], [0] !", PROBLEM_DUPLICATED),
    ("Hello, [player]!", "Bonjour [0] [5] !", PROBLEM_UNKNOWN),
    ("{b}Hi{/b}", "[1]Salut[0]", PROBLEM_TAG_ORDER),
    ("{b}{i}Hi{/i}{/b}", "[0][1]Salut[3][2]", PROBLEM_TAG_ORDER),
    ("Hello", "Bonjour [option]", PROBLEM_SPECIAL),
    ("Hello", "Bonjour {", PROBLEM_SPECIAL),
    ("Hello", "Bonjour }", PROBLEM_SPECIAL),
    ("Hello", "", PROBLEM_EMPTY),
    ("Hello, [player]!", "   ", PROBLEM_MISSING),
    ("Hello, [player]!", "[0]", None),  # FR : accepté : il reste la variable / EN : accepted
]


@pytest.mark.parametrize(("source", "translated", "problem"), PROBLEM_CASES)
def test_engine_mistakes_are_detected(source: str, translated: str, problem: str | None) -> None:
    """FR : chaque erreur possible d'un moteur est repérée. EN : every engine mistake is caught."""
    result = restore(translated, protect(source))
    if problem is None:
        assert result.ok
    else:
        assert problem in result.problems
        assert not result.ok


def test_stray_bracket_already_in_original_is_fine() -> None:
    """FR : le « ] » de « [[x] » existe déjà dans l'original : pas une erreur.

    EN : the "]" of "[[x]" is already in the original: not an error.
    """
    result = restore("Littéral [0]crochet]", protect("Literal [[bracket]"))
    assert result.ok
    assert result.text == "Littéral [[crochet]"


@pytest.mark.parametrize(
    ("source", "translatable"),
    [
        ("Hello", True),
        ("{w}", False),
        ("[player]", False),
        ("{b}[player]{/b}", False),
        ("...", False),
        ("{p}!", False),
        ("[player]?", False),
        ("Yes", True),
        ("  ", False),
        ("Ок", True),
    ],
)
def test_translatable(source: str, translatable: bool) -> None:
    """FR : une ligne sans mots n'est pas envoyée au moteur. EN : wordless lines are skipped."""
    assert protect(source).translatable is translatable


def test_xml_style() -> None:
    """FR : repères au format XML, pour les moteurs qui comprennent le HTML.

    EN : XML-style markers, for engines that understand HTML.
    """
    protected = protect("{b}Hello{/b} [player]!", style=STYLE_XML)
    assert protected.masked == '<x id="0"/>Hello<x id="1"/> <x id="2"/>!'
    returned = "<x id='0'></x>Bonjour<x id=\"1\"/> <x id=2 /> !"
    result = restore(returned, protected)
    assert result.ok, result.problems
    assert result.text == "{b}Bonjour{/b} [player] !"


def test_xml_style_detects_missing_marker() -> None:
    """FR : style XML : un repère perdu est détecté. EN : XML style: a lost marker is caught."""
    result = restore("Bonjour", protect("Hi [player]", style=STYLE_XML))
    assert PROBLEM_MISSING in result.problems


def test_unknown_style_is_refused() -> None:
    """FR : style inconnu refusé. EN : unknown style refused."""
    with pytest.raises(ValueError):
        protect("Hi", style="bizarre")


def test_command_line_demo() -> None:
    """FR : démonstration en ligne de commande : « runecast --protect ».

    EN : command-line demonstration: "runecast --protect".
    """
    completed = subprocess.run(
        [sys.executable, "-m", "runecast", "--protect", "{b}Bonjour{/b} [player] !"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    assert "[0]Bonjour[1] [2] !" in completed.stdout
    assert "[2] = [player]" in completed.stdout
