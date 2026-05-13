"""Tests for the public mtgcompiler.parse() API and the semantic AST."""
from __future__ import annotations

import pytest

from mtgcompiler import parse
from mtgcompiler.ast import (
    Ability,
    Card,
    Cost,
    Effect,
    Keyword,
    KeywordAbility,
    ParseError,
    ParseResult,
    Target,
    TriggerCondition,
)


# ---------------------------------------------------------------------------
# parse() shape
# ---------------------------------------------------------------------------


def test_parse_str_empty_returns_empty_card():
    result = parse("")
    assert isinstance(result, ParseResult)
    assert result.ok
    assert result.ast == Card(abilities=())


def test_parse_dict_empty_oracle_text_returns_empty_card():
    result = parse({"name": "Glory Seeker", "oracle_text": ""})
    assert result.ok
    assert result.ast == Card(abilities=())


def test_parse_dict_missing_oracle_text_treated_as_empty():
    result = parse({"name": "Mystery Card"})
    assert result.ok
    assert result.ast.abilities == ()


def test_parse_result_ok_is_ast_is_not_none():
    ok = ParseResult(ast=Card(abilities=()))
    fail = ParseResult(error=ParseError(kind="incomplete", message="x"))
    assert ok.ok is True
    assert fail.ok is False


# ---------------------------------------------------------------------------
# Keyword abilities (day-one coverage)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text, expected_keyword",
    [
        ("flying", Keyword.FLYING),
        ("trample", Keyword.TRAMPLE),
        ("haste", Keyword.HASTE),
        ("vigilance", Keyword.VIGILANCE),
        ("lifelink", Keyword.LIFELINK),
        ("deathtouch", Keyword.DEATHTOUCH),
        ("first strike", Keyword.FIRST_STRIKE),
        ("double strike", Keyword.DOUBLE_STRIKE),
        ("reach", Keyword.REACH),
        ("menace", Keyword.MENACE),
        ("hexproof", Keyword.HEXPROOF),
        ("indestructible", Keyword.INDESTRUCTIBLE),
        ("defender", Keyword.DEFENDER),
        ("flash", Keyword.FLASH),
    ],
)
def test_single_keyword(text, expected_keyword):
    result = parse(text)
    assert result.ok, f"expected ok for {text!r}, got {result.error}"
    assert len(result.ast.abilities) == 1
    ability = result.ast.abilities[0]
    assert isinstance(ability, KeywordAbility)
    assert ability.keyword == expected_keyword
    assert ability.parameter is None


def test_keyword_salad_comma_separated():
    result = parse("flying, vigilance, trample")
    assert result.ok
    keywords = [a.keyword for a in result.ast.abilities]
    assert keywords == [Keyword.FLYING, Keyword.VIGILANCE, Keyword.TRAMPLE]


def test_multi_word_keywords_in_salad():
    result = parse("first strike, double strike")
    assert result.ok
    keywords = [a.keyword for a in result.ast.abilities]
    assert keywords == [Keyword.FIRST_STRIKE, Keyword.DOUBLE_STRIKE]


# ---------------------------------------------------------------------------
# Non-keyword content correctly fails with kind="incomplete"
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "destroy target creature.",
        "draw a card.",
    ],
)
def test_non_keyword_content_returns_incomplete(text):
    result = parse(text)
    assert not result.ok
    assert result.error is not None
    assert result.error.kind == "incomplete"
    # error.message is a short label, not the parse exception spilling out
    assert "\n" not in result.error.message
    assert len(result.error.message) < 120


# ---------------------------------------------------------------------------
# Public AST surface
# ---------------------------------------------------------------------------


def test_match_dispatch_on_keyword_ability():
    """Consumer-side dispatch: match on (keyword, parameter) only."""
    ability = KeywordAbility(Keyword.FLYING)
    match ability:
        case KeywordAbility(Keyword.FLYING, None):
            matched = True
        case _:
            matched = False
    assert matched


def test_keyword_ability_match_args_excludes_nothing_extra():
    assert KeywordAbility.__match_args__ == ("keyword", "parameter")


def test_card_match_args_is_abilities_only():
    assert Card.__match_args__ == ("abilities",)


def test_dataclasses_are_frozen():
    ka = KeywordAbility(Keyword.FLYING)
    with pytest.raises(AttributeError):
        ka.keyword = Keyword.TRAMPLE  # type: ignore[misc]


def test_dataclasses_use_slots():
    # slots=True forbids attaching arbitrary attributes; the slot layout
    # contains only declared dataclass fields.
    assert KeywordAbility.__slots__ == ("keyword", "parameter")
    assert Card.__slots__ == ("abilities",)
    ka = KeywordAbility(Keyword.FLYING)
    with pytest.raises((AttributeError, TypeError)):
        ka._mg = object()  # type: ignore[attr-defined]


def test_ast_hierarchies_are_importable():
    """Sanity-check the exported surface argentum-press depends on."""
    # base classes
    assert Ability is not None
    assert Effect is not None
    assert Cost is not None
    assert Target is not None
    # enums
    assert Keyword.FLYING.value == "flying"
    assert TriggerCondition.ENTERS_BATTLEFIELD.value == "enters"
