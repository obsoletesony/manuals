"""Build PSPMAN twice in each of two clean checkouts at different paths."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
MANUAL_RELATIVE = Path("manuals") / "pspman"
CANONICAL_ORIGIN = "https://github.com/obsoletesony/PSPMAN.git"

EXPECTED = {
    "PSPMAN-User-Guide.pdf": {
        "bytes": 227_118,
        "sha256": "01680c55b20ab944593cf600f1f6824a83cc0f1c136bafc287c3290ab937d12a",
    },
    "PSPMAN-User-Guide-Print.pdf": {
        "bytes": 229_260,
        "sha256": "37f54941b87c3730de925c5a4ca32d24f65cb0ca71f6ca6e7f85ec9da3ca294e",
    },
    "PSPMAN-User-Guide-Spreads.pdf": {
        "bytes": 506_415,
        "sha256": "07c05ea3b71e09c99a0458290ebf3bf51ac6ec4a108df166fcb9a2d974009f4b",
    },
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    require(
        completed.returncode == 0,
        f"Command failed ({completed.returncode}): {command}\n{completed.stdout}\n{completed.stderr}",
    )
    return completed.stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_origin_context(root: Path) -> dict[str, str]:
    git_dir = root / "canonical-origin.git"
    run(["git", "init", "--bare", "--quiet", str(git_dir)], cwd=root)
    run(
        ["git", f"--git-dir={git_dir}", "remote", "add", "origin", CANONICAL_ORIGIN],
        cwd=root,
    )
    environment = os.environ.copy()
    environment["GIT_DIR"] = str(git_dir)
    return environment


def build_twice(
    checkout: Path, output_root: Path, environment: dict[str, str]
) -> dict[str, dict]:
    builder = checkout / MANUAL_RELATIVE / "source" / "build_manual.py"
    builds: list[Path] = []
    for number in (1, 2):
        destination = output_root / f"build-{number}"
        run(
            [sys.executable, str(builder), "--output-dir", str(destination)],
            cwd=checkout,
            env=environment,
        )
        builds.append(destination)

    results: dict[str, dict] = {}
    for filename, expected in EXPECTED.items():
        first = builds[0] / filename
        second = builds[1] / filename
        require(first.read_bytes() == second.read_bytes(), f"Same-root builds differ: {filename}")
        digest = sha256(first)
        require(first.stat().st_size == expected["bytes"], f"Unexpected size: {filename}")
        require(digest == expected["sha256"], f"Unexpected hash: {filename} {digest}")
        results[filename] = {
            "bytes": first.stat().st_size,
            "sha256": digest,
            "first": first,
            "second": second,
        }
    return results


def main() -> None:
    require((REPO_ROOT / ".git").exists(), f"Not a Git checkout: {REPO_ROOT}")
    require(
        not run(["git", "status", "--porcelain"], cwd=REPO_ROOT),
        "Source checkout must be clean before portability verification",
    )
    source_head = run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT)

    with tempfile.TemporaryDirectory(prefix="pspman-portability-") as temporary:
        root = Path(temporary)
        checkouts = {
            "rootA": root / "checkout-a",
            "rootB": root / "different" / "nested" / "checkout-b",
        }
        require(
            str(checkouts["rootA"].resolve()) != str(checkouts["rootB"].resolve()),
            "Checkout paths are not genuinely different",
        )

        for checkout in checkouts.values():
            checkout.parent.mkdir(parents=True, exist_ok=True)
            run(
                [
                    "git",
                    "-c",
                    "core.longpaths=true",
                    "clone",
                    "--quiet",
                    "--no-local",
                    "--single-branch",
                    "--branch",
                    "main",
                    str(REPO_ROOT),
                    str(checkout),
                ],
                cwd=root,
            )
            require(
                run(["git", "rev-parse", "HEAD"], cwd=checkout) == source_head,
                f"Checkout did not reproduce source HEAD: {checkout}",
            )
            require(
                not run(["git", "status", "--porcelain"], cwd=checkout),
                f"Checkout is not clean: {checkout}",
            )

        environment = create_origin_context(root)
        results = {
            label: build_twice(checkout, root / "outputs" / label, environment)
            for label, checkout in checkouts.items()
        }

        editions: dict[str, dict] = {}
        for filename, expected in EXPECTED.items():
            first_root = results["rootA"][filename]["first"]
            second_root = results["rootB"][filename]["first"]
            require(
                first_root.read_bytes() == second_root.read_bytes(),
                f"Cross-root build bytes differ: {filename}",
            )
            editions[filename] = {
                "bytes": expected["bytes"],
                "sha256": expected["sha256"],
                "sameRootDeterminism": {
                    "rootA": True,
                    "rootB": True,
                },
                "crossRootByteIdentical": True,
            }

        for checkout in checkouts.values():
            require(
                not run(["git", "status", "--porcelain"], cwd=checkout),
                f"Build dirtied checkout: {checkout}",
            )

        report = {
            "status": "PATH-INDEPENDENT-BUILDS-VERIFIED",
            "sourceHead": source_head,
            "checkoutPathsDiffer": True,
            "cleanCheckouts": True,
            "sameRootBuildsPerCheckout": 2,
            "editions": editions,
        }
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
