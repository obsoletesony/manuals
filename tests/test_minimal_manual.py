from __future__ import annotations

from pathlib import Path
import re
import tempfile
import unittest

from manualkit.build import build_project
from manualkit.project import load_project
from manualkit.validation import cross_root_determinism, validate_project


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "minimal-text-manual"


class MinimalManualTests(unittest.TestCase):
    def test_fixture_build_validation_render_and_determinism(self) -> None:
        project = load_project(FIXTURE)
        with tempfile.TemporaryDirectory(prefix="manualkit-fixture-output-") as temporary:
            root = Path(temporary)
            output = root / "output"
            render = root / "rendered"
            build_project(project, output)
            result = validate_project(
                project,
                output,
                render_dir=render,
                check_determinism=True,
            )
            self.assertEqual(result["rasterImageXObjects"], 0)
            self.assertEqual(result["clippingAndOverflow"], "pass")
            self.assertEqual(result["render"]["readerPages"], result["pages"])
            self.assertEqual(result["render"]["printPages"], result["pages"])
            self.assertEqual(result["render"]["spreadPages"], result["spreads"])
            self.assertTrue((render / "contact-sheet.png").is_file())

        cross_root = cross_root_determinism(FIXTURE)
        self.assertEqual(len(cross_root), 3)
        self.assertTrue(all(item["crossRootByteIdentical"] for item in cross_root.values()))

    def test_shared_runtime_has_no_product_assumptions(self) -> None:
        forbidden = re.compile(
            r"\b(?:PSPMAN|PSP|Sony|Walkman|FLAC|cassette)\b|Memory Stick",
            re.IGNORECASE,
        )
        findings: list[str] = []
        for path in sorted((REPO_ROOT / "manualkit").rglob("*.py")):
            match = forbidden.search(path.read_text(encoding="utf-8"))
            if match:
                findings.append(f"{path.relative_to(REPO_ROOT)}: {match.group(0)}")
        self.assertEqual(findings, [])

    def test_fixture_contains_no_visual_assets_or_product_references(self) -> None:
        files = [path for path in FIXTURE.rglob("*") if path.is_file()]
        self.assertEqual([path.name for path in files], ["manual.json"])
        text = files[0].read_text(encoding="utf-8")
        self.assertNotRegex(text, re.compile(r"PSPMAN|Sony", re.IGNORECASE))
        self.assertNotRegex(
            text,
            re.compile(r"\.(?:png|jpe?g|svg)|screenshot|diagram|chart", re.IGNORECASE),
        )


if __name__ == "__main__":
    unittest.main()
