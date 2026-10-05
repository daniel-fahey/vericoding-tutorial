import html
import pathlib
import re
import subprocess
import tempfile
import unittest


def normalized_text(fragment):
    without_tags = re.sub(r"<[^>]+>", "", fragment)
    return " ".join(html.unescape(without_tags).split())


class DeckBuildTests(unittest.TestCase):
    def test_each_tactic_has_a_lean_state_slide(self):
        repository = pathlib.Path(__file__).resolve().parents[1]
        fixture = repository / "tests" / "fixtures" / "DeckStepExample.lean"
        expected_tactics = ["intro hp hq", "constructor", "all_goals assumption"]

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = pathlib.Path(temporary_directory)
            output_path = temporary_path / "index.html"
            build = subprocess.run(
                [
                    "python3",
                    "scripts/build_deck.py",
                    "--example",
                    "tests/fixtures/DeckStepExample.lean",
                    "--output",
                    str(output_path),
                ],
                cwd=repository,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertTrue(
                output_path.is_file(),
                f"Deck output was not created: {build.stderr or build.stdout}",
            )
            self.assertEqual(
                build.returncode,
                0,
                f"Deck generation failed: {build.stderr or build.stdout}",
            )

            deck = output_path.read_text(encoding="utf-8")
            slides = re.findall(
                r'<section class="proof-step">(.*?)</section>', deck, re.DOTALL
            )
            self.assertEqual(len(slides), len(expected_tactics))

            goal_panels = []
            for slide, tactic in zip(slides, expected_tactics):
                highlights = re.findall(
                    r'<mark class="current-tactic">(.*?)</mark>', slide, re.DOTALL
                )
                self.assertEqual(len(highlights), 1)
                self.assertEqual(normalized_text(highlights[0]), tactic)

                panels = re.findall(
                    r'<pre class="goal-state">(.*?)</pre>', slide, re.DOTALL
                )
                self.assertEqual(len(panels), 1)
                goal_panels.append(panels[0])

            fixture_lines = fixture.read_text(encoding="utf-8").splitlines()
            marker_lines = [
                index
                for index, line in enumerate(fixture_lines)
                if line.strip() == "-- slide-step"
            ]
            self.assertEqual(len(marker_lines), len(expected_tactics))
            self.assertEqual(
                [fixture_lines[index + 1].strip() for index in marker_lines],
                expected_tactics,
            )

            oracle_lines = []
            inserted_probes = 0
            for line in fixture_lines:
                oracle_lines.append(line)
                if line.strip() in expected_tactics[:2]:
                    indentation = line[: len(line) - len(line.lstrip())]
                    oracle_lines.append(f"{indentation}trace_state")
                    inserted_probes += 1
            self.assertEqual(inserted_probes, 2)

            oracle_path = temporary_path / "DeckStepOracle.lean"
            oracle_path.write_text("\n".join(oracle_lines) + "\n", encoding="utf-8")
            lean = subprocess.run(
                ["lean", str(oracle_path)],
                cwd=temporary_path,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                lean.returncode,
                0,
                f"Lean rejected the proof: {lean.stdout}\n{lean.stderr}",
            )

            lean_output = normalized_text(lean.stdout + "\n" + lean.stderr)
            position = 0
            for panel in goal_panels[:2]:
                state = normalized_text(panel)
                self.assertTrue(state)
                position = lean_output.find(state, position)
                self.assertNotEqual(position, -1)
                position += len(state)
            self.assertEqual(normalized_text(goal_panels[2]), "")


if __name__ == "__main__":
    unittest.main()
