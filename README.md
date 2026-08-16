# ObsoleteSony manuals

This repository contains shared PDF build mechanics and product-local manual
projects. New manuals begin as plain text. Graphics are added only when they
make an instruction easier to understand.

The PSPMAN User's Guide remains the preserved reference project. Its content,
layout, branding, and canonical PDF bytes are protected by exact regression
tests.

## Repository layout

- `manualkit/` contains product-neutral build, project, theme, and validation code.
- `manuals/pspman/` contains the PSPMAN-specific compositor, content, assets, and tests.
- `docs/ARCHITECTURE.md` defines the shared and product-local boundary.
- `docs/EDITORIAL-GUIDE.md` defines the text-first editorial policy.
- `tests/fixtures/minimal-text-manual/` is a generic text-only test input.
- `scripts/` contains common commands and the preserved PSPMAN wrappers.

The shared runtime does not choose product wording, page count, branding, or
visuals. PSPMAN keeps those decisions in its own project.

## Requirements

- Python 3.12
- Pillow 12.3.0
- pypdf 6.10.0
- pypdfium2 5.12.1
- ReportLab 4.4.9

Exact pins are in `pyproject.toml`.

## Create a manual

Run this from the repository root:

```powershell
.\scripts\new-manual.ps1 `
  -Slug "product-name" `
  -Title "Product Name User's Guide"
```

The command creates only:

```text
manuals/product-name/
  README.md
  manual.json
```

It refuses invalid slugs and existing directories. The starter content is
clearly marked for editing and contains no product claims, artwork directory,
chart, diagram, screenshot, icon, or image placeholder.

## Build and validate

```powershell
.\scripts\build-manual.ps1 -Slug "product-name"
.\scripts\validate-manual.ps1 -Slug "product-name"
```

Builds produce Reader, Print, and Spreads editions under the project's ignored
`output/` directory. Validation checks metadata, page geometry, print boxes,
text bounds, raster-image absence, repeated-build determinism, and rendering.

The PSPMAN-specific commands remain supported:

```powershell
.\scripts\build-pspman-manual.ps1
.\scripts\verify-pspman-manual.ps1
```

## Editorial policy

Start with prose. Add a visual only when removing it would make the instructions
harder to understand. The scaffold does not create decorative panels, cards,
graphics, or empty visual sections. See `docs/EDITORIAL-GUIDE.md`.

## Reproducibility tests

Run the generic fixture and scaffold tests:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

The tests build the fixture and a fresh scaffold repeatedly from different
absolute paths and compare file size, SHA-256, and raw bytes for all editions.
They render every page and reject clipping, overflow, raster images, or shared
runtime product assumptions.

PSPMAN has an additional clean-checkout gate:

```powershell
python .\manuals\pspman\tests\verify_cross_root_portability.py
```

## PSPMAN canonical outputs

| Edition | Bytes | SHA-256 |
| --- | ---: | --- |
| Reader | 227118 | `01680c55b20ab944593cf600f1f6824a83cc0f1c136bafc287c3290ab937d12a` |
| Print | 229260 | `37f54941b87c3730de925c5a4ca32d24f65cb0ca71f6ca6e7f85ec9da3ca294e` |
| Spreads | 506415 | `07c05ea3b71e09c99a0458290ebf3bf51ac6ec4a108df166fcb9a2d974009f4b` |

The immutable approved Reader PDF remains separately preserved at
`manuals/pspman/reference/PSPMAN-User-Guide-approved.pdf`. Historical builds and
reports remain under `manuals/pspman/historical/`; the original path-sensitive
verifier remains under `manuals/pspman/tests/` and in Git history. See
`RECOVERY.md` for provenance.

This repository contains no PSPMAN application runtime, private media, website,
or deployment configuration.
