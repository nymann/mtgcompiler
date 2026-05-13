# Design alignment: mtgcompiler ↔ argentum-press

## What I observed

**argentum-press `src/argentum_press/_ast.py`** defines a *semantic, lowered* AST — and the docstring is explicit that this is the **contract**: "Once mtgcompiler exposes the matching surface this file collapses to `from mtgcompiler.ast import *`."

Concretely:
- `Effect` subclasses are game-rules categories carrying primitives: `DrawCards(amount: int)`, `GainLife(amount: int)`, `DealDamage(amount: int, target: Target)`, `DestroyTarget(target)`, `CreateToken(token_name, count)`, `ModifyStats(power_delta, toughness_delta, target)`, `ReanimateTarget(target)`, `ShuffleSelfIntoLibrary()`.
- `Target` is a closed flat hierarchy: `AnyTarget`, `TargetCreature`, `TargetPlayer`, `TargetSelf` — no wrapped expression.
- `TriggerCondition` is an `Enum`: `ENTERS_BATTLEFIELD`, `ATTACKS`, `DIES`, `BEGINNING_OF_UPKEEP`, `END_OF_TURN`.
- `Cost`: `ManaCost(symbols: str)`, `TapSelf`, `SacrificeSelf`.
- `Ability`: exactly four subclasses (`KeywordAbility`, `SpellAbility`, `TriggeredAbility`, `ActivatedAbility`); no `StaticAbility`, no `RegularAbility`, no `ability_word`/`reminder_text`.
- `Keyword` enum: ~22 entries (modern common keywords).
- `slots=True` on every dataclass.
- No `Node` base class. No `unparse()` method.
- `ParseResult.ok = self.ast is not None`.
- `lowerer.py` dispatches via `functools.singledispatchmethod` over those closed hierarchies. Unknown nodes raise `EmitterGap` → caller's `DeferredEmitterGap` outcome.

**mtgcompiler internally** parses oracle text into a *syntactic* tree of ~250 `Mg*` classes (closed, abc-based, with `unparseToString()`). The Mg classes mirror the **shape of the sentence**, not the game-rules semantics. "Draw a card" parses to `MgExpressionStatement(MgCardDrawExpression(MgNumberValue(1)))`, not to a `DrawCards(1)` instance.

So the gap to close is **semantic lowering**: pattern-matching on the Mg syntactic tree and producing the lowered classes argentum-press wants. That's interpretive work, not a 1:1 mapping. Many oracle-text shapes won't lower cleanly on day one (and possibly ever — keyword salad, weird modal patterns, replacement effects, etc.).

## Architectural options

### Option A — mtgcompiler does it all
- `mtgcompiler.parse() → ParseResult(ast: Card)` returns argentum-press's semantic AST directly.
- mtgcompiler owns: syntactic parse (Mg) **plus** semantic lowering (Mg → semantic AST).
- argentum-press: `from mtgcompiler.ast import *`, deletes `_ast.py`, keeps `lowerer.py`.
- Unrecognized patterns become `ParseError(kind="incomplete", ...)` so `outcome.py:DeferredEmitterGap` flows naturally.
- **Pros**: caller stays as simple as it is today. Single boundary. Matches the docstring in `_ast.py`.
- **Cons**: every new semantic Effect category requires changes inside mtgcompiler. The lowering rules become tightly coupled to argentum-press's DSL surface. If another consumer ever shows up wanting different semantic categories, mtgcompiler has to either branch or grow another surface.

### Option B — two-layer split
- `mtgcompiler.parse()` returns a **syntactic** AST (a polished, frozen-dataclass version of the Mg tree).
- argentum-press grows a new pass — `argentum_press/_lower.py` — that walks the syntactic AST and produces the existing `_ast.py` semantic classes. `lowerer.py` stays as-is.
- **Pros**: clean compiler-pipeline separation. mtgcompiler stays focused on language structure. Semantic categories are owned by the consumer that knows what they mean for their target DSL. Other consumers can pick different semantic categories without forcing mtgcompiler to change.
- **Cons**: argentum-press grows a new pass it didn't ask for. Two layers of "unknown shape" gaps to handle (parse-level and lower-level). The contract surface in `_ast.py` doesn't collapse to a re-export.

### Option C — mtgcompiler exposes both
- `mtgcompiler.ast` (syntactic) **and** `mtgcompiler.semantic` (lowered, matching `_ast.py`).
- argentum-press imports from `mtgcompiler.semantic`.
- **Pros**: keeps both audiences happy.
- **Cons**: maximum maintenance burden. The semantic layer is still argentum-press-shaped; we'd be pretending it's general-purpose. Probably not worth the extra surface unless a second consumer actually shows up.

## My recommendation, weakly held

**Option A**, with one caveat. Going by the `_ast.py` docstring, this is what argentum-press explicitly wants — "this file collapses to a re-export." That's the strongest signal in the room. Lowering rules being tightly coupled to argentum-press's DSL is fine *while there's one consumer*. Splitting prematurely (Option B) is a YAGNI move dressed up as cleanliness.

**The caveat**: I want to push back on putting *every* semantic Effect inside mtgcompiler. The lowering layer should live in `mtgcompiler/_lower.py` (a single file), not bleed into the public `ast` module. That way:
- The public AST shape is owned by argentum-press's `_ast.py`. mtgcompiler imports/mirrors it.
- The lowering logic is owned by mtgcompiler.
- When argentum-press adds a new `Effect` subclass, mtgcompiler adds a new pattern matcher in `_lower.py` — that's the only mtgcompiler change.
- If a second consumer ever shows up, we can extract the AST shape into a separate package both depend on; until then we don't pay that cost.

## Open questions for argentum-press

1. **Does the contract really need to be byte-for-byte exact?** Specifically:
   - Is the `Keyword` enum frozen at 22 members, or can mtgcompiler add the rest (e.g. `EQUIP`, `WARD`, `PROTECTION` with parameters)? `KeywordAbility(keyword)` has no parameter field — what happens for parametric keywords like `equip {2}`, `protection from red`, `ward {1}`? Do those become `EmitterGap` deliberately, or should the AST grow a `parameter` field?
   - Same question for `TriggerCondition`: many real triggers aren't in your 5-entry enum (`whenever you cast a spell`, `at the beginning of combat`, `when ~ leaves the battlefield`). Should mtgcompiler return `ParseError("incomplete")` for those, or should the enum grow?

2. **Where do `StaticAbility`s go?** Many cards have static effects ("Other creatures you control get +1/+1", "You can't lose the game"). Your `Ability` hierarchy has no `StaticAbility`. Are these expected to fail with `ParseError("incomplete")` on day one, or do you have a category planned?

3. **`ParseError.alternatives`** — the original spec the user sent me had `alternatives: list[Card]` for ambiguous parses. `_ast.py:ParseError` doesn't have it. Did you intentionally drop it, or just not get to it?

4. **Coverage on day one.** What's the minimum set of cards that must lower successfully? My guess based on `lowerer.py`'s registered handlers:
   - Vanilla / keyword-only cards (`Flying. Vigilance.`)
   - `Draw a card.` / `Draw N cards.`
   - `You gain N life.` / `You lose N life.`
   - `CARDNAME deals N damage to any target.`
   - `Destroy target creature.`
   - `Create a {token} token.`
   - `Target creature gets +X/+Y.`
   - `Return target creature card from your graveyard to the battlefield.`

   Everything else returns `ParseError("incomplete")`. Sound right?

5. **`slots=True` constraint**: it precludes attaching backreferences to the Mg parse tree on the dataclass. Confirming you don't want a `_mg: object` escape hatch — you're OK never seeing the original parse tree from a lowered node.

6. **Where does `mtgcompiler.parse(card: dict)` get card metadata from?** Scryfall dicts have `name`, `oracle_text`, `power`, `toughness`, `type_line`, etc. Your `Card` dataclass only has `abilities`. Should I read `oracle_text` from the dict and ignore the rest, or do you want `Card` to grow `name`/`power`/`toughness` fields?

## What I'd do if you say "go"

1. Delete the syntactic AST module I wrote, replace with a re-implementation of `_ast.py`'s exact classes inside `mtgcompiler/ast/__init__.py`.
2. Write `mtgcompiler/_lower.py`: pattern matchers over Mg syntax tree → semantic AST nodes, with a small initial coverage set (the ~8 patterns above).
3. Wire `mtgcompiler.parse(card)` and `ParseResult`/`ParseError` to match the contract exactly.
4. Round-trip tests: a handful of representative cards lower correctly; unknown shapes produce `ParseError(kind="incomplete")`.
