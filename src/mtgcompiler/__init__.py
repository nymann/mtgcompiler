"""mtgcompiler — parse Magic: the Gathering card text into a semantic AST.

The public surface is intentionally small:

    from mtgcompiler import parse
    from mtgcompiler.ast import Card, KeywordAbility, Keyword

    result = parse({"name": "Glory Seeker", "oracle_text": ""})
    assert result.ok
    result.ast  # -> Card(abilities=())

``parse`` accepts either a Scryfall-shaped dict (``oracle_text`` + ``name``)
or a raw oracle-text string. Anything the lowerer doesn't yet recognize
produces ``ParseResult(error=ParseError(kind="incomplete", ...))`` so the
caller can route it to a deferred-emitter-gap outcome.

Error positions are byte offsets into the **preprocessed** text (after
mtgcompiler's contraction expansion and name -> ``~`` substitution), not
the raw oracle text.
"""
from __future__ import annotations

from typing import Any

from mtgcompiler import _lower
from mtgcompiler.ast import Card, ParseError, ParseResult

__all__ = ["parse", "Card", "ParseError", "ParseResult"]


_COMPILER = None


def _get_compiler():
    """Return the shared MtgJsonCompiler, building it lazily.

    The first build is slow (Lark grammar compilation); subsequent calls
    reuse the same parser instance, which is thread-unsafe but fine for
    the single-threaded callers we have today.
    """
    global _COMPILER
    if _COMPILER is None:
        from mtgcompiler.frontend.compilers.LarkMtgJson.MtgJsonCompiler import (
            MtgJsonCompiler,
        )

        _COMPILER = MtgJsonCompiler(
            options={"parser.startRule": "cardtext", "parser.larkDebug": False}
        )
    return _COMPILER


def parse(card: dict[str, Any] | str, *, name: str | None = None) -> ParseResult:
    """Parse a card's oracle text into a semantic AST.

    Args:
        card: Either a Scryfall-shaped dict (with ``oracle_text`` and
            optional ``name``) or a raw oracle-text string.
        name: Card name for ``~`` normalization when ``card`` is a string.
            Ignored when ``card`` is a dict (``card["name"]`` wins).

    Returns:
        A :class:`mtgcompiler.ast.ParseResult`. ``result.ok`` is ``True``
        iff ``result.ast`` is populated.
    """
    if isinstance(card, dict):
        oracle_text = card.get("oracle_text") or card.get("text") or ""
        card_name = card.get("name")
    else:
        oracle_text = card
        card_name = name

    if not oracle_text.strip():
        return ParseResult(ast=Card(abilities=()))

    try:
        compiler = _get_compiler()
    except Exception as e:  # grammar build failure
        return ParseResult(error=ParseError(kind="invalid", message=str(e)))

    preprocessor = compiler.getPreprocessor()
    parser = compiler.getParser()

    try:
        preprocessed = preprocessor.prelex(oracle_text, {}, card_name)
        preprocessed = preprocessor.postlex(preprocessed, {})
    except Exception as e:
        return ParseResult(error=ParseError(kind="invalid", message=f"preprocess: {e}"))

    try:
        import lark

        try:
            tree = parser.parse(preprocessed)
        except lark.exceptions.UnexpectedInput as e:
            return ParseResult(
                error=ParseError(
                    kind="invalid",
                    message=str(e).splitlines()[0],
                    position=getattr(e, "pos_in_stream", None),
                )
            )
        except lark.exceptions.LarkError as e:
            # Ambiguous, GrammarError, ParseError-as-class, etc.
            message = str(e).splitlines()[0] if str(e) else type(e).__name__
            kind = "ambiguous" if "ambig" in message.lower() else "invalid"
            return ParseResult(error=ParseError(kind=kind, message=message))
    except ImportError:
        return ParseResult(
            error=ParseError(kind="invalid", message="lark not installed")
        )

    # We deliberately skip ``transformer.transform(tree)``: MtgJsonTransformer
    # carries pre-existing import gaps for many keyword classes and is under
    # active development. The lowerer walks the Lark tree directly.
    try:
        ast = _lower.lower_card(tree)
    except _lower.LoweringIncomplete as e:
        return ParseResult(error=ParseError(kind="incomplete", message=str(e)))

    return ParseResult(ast=ast)
