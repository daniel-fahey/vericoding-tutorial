# Vericoding Tutorial

Small programs with **contracts** — postconditions proved about them in
Lean 4 — presented as a slideshow you step through with the arrow keys.
Each slide highlights one tactic and shows the goal state that Lean itself
reports at that point in the proof.

The first examples:

- `Examples/Head.lean` — a safe `head?`; if it returns an element, that
  element belongs to the list.
- `Examples/Find.lean` — a `find?` over a list and a predicate; if it
  returns an element, the element satisfies the predicate and belongs to
  the list.

## Requirements

[Nix](https://nixos.org/) with flakes enabled. Everything else — the Lean
toolchain, Python, the slideshow build — comes from the flake.

## Building the slides

```sh
nix build .#slides
```

This produces `result/index.html`: a single self-contained file (reveal.js
is vendored under `vendor/reveal.js/` and inlined). Open it in a browser
and use the arrow keys to step through the proofs.

For development, enter the shell:

```sh
nix develop
```

and rebuild the deck after editing an example:

```sh
python3 scripts/build_deck.py \
  --example Examples/Head.lean \
  --example Examples/Find.lean \
  --output index.html
```

Check the examples on their own with `lean Examples/Head.lean` (and
likewise for `Find.lean`).

## How the proof states are captured

Proofs mark their steps with a standalone `-- slide-step` comment on the
line before each tactic. The generator
(`scripts/build_deck.py`) replays every proof once per step in a temporary
copy with a `trace_state` probe inserted after that step's tactic, runs
the real `lean` binary, and captures the goal state Lean prints. Goal
panels show exactly what Lean prints, and nothing else. When a tactic
closes the last goal of the proof the panel is empty and the slide says
the proof is complete; when a tactic closes only its own branch (`case`
or `·`) Lean reports no goals *in that branch*, and the slide says so
instead. If Lean rejects a proof, or writes anything unexpected while a
state is being captured, the build fails. No goal text in the deck is
written by hand.

Because a probe is inserted after a marked tactic line, mark tactics that
stand alone (`cases xs` followed by `case` branches) rather than syntax
that is glued to what follows (`cases xs with | nil => …`).

## Tests

```sh
nix develop -c python3 tests/test_deck_build.py
```

builds a deck from `tests/fixtures/DeckStepExample.lean` and checks that
each marked tactic gets a slide whose goal panel matches an independent
`trace_state` probe of the same proof.

## License

The tutorial content is licensed under
[Creative Commons Attribution 4.0 International](LICENSE) (CC BY 4.0).
The vendored reveal.js assets under `vendor/reveal.js/` are MIT licensed;
see `vendor/reveal.js/LICENSE`.
