# Repository conventions

## Toolchain

All Lean, Python, and build commands run through the nix dev shell:

```sh
nix develop -c <command>
```

Do not assume an activated shell; each command brings its own environment.

## Tests

- Framework: Python standard-library `unittest` only. No test
  dependencies, no new package managers.
- Run: `nix develop -c python3 tests/test_deck_build.py`.
- Fixtures live in `tests/fixtures/`.
- Tests compare generated slide content against goal states probed from
  the real `lean` binary; never hand-write expected goal text.

## Examples and slides

- Examples import Lean core only — no Mathlib.
- Mark each proof step with a standalone `-- slide-step` comment on the
  line before the tactic. The tactic must stand alone syntactically
  (use `cases xs` + `case` branches, not `cases … with`), because the
  generator inserts a `trace_state` probe after the marked line.
- The last marked step of a proof should close the proof: the deck
  labels the final step's empty panel as proof completion, and any
  earlier empty panel as a closed branch.
- Generated output (`result/`, ad-hoc `index.html`) is never committed.

## Layout

- `Examples/` — the tutorial programs and their contract proofs.
- `scripts/build_deck.py` — the slideshow generator (Python stdlib only).
- `vendor/reveal.js/` — vendored reveal.js assets (MIT), inlined into the
  deck; keep its LICENSE file with it.
