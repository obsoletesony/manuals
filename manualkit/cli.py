"""Scriptable commands for manual scaffolding, builds, and validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from manualkit.build import build_project
from manualkit.project import ProjectError, create_project, resolve_project
from manualkit.validation import validate_project


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="manualkit")
    commands = parser.add_subparsers(dest="command", required=True)

    new = commands.add_parser("new", help="create a minimal text-only manual")
    new.add_argument("--repo-root", type=Path, required=True)
    new.add_argument("--slug", required=True)
    new.add_argument("--title", required=True)

    build = commands.add_parser("build", help="build all editions for one manual")
    build.add_argument("--repo-root", type=Path, required=True)
    build.add_argument("--slug", required=True)
    build.add_argument("--output-dir", type=Path)

    validate = commands.add_parser("validate", help="build and validate one manual")
    validate.add_argument("--repo-root", type=Path, required=True)
    validate.add_argument("--slug", required=True)
    validate.add_argument("--output-dir", type=Path)
    validate.add_argument("--render-dir", type=Path)
    return parser


def run(arguments: list[str] | None = None) -> int:
    """Run one non-interactive command and return its process status."""

    parser = _parser()
    args = parser.parse_args(arguments)
    try:
        if args.command == "new":
            project = create_project(args.repo_root, args.slug, args.title)
            result = {
                "status": "MANUAL-CREATED",
                "slug": args.slug,
                "directory": str(project.directory),
                "files": sorted(
                    path.relative_to(project.directory).as_posix()
                    for path in project.directory.rglob("*")
                    if path.is_file()
                ),
            }
        else:
            project = resolve_project(args.repo_root, args.slug)
            output_dir = args.output_dir.resolve() if args.output_dir else project.output_dir
            build = build_project(project, output_dir)
            if args.command == "build":
                result = {"status": "MANUAL-BUILT", **build}
            else:
                render_dir = args.render_dir.resolve() if args.render_dir else project.render_dir
                result = {
                    "status": "MANUAL-VALIDATED",
                    **validate_project(project, output_dir, render_dir=render_dir),
                }
        print(json.dumps(result, indent=2))
        return 0
    except (ProjectError, AssertionError) as error:
        print(f"manualkit: {error}", file=sys.stderr)
        return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
