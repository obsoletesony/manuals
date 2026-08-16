from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from manualkit.build import build_project
from manualkit.project import ProjectError, create_project, load_project, resolve_project
from manualkit.validation import cross_root_determinism, validate_project


class ScaffoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="manualkit-scaffold-test-")
        self.repo_root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_valid_project_creation_and_inventory(self) -> None:
        project = create_project(self.repo_root, "product-name", "Product Name User's Guide")
        files = sorted(
            path.relative_to(project.directory).as_posix()
            for path in project.directory.rglob("*")
            if path.is_file()
        )
        self.assertEqual(files, ["README.md", "manual.json"])
        self.assertFalse((project.directory / "assets").exists())
        block_types = {
            block["type"]
            for section in project.sections
            for block in section["blocks"]
        }
        self.assertEqual(block_types, {"paragraph", "ordered-list", "code"})
        self.assertTrue(
            all(
                term not in json.dumps(project.manifest).lower()
                for term in ("chart", "diagram", "screenshot", "icon", "image-placeholder")
            )
        )

    def test_invalid_slug_rejection(self) -> None:
        for slug in ("Product", "two words", "double--hyphen", "-leading", "trailing-"):
            with self.subTest(slug=slug), self.assertRaisesRegex(ProjectError, "slug"):
                create_project(self.repo_root, slug, "Title")

    def test_existing_directory_overwrite_refusal(self) -> None:
        create_project(self.repo_root, "existing", "Existing User's Guide")
        with self.assertRaisesRegex(ProjectError, "Refusing to overwrite"):
            create_project(self.repo_root, "existing", "Replacement")

    def test_missing_required_metadata(self) -> None:
        project = create_project(self.repo_root, "missing-metadata", "Metadata User's Guide")
        path = project.directory / "manual.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        del manifest["document"]["author"]
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
        with self.assertRaisesRegex(ProjectError, "author"):
            load_project(project.directory)

    def test_unknown_manual_slug(self) -> None:
        with self.assertRaisesRegex(ProjectError, "Unknown manual slug"):
            resolve_project(self.repo_root, "unknown")

    def test_scaffold_build_validation_and_cross_root_determinism(self) -> None:
        project = create_project(self.repo_root, "buildable", "Buildable User's Guide")
        build_project(project)
        result = validate_project(project, check_determinism=True)
        self.assertEqual(result["rasterImageXObjects"], 0)
        self.assertEqual(result["clippingAndOverflow"], "pass")
        cross_root = cross_root_determinism(project.directory)
        self.assertEqual(len(cross_root), 3)
        self.assertTrue(all(item["crossRootByteIdentical"] for item in cross_root.values()))


if __name__ == "__main__":
    unittest.main()
