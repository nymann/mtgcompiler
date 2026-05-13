"""Public AST for mtgcompiler.

A *semantic*, lowered AST. Every concrete node is a ``@dataclass(frozen=True,
slots=True)`` exposing only public attributes. Consumers dispatch via
``isinstance`` or ``match`` over the closed hierarchies (``Ability``,
``Effect``, ``Cost``, ``Target``).

This module is the source of truth for the shape argentum-press and other
consumers depend on. The full set of node classes is enumerable with
``dir(mtgcompiler.ast)``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

__all__ = [
    # enums
    "Keyword",
    "TriggerCondition",
    # targets
    "Target",
    "AnyTarget",
    "TargetCreature",
    "TargetPlayer",
    "TargetSelf",
    # effects
    "Effect",
    "DrawCards",
    "GainLife",
    "LoseLife",
    "DealDamage",
    "DestroyTarget",
    "CreateToken",
    "ModifyStats",
    "ReanimateTarget",
    "ShuffleSelfIntoLibrary",
    # costs
    "Cost",
    "ManaCost",
    "TapSelf",
    "SacrificeSelf",
    # abilities
    "Ability",
    "KeywordAbility",
    "SpellAbility",
    "TriggeredAbility",
    "ActivatedAbility",
    # card
    "Card",
    # parse result
    "ParseError",
    "ParseResult",
]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Keyword(Enum):
    """Keyword abilities recognized by the parser. Open-ended: consumers
    that don't know a member should raise their own gap error."""

    # Evergreen
    FLYING = "flying"
    TRAMPLE = "trample"
    FIRST_STRIKE = "first strike"
    DOUBLE_STRIKE = "double strike"
    DEATHTOUCH = "deathtouch"
    LIFELINK = "lifelink"
    HASTE = "haste"
    VIGILANCE = "vigilance"
    REACH = "reach"
    MENACE = "menace"
    HEXPROOF = "hexproof"
    SHROUD = "shroud"
    INDESTRUCTIBLE = "indestructible"
    FLASH = "flash"
    DEFENDER = "defender"
    # Older / less common
    INTIMIDATE = "intimidate"
    FEAR = "fear"
    SHADOW = "shadow"
    HORSEMANSHIP = "horsemanship"
    PROWESS = "prowess"
    CHANGELING = "changeling"
    # Parametric (carry a `parameter: str | None` on KeywordAbility)
    EQUIP = "equip"
    WARD = "ward"
    PROTECTION = "protection"
    LANDWALK = "landwalk"
    CYCLING = "cycling"
    KICKER = "kicker"
    FLASHBACK = "flashback"
    BUYBACK = "buyback"
    ENCHANT = "enchant"
    BANDING = "banding"
    RAMPAGE = "rampage"
    BUSHIDO = "bushido"
    ANNIHILATOR = "annihilator"
    FADING = "fading"
    VANISHING = "vanishing"
    SUSPEND = "suspend"
    MORPH = "morph"
    AMPLIFY = "amplify"
    MODULAR = "modular"
    AFFINITY = "affinity"
    SOULSHIFT = "soulshift"
    DREDGE = "dredge"
    BLOODTHIRST = "bloodthirst"
    GRAFT = "graft"
    POISONOUS = "poisonous"
    DEVOUR = "devour"
    NINJUTSU = "ninjutsu"
    TRANSMUTE = "transmute"
    REPLICATE = "replicate"
    RECOVER = "recover"
    SPLICE = "splice"
    OFFERING = "offering"
    CHAMPION = "champion"
    EVOKE = "evoke"
    PROWL = "prowl"
    REINFORCE = "reinforce"
    UNEARTH = "unearth"
    LEVEL_UP = "level up"
    MIRACLE = "miracle"
    OVERLOAD = "overload"
    SCAVENGE = "scavenge"
    BESTOW = "bestow"
    OUTLAST = "outlast"
    DASH = "dash"
    AWAKEN = "awaken"
    SURGE = "surge"
    EMERGE = "emerge"
    ESCALATE = "escalate"
    CREW = "crew"
    FABRICATE = "fabricate"
    PARTNER = "partner"
    EMBALM = "embalm"
    ETERNALIZE = "eternalize"
    AFFLICT = "afflict"
    SURVEIL = "surveil"
    JUMP_START = "jump-start"
    FORTIFY = "fortify"
    ENTWINE = "entwine"
    MADNESS = "madness"
    MULTIKICKER = "multikicker"
    CASCADE = "cascade"
    STORM = "storm"
    SUNBURST = "sunburst"
    CONVOKE = "convoke"
    DELVE = "delve"
    GRAVESTORM = "gravestorm"
    REBOUND = "rebound"
    TOTEM_ARMOR = "totem armor"
    INFECT = "infect"
    BATTLE_CRY = "battle cry"
    LIVING_WEAPON = "living weapon"
    UNDYING = "undying"
    SOULBOND = "soulbond"
    UNLEASH = "unleash"
    CIPHER = "cipher"
    EVOLVE = "evolve"
    EXTORT = "extort"
    FUSE = "fuse"
    DETHRONE = "dethrone"
    EXPLOIT = "exploit"
    DEVOID = "devoid"
    INGEST = "ingest"
    MYRIAD = "myriad"
    SKULK = "skulk"
    MELEE = "melee"
    IMPROVISE = "improvise"
    AFTERMATH = "aftermath"
    ASCEND = "ascend"
    ASSIST = "assist"
    MENTOR = "mentor"
    HIDEAWAY = "hideaway"
    CONSPIRE = "conspire"
    PERSIST = "persist"
    WITHER = "wither"
    RETRACE = "retrace"
    EXALTED = "exalted"
    PROVOKE = "provoke"
    EPIC = "epic"
    HAUNT = "haunt"
    ABSORB = "absorb"
    FRENZY = "frenzy"
    TRANSFIGURE = "transfigure"
    AURA_SWAP = "aura swap"
    ECHO = "echo"
    SPLIT_SECOND = "split second"
    RIPPLE = "ripple"
    HIDDEN_AGENDA = "hidden agenda"
    RENOWN = "renown"
    TRIBUTE = "tribute"
    FORECAST = "forecast"
    CUMULATIVE_UPKEEP = "cumulative upkeep"


class TriggerCondition(Enum):
    """Trigger conditions for triggered abilities. Open-ended."""

    ENTERS_BATTLEFIELD = "enters"
    LEAVES_BATTLEFIELD = "leaves"
    ATTACKS = "attacks"
    BLOCKS = "blocks"
    DIES = "dies"
    CAST_SPELL = "cast_spell"
    BEGINNING_OF_UPKEEP = "upkeep"
    BEGINNING_OF_DRAW = "draw_step"
    BEGINNING_OF_COMBAT = "beginning_of_combat"
    END_OF_COMBAT = "end_of_combat"
    BEGINNING_OF_END_STEP = "end_step"
    END_OF_TURN = "end_of_turn"


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------


class Target:
    """Base for the closed target hierarchy."""


@dataclass(frozen=True, slots=True)
class AnyTarget(Target):
    pass


@dataclass(frozen=True, slots=True)
class TargetCreature(Target):
    pass


@dataclass(frozen=True, slots=True)
class TargetPlayer(Target):
    pass


@dataclass(frozen=True, slots=True)
class TargetSelf(Target):
    pass


# ---------------------------------------------------------------------------
# Effects
# ---------------------------------------------------------------------------


class Effect:
    """Base for the closed effect hierarchy."""


@dataclass(frozen=True, slots=True)
class DrawCards(Effect):
    amount: int


@dataclass(frozen=True, slots=True)
class GainLife(Effect):
    amount: int


@dataclass(frozen=True, slots=True)
class LoseLife(Effect):
    amount: int


@dataclass(frozen=True, slots=True)
class DealDamage(Effect):
    amount: int
    target: Target


@dataclass(frozen=True, slots=True)
class DestroyTarget(Effect):
    target: Target


@dataclass(frozen=True, slots=True)
class CreateToken(Effect):
    token_name: str
    count: int


@dataclass(frozen=True, slots=True)
class ModifyStats(Effect):
    power_delta: int
    toughness_delta: int
    target: Target


@dataclass(frozen=True, slots=True)
class ReanimateTarget(Effect):
    target: Target


@dataclass(frozen=True, slots=True)
class ShuffleSelfIntoLibrary(Effect):
    pass


# ---------------------------------------------------------------------------
# Costs
# ---------------------------------------------------------------------------


class Cost:
    """Base for the closed cost hierarchy."""


@dataclass(frozen=True, slots=True)
class ManaCost(Cost):
    symbols: str


@dataclass(frozen=True, slots=True)
class TapSelf(Cost):
    pass


@dataclass(frozen=True, slots=True)
class SacrificeSelf(Cost):
    pass


# ---------------------------------------------------------------------------
# Abilities
# ---------------------------------------------------------------------------


class Ability:
    """Base for the closed ability hierarchy."""


@dataclass(frozen=True, slots=True)
class KeywordAbility(Ability):
    keyword: Keyword
    parameter: str | None = None


@dataclass(frozen=True, slots=True)
class SpellAbility(Ability):
    effects: tuple[Effect, ...]


@dataclass(frozen=True, slots=True)
class TriggeredAbility(Ability):
    condition: TriggerCondition
    effects: tuple[Effect, ...]


@dataclass(frozen=True, slots=True)
class ActivatedAbility(Ability):
    costs: tuple[Cost, ...]
    effects: tuple[Effect, ...]


# ---------------------------------------------------------------------------
# Card
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Card:
    abilities: tuple[Ability, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Parse result
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ParseError:
    kind: str  # one of: "incomplete", "invalid", "ambiguous"
    message: str
    position: int | None = None


@dataclass(frozen=True, slots=True)
class ParseResult:
    ast: Card | None = None
    error: ParseError | None = None

    @property
    def ok(self) -> bool:
        return self.ast is not None
