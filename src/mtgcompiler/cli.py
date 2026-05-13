"""Command-line interface for mtgcompiler."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path

from mtgcompiler import parse


def _read_input(path: Path) -> dict | str:
    """Return either a Scryfall-shaped dict or a raw oracle-text string."""
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(raw)
    return raw


def _to_jsonable(obj):
    """Convert dataclass / enum / tuple trees into JSON-friendly primitives."""
    if isinstance(obj, Enum):
        return obj.name
    if is_dataclass(obj) and not isinstance(obj, type):
        out = {"__type__": type(obj).__name__}
        for k, v in asdict(obj).items():
            out[k] = _to_jsonable(v)
        # asdict can't reach Enum members inside slots-dataclasses on all
        # Python versions; re-walk to fix.
        for f in obj.__dataclass_fields__:
            v = getattr(obj, f)
            out[f] = _to_jsonable(v)
        return out
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    return obj


def _cmd_parse(args: argparse.Namespace) -> int:
    card = _read_input(Path(args.file))
    result = parse(card)
    if args.json:
        print(json.dumps(_to_jsonable(result), indent=2))
    else:
        print(result)
    return 0 if result.ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mtgcompiler",
        description="Parse Magic: the Gathering card text into a semantic AST.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    parse_cmd = sub.add_parser(
        "parse",
        help="Parse a card file (JSON with oracle_text, or raw text).",
    )
    parse_cmd.add_argument("file", help="Path to the input file.")
    parse_cmd.add_argument(
        "--json",
        action="store_true",
        help="Output the ParseResult as JSON.",
    )
    parse_cmd.set_defaults(func=_cmd_parse)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
