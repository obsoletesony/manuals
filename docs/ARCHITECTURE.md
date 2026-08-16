# Manual framework architecture

This document records the extraction boundary for the reusable manual framework.
It describes current code and the decisions used for this refactor. It is not a
proposal for a universal page-description language.

## Dependency direction

`manualkit` contains product-neutral PDF mechanics. Product manuals may import
it. `manualkit` must not import a product project or encode product names,
hardware, media formats, interface concepts, or branding.

The PSPMAN project remains under `manuals/pspman`. Its explicit page compositor,
content, visual language, and validation policy remain local. A shared function
is used by PSPMAN only when moving it preserves the canonical PDF bytes.

## Extraction boundary

### Reusable deterministic PDF infrastructure

The following mechanics are suitable for `manualkit`:

- invariant ReportLab canvas creation;
- deterministic document metadata;
- deterministic font registration from explicit name/path mappings;
- byte-backed image readers for explicitly supplied images;
- stable Reader, Print, and Spreads output paths;
- print trim and bleed boxes;
- spread assembly with explicit metadata;
- project lookup, output-directory handling, and clear configuration errors;
- generic structural, rendering, and reproducibility checks.

These functions operate on values supplied by a product project. They do not
choose content, styling, page count, or visuals.

### PSPMAN-specific content and page composition

The following remain in `manuals/pspman`:

- the 15-page sequence and table of contents;
- all prose, controls, compatibility facts, and application metadata;
- block measurement, explicit page templates, and page-level composition;
- PSPMAN bookmarks, hyperlinks, covers, headers, footers, and page numbering;
- PSPMAN-specific content and provenance assertions.

No declarative system is being inferred from this one document.

### PSPMAN-specific styling and branding

The trim geometry, margins, typography, bundled Inter fonts, colors, wordmarks,
cover treatment, screenshot treatment, and product layout classes remain local.
The neutral theme for future manuals is separate and is not applied to PSPMAN.

### Optional visuals and diagrams

PSPMAN diagrams, screenshots, branding, image conversion, and visual measurement
remain product-local. The shared layer can load an image only when a product
explicitly supplies one. It never creates a chart, diagram, screenshot frame,
placeholder, icon, callout, or decorative panel.

### Validation and reproducibility

Shared validation covers properties that apply to any manual: required files,
edition dimensions, metadata, clipping and overflow, deterministic output,
rendering, and cross-root byte identity. PSPMAN retains its product facts,
approved screenshot inventory, monochrome policy, wording checks, canonical
hashes, and approved-reference comparison.

## Compatibility rule

Every extraction step must preserve these PSPMAN outputs exactly:

| Edition | Bytes | SHA-256 |
| --- | ---: | --- |
| Reader | 227118 | `01680c55b20ab944593cf600f1f6824a83cc0f1c136bafc287c3290ab937d12a` |
| Print | 229260 | `37f54941b87c3730de925c5a4ca32d24f65cb0ca71f6ca6e7f85ec9da3ca294e` |
| Spreads | 506415 | `07c05ea3b71e09c99a0458290ebf3bf51ac6ec4a108df166fcb9a2d974009f4b` |

If sharing a function changes those bytes, the function stays product-local.

## Text-first default

New projects use a deliberately quiet theme with headings, prose, lists, code or
path blocks, compact tables, and page numbers. A project may add a visual later
as an explicit product decision. The framework does not create empty asset
directories or visual placeholders.
