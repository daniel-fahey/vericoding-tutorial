#!/usr/bin/env python3
"""Build a self-contained reveal.js slideshow from marked Lean proofs.

Each `-- slide-step` comment in an example marks one proof step: the tactic
on the following line. For every step this script replays the proof with a
`trace_state` probe inserted after that tactic and captures the goal state
that Lean itself reports. The slides can therefore never drift from the
proofs: every goal panel is real Lean output, and a proof that Lean rejects
fails the build.

Usage:
    python3 scripts/build_deck.py --example Examples/Head.lean \
        [--example Examples/Find.lean] --output index.html
"""

import argparse
import html
import pathlib
import re
import subprocess
import sys
import tempfile

MARKER = "-- slide-step"
PROBE = "trace_state"

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
REVEAL_DIST = REPO_ROOT / "vendor" / "reveal.js" / "dist"

DIAGNOSTIC = re.compile(r"^\S+:\d+:\d+: (?:info|warning|error)\b")


def fail(message):
    sys.exit(f"build_deck: error: {message}")


def parse_steps(path, lines):
    """Return [(tactic_line_index, indent, tactic_text)] for each marker."""
    steps = []
    for index, line in enumerate(lines):
        if line.strip() != MARKER:
            continue
        tactic_index = index + 1
        if tactic_index >= len(lines):
            fail(f"{path}:{index + 1}: '{MARKER}' has no following tactic line")
        tactic_line = lines[tactic_index]
        if not tactic_line.strip() or tactic_line.strip() == MARKER:
            fail(
                f"{path}:{tactic_index + 1}: '{MARKER}' must be followed by "
                f"exactly one tactic line, found {tactic_line.strip()!r}"
            )
        indent = tactic_line[: len(tactic_line) - len(tactic_line.lstrip())]
        steps.append((tactic_index, indent, tactic_line.strip()))
    if not steps:
        fail(f"{path}: no '{MARKER}' comments found")
    return steps


def capture_state(path, lines, step_index, tactic_index, temporary_directory):
    """Replay the proof with a probe after one tactic; return Lean's state."""
    instrumented = ["set_option linter.unusedVariables false"]
    for index, line in enumerate(lines):
        instrumented.append(line)
        if index == tactic_index:
            indent = line[: len(line) - len(line.lstrip())]
            instrumented.append(f"{indent}{PROBE}")
    probe_path = temporary_directory / path.name
    probe_path.write_text("\n".join(instrumented) + "\n", encoding="utf-8")
    result = subprocess.run(
        ["lean", str(probe_path)],
        cwd=temporary_directory,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        fail(
            f"{path}: Lean rejected the proof while capturing step "
            f"{step_index + 1}:\n{result.stdout}\n{result.stderr}"
        )
    if result.stderr.strip():
        fail(
            f"{path}: Lean wrote to stderr while capturing step "
            f"{step_index + 1}:\n{result.stderr}"
        )
    unexpected = [ln for ln in result.stdout.splitlines() if DIAGNOSTIC.match(ln)]
    if unexpected:
        fail(
            f"{path}: unexpected Lean diagnostic while capturing step "
            f"{step_index + 1}: {unexpected[0]!r}"
        )
    return result.stdout.strip()


def render_code_lines(lines, steps):
    """Proof listing without markers; current tactic wrapped per step."""
    marker_indices = {i for i, ln in enumerate(lines) if ln.strip() == MARKER}
    display = [ln for i, ln in enumerate(lines) if i not in marker_indices]
    remap = {}
    new_index = 0
    for old_index in range(len(lines)):
        if old_index in marker_indices:
            continue
        remap[old_index] = new_index
        new_index += 1
    listings = []
    for tactic_index, _, _ in steps:
        highlighted = remap[tactic_index]
        rendered = []
        for index, line in enumerate(display):
            escaped = html.escape(line)
            if index == highlighted:
                indent_len = len(line) - len(line.lstrip())
                rendered.append(
                    html.escape(line[:indent_len])
                    + '<mark class="current-tactic">'
                    + html.escape(line.strip())
                    + "</mark>"
                )
            else:
                rendered.append(escaped)
        listings.append("\n".join(rendered))
    return listings


def build_deck(examples, output_path):
    if not (REVEAL_DIST / "reveal.js").is_file():
        fail(f"vendored reveal.js not found at {REVEAL_DIST}")
    reveal_js = (REVEAL_DIST / "reveal.js").read_text(encoding="utf-8").replace(
        "</script", "<\\/script"
    )
    reveal_css = (REVEAL_DIST / "reveal.css").read_text(encoding="utf-8")
    theme_css = (REVEAL_DIST / "theme" / "black.css").read_text(encoding="utf-8")

    sections = [
        "<section><h1>Vericoding Tutorial</h1>"
        "<p>Contracts over programs, proved step by step.</p></section>"
    ]
    with tempfile.TemporaryDirectory() as temporary:
        temporary_directory = pathlib.Path(temporary)
        for example in examples:
            path = pathlib.Path(example)
            if not path.is_file():
                fail(f"example not found: {example}")
            lines = path.read_text(encoding="utf-8").splitlines()
            steps = parse_steps(path, lines)
            states = [
                capture_state(path, lines, k, tactic_index, temporary_directory)
                for k, (tactic_index, _, _) in enumerate(steps)
            ]
            listings = render_code_lines(lines, steps)
            sections.append(
                f"<section><h2>{html.escape(path.name)}</h2></section>"
            )
            last_step = len(steps) - 1
            for k, (listing, state) in enumerate(zip(listings, states)):
                caption = ""
                if not state:
                    if k == last_step:
                        caption = (
                            '<p class="proof-status proof-complete">'
                            "No goals remain — the proof is complete.</p>"
                        )
                    else:
                        caption = (
                            '<p class="proof-status branch-closed">'
                            "Branch closed — the proof continues.</p>"
                        )
                sections.append(
                    '<section class="proof-step">'
                    f'<pre class="proof-code"><code>{listing}</code></pre>'
                    f'<pre class="goal-state">{html.escape(state)}</pre>'
                    f"{caption}"
                    "</section>"
                )

    deck = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vericoding Tutorial</title>
<style>
{reveal_css}
{theme_css}
.reveal .proof-code code {{
  max-height: none;
  overflow: visible;
}}
.reveal .proof-code {{
  font-size: 0.55em;
  line-height: 1.35;
  text-align: left;
  margin: 0 auto 0.4em auto;
  width: fit-content;
  max-width: 100%;
  white-space: pre-wrap;
}}
.reveal .goal-state {{
  font-size: 0.5em;
  line-height: 1.35;
  text-align: left;
  margin: 0 auto;
  width: fit-content;
  max-width: 100%;
  border-top: 2px solid #42affa;
  padding-top: 0.4em;
  color: #a5d8ff;
  white-space: pre-wrap;
}}
.reveal .proof-status {{
  font-size: 0.55em;
  margin: 0.4em 0 0 0;
}}
.reveal .proof-status.branch-closed {{
  color: #ffd43b;
}}
.reveal .proof-status.proof-complete {{
  color: #51cf66;
}}
.reveal mark.current-tactic {{
  background: #42affa;
  color: #000;
  padding: 0 0.15em;
  border-radius: 3px;
}}
</style>
</head>
<body>
<div class="reveal">
<div class="slides">
{chr(10).join(sections)}
</div>
</div>
<script>
{reveal_js}
</script>
<script>
Reveal.initialize({{
  keyboard: true,
  slideNumber: "c/t",
  center: false,
  width: 1200,
  height: 1080,
  margin: 0.04
}});
</script>
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(deck, encoding="utf-8")
    print(
        f"built {output_path} "
        f"({sum(1 for s in sections if 'proof-step' in s)} proof steps)"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--example",
        action="append",
        required=True,
        help="Lean example file with '-- slide-step' markers (repeatable)",
    )
    parser.add_argument("--output", required=True, help="HTML file to write")
    arguments = parser.parse_args()
    build_deck(arguments.example, pathlib.Path(arguments.output))


if __name__ == "__main__":
    main()
