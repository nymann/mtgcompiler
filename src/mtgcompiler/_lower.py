"""Lower the Lark parse tree to the public semantic AST.

This module operates on the **Lark parse tree** rather than the Mg* IR
produced by ``MtgJsonTransformer``. That transformer carries pre-existing
import gaps for many keyword classes and is under active development;
the Lark tree is the stable surface.

Patterns the lowerer doesn't recognize raise :class:`LoweringIncomplete`,
which ``mtgcompiler.parse`` converts into
``ParseError(kind="incomplete")``.
"""
from __future__ import annotations

from typing import Iterable

from lark import Token, Tree

from mtgcompiler.ast import (
    Ability,
    Card,
    Keyword,
    KeywordAbility,
)


class LoweringIncomplete(Exception):
    """Raised when the lowerer hits a parse-tree shape it doesn't yet handle.

    Message format is a short, machine-grep-able label (e.g.
    ``"unknown-keyword:kwward"``) so it can flow straight into
    ``ParseError.message``.
    """


# ---------------------------------------------------------------------------
# Keyword grammar-rule -> Keyword enum
# ---------------------------------------------------------------------------


# The grammar emits a rule like ``kwflying`` for each keyword ability. The
# rule name is the keyword's lowercase identifier prefixed with "kw"; for
# multi-word keywords ("first strike", "double strike") the prefix is the
# same but the spelling collapses ("kwfirststrike", "kwdoublestrike").
_KEYWORD_BY_RULE: dict[str, Keyword] = {
    "kwflying": Keyword.FLYING,
    "kwtrample": Keyword.TRAMPLE,
    "kwfirststrike": Keyword.FIRST_STRIKE,
    "kwdoublestrike": Keyword.DOUBLE_STRIKE,
    "kwdeathtouch": Keyword.DEATHTOUCH,
    "kwlifelink": Keyword.LIFELINK,
    "kwhaste": Keyword.HASTE,
    "kwvigilance": Keyword.VIGILANCE,
    "kwreach": Keyword.REACH,
    "kwmenace": Keyword.MENACE,
    "kwhexproof": Keyword.HEXPROOF,
    "kwshroud": Keyword.SHROUD,
    "kwindestructible": Keyword.INDESTRUCTIBLE,
    "kwflash": Keyword.FLASH,
    "kwdefender": Keyword.DEFENDER,
    "kwintimidate": Keyword.INTIMIDATE,
    "kwfear": Keyword.FEAR,
    "kwshadow": Keyword.SHADOW,
    "kwhorsemanship": Keyword.HORSEMANSHIP,
    "kwprowess": Keyword.PROWESS,
    "kwchangeling": Keyword.CHANGELING,
    "kwequip": Keyword.EQUIP,
    "kwward": Keyword.WARD,
    "kwprotection": Keyword.PROTECTION,
    "kwlandwalk": Keyword.LANDWALK,
    "kwcycling": Keyword.CYCLING,
    "kwkicker": Keyword.KICKER,
    "kwflashback": Keyword.FLASHBACK,
    "kwbuyback": Keyword.BUYBACK,
    "kwenchant": Keyword.ENCHANT,
    "kwbanding": Keyword.BANDING,
    "kwrampage": Keyword.RAMPAGE,
    "kwbushido": Keyword.BUSHIDO,
    "kwannihilator": Keyword.ANNIHILATOR,
    "kwfading": Keyword.FADING,
    "kwvanishing": Keyword.VANISHING,
    "kwsuspend": Keyword.SUSPEND,
    "kwmorph": Keyword.MORPH,
    "kwamplify": Keyword.AMPLIFY,
    "kwmodular": Keyword.MODULAR,
    "kwaffinity": Keyword.AFFINITY,
    "kwsoulshift": Keyword.SOULSHIFT,
    "kwdredge": Keyword.DREDGE,
    "kwbloodthirst": Keyword.BLOODTHIRST,
    "kwgraft": Keyword.GRAFT,
    "kwpoisonous": Keyword.POISONOUS,
    "kwdevour": Keyword.DEVOUR,
    "kwninjutsu": Keyword.NINJUTSU,
    "kwtransmute": Keyword.TRANSMUTE,
    "kwreplicate": Keyword.REPLICATE,
    "kwrecover": Keyword.RECOVER,
    "kwsplice": Keyword.SPLICE,
    "kwoffering": Keyword.OFFERING,
    "kwchampion": Keyword.CHAMPION,
    "kwevoke": Keyword.EVOKE,
    "kwprowl": Keyword.PROWL,
    "kwreinforce": Keyword.REINFORCE,
    "kwunearth": Keyword.UNEARTH,
    "kwlevelup": Keyword.LEVEL_UP,
    "kwmiracle": Keyword.MIRACLE,
    "kwoverload": Keyword.OVERLOAD,
    "kwscavenge": Keyword.SCAVENGE,
    "kwbestow": Keyword.BESTOW,
    "kwoutlast": Keyword.OUTLAST,
    "kwdash": Keyword.DASH,
    "kwawaken": Keyword.AWAKEN,
    "kwsurge": Keyword.SURGE,
    "kwemerge": Keyword.EMERGE,
    "kwescalate": Keyword.ESCALATE,
    "kwcrew": Keyword.CREW,
    "kwfabricate": Keyword.FABRICATE,
    "kwpartner": Keyword.PARTNER,
    "kwembalm": Keyword.EMBALM,
    "kwenbalm": Keyword.EMBALM,  # grammar misspelling tolerance
    "kweternalize": Keyword.ETERNALIZE,
    "kwafflict": Keyword.AFFLICT,
    "kwsurveil": Keyword.SURVEIL,
    "kwjumpstart": Keyword.JUMP_START,
    "kwfortify": Keyword.FORTIFY,
    "kwentwine": Keyword.ENTWINE,
    "kwmadness": Keyword.MADNESS,
    "kwmultikicker": Keyword.MULTIKICKER,
    "kwcascade": Keyword.CASCADE,
    "kwstorm": Keyword.STORM,
    "kwsunburst": Keyword.SUNBURST,
    "kwconvoke": Keyword.CONVOKE,
    "kwdelve": Keyword.DELVE,
    "kwgravestorm": Keyword.GRAVESTORM,
    "kwrebound": Keyword.REBOUND,
    "kwtotemarmor": Keyword.TOTEM_ARMOR,
    "kwinfect": Keyword.INFECT,
    "kwbattlecry": Keyword.BATTLE_CRY,
    "kwlivingweapon": Keyword.LIVING_WEAPON,
    "kwundying": Keyword.UNDYING,
    "kwsoulbond": Keyword.SOULBOND,
    "kwunleash": Keyword.UNLEASH,
    "kwcipher": Keyword.CIPHER,
    "kwevolve": Keyword.EVOLVE,
    "kwextort": Keyword.EXTORT,
    "kwfuse": Keyword.FUSE,
    "kwdethrone": Keyword.DETHRONE,
    "kwexploit": Keyword.EXPLOIT,
    "kwdevoid": Keyword.DEVOID,
    "kwingest": Keyword.INGEST,
    "kwmyriad": Keyword.MYRIAD,
    "kwskulk": Keyword.SKULK,
    "kwmelee": Keyword.MELEE,
    "kwimprovise": Keyword.IMPROVISE,
    "kwaftermath": Keyword.AFTERMATH,
    "kwascend": Keyword.ASCEND,
    "kwassist": Keyword.ASSIST,
    "kwmentor": Keyword.MENTOR,
    "kwhideaway": Keyword.HIDEAWAY,
    "kwconspire": Keyword.CONSPIRE,
    "kwconspiare": Keyword.CONSPIRE,  # grammar misspelling tolerance
    "kwpersist": Keyword.PERSIST,
    "kwwither": Keyword.WITHER,
    "kwretrace": Keyword.RETRACE,
    "kwexalted": Keyword.EXALTED,
    "kwprovoke": Keyword.PROVOKE,
    "kwepic": Keyword.EPIC,
    "kwhaunt": Keyword.HAUNT,
    "kwabsorb": Keyword.ABSORB,
    "kwfrenzy": Keyword.FRENZY,
    "kwtransfigure": Keyword.TRANSFIGURE,
    "kwauraswap": Keyword.AURA_SWAP,
    "kwecho": Keyword.ECHO,
    "kwsplitsecond": Keyword.SPLIT_SECOND,
    "kwripple": Keyword.RIPPLE,
    "kwhiddenagenda": Keyword.HIDDEN_AGENDA,
    "kwrenown": Keyword.RENOWN,
    "kwtribute": Keyword.TRIBUTE,
    "kwforecast": Keyword.FORECAST,
    "kwcumulativeupkeep": Keyword.CUMULATIVE_UPKEEP,
}


# ---------------------------------------------------------------------------
# Tree walking
# ---------------------------------------------------------------------------


def _children_of(node: Tree | Token, name: str) -> Iterable[Tree | Token]:
    """Yield direct children of ``node`` whose rule name matches ``name``."""
    if not isinstance(node, Tree):
        return
    for child in node.children:
        if isinstance(child, Tree) and child.data == name:
            yield child


def _descendants_of(node: Tree | Token, name: str) -> Iterable[Tree]:
    """Yield Tree descendants whose rule name matches ``name`` (depth-first)."""
    if not isinstance(node, Tree):
        return
    if node.data == name:
        yield node
    for child in node.children:
        if isinstance(child, Tree):
            yield from _descendants_of(child, name)


def _flatten_text(node: Tree | Token) -> str:
    """Concatenate all token values under ``node`` in source order."""
    if isinstance(node, Token):
        return str(node)
    parts: list[str] = []
    for child in node.children:
        parts.append(_flatten_text(child))
    return " ".join(p for p in parts if p)


def _lower_keyword_node(node: Tree) -> KeywordAbility:
    """Lower a ``keywordability`` tree to ``KeywordAbility``."""
    if not isinstance(node, Tree) or node.data != "keywordability":
        raise LoweringIncomplete(f"expected-keywordability:{getattr(node, 'data', '?')}")
    if not node.children:
        raise LoweringIncomplete("empty-keywordability")
    inner = node.children[0]
    if not isinstance(inner, Tree):
        raise LoweringIncomplete(f"non-tree-keyword:{type(inner).__name__}")
    keyword = _KEYWORD_BY_RULE.get(inner.data)
    if keyword is None:
        raise LoweringIncomplete(f"unknown-keyword:{inner.data}")
    parameter = _flatten_text(inner).strip() or None
    # If the parameter is exactly the keyword's spelling, treat as no
    # parameter (the inner tree contained only the literal token).
    if parameter is not None and parameter.lower() == keyword.value:
        parameter = None
    return KeywordAbility(keyword=keyword, parameter=parameter)


def _lower_ability(node: Tree) -> list[Ability]:
    """Lower an ``ability`` tree to a list of public Ability instances.

    A single ability subtree may produce multiple keyword abilities when
    it contains a ``keywordlist``.
    """
    if not isinstance(node, Tree):
        raise LoweringIncomplete(f"non-tree-ability:{type(node).__name__}")
    results: list[Ability] = []
    handled = False
    for child in node.children:
        if not isinstance(child, Tree):
            continue
        if child.data == "keywordlist":
            for kw_node in _descendants_of(child, "keywordability"):
                results.append(_lower_keyword_node(kw_node))
            handled = True
        elif child.data == "keywordability":
            results.append(_lower_keyword_node(child))
            handled = True
        elif child.data == "remindertext":
            # Reminder text is recorded only on the most recent ability
            # in the public AST; we drop it on day one. The contract
            # doesn't carry reminder text on KeywordAbility today.
            continue
        elif child.data == "regularability":
            # SpellAbility / TriggeredAbility / ActivatedAbility / static.
            # Not in day-one coverage.
            raise LoweringIncomplete("regular-ability")
        else:
            raise LoweringIncomplete(f"unhandled-ability-child:{child.data}")
    if not handled:
        raise LoweringIncomplete("ability-with-no-recognized-child")
    return results


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def lower_card(tree: Tree) -> Card:
    """Lower the root of a parsed card body to a public ``Card``.

    Expects a Lark ``cardtext`` tree. Empty cardtext yields ``Card(())``.
    Any non-keyword content under the root raises
    :class:`LoweringIncomplete` so the caller never silently drops text.
    """
    if tree is None:
        return Card(abilities=())
    if not isinstance(tree, Tree):
        raise LoweringIncomplete(f"unexpected-root:{type(tree).__name__}")
    if tree.data != "cardtext":
        raise LoweringIncomplete(f"unexpected-root-rule:{tree.data}")
    abilities: list[Ability] = []
    for child in tree.children:
        if not isinstance(child, Tree):
            continue
        if child.data == "ability":
            abilities.extend(_lower_ability(child))
        elif child.data == "keywordlist":
            for kw_node in _descendants_of(child, "keywordability"):
                abilities.append(_lower_keyword_node(kw_node))
        elif child.data == "keywordability":
            abilities.append(_lower_keyword_node(child))
        elif child.data == "regularability":
            # Spell / Triggered / Activated / Static — not in day-one coverage.
            raise LoweringIncomplete("regular-ability")
        elif child.data == "remindertext":
            continue
        else:
            raise LoweringIncomplete(f"unhandled-cardtext-child:{child.data}")
    return Card(abilities=tuple(abilities))
