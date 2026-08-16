# PSPMAN manual recovery record

Status: preservation-equivalent with one authorized ReportLab path-sensitive
resource-name exception.

The copied source and inputs are byte-identical to the recovered generator. The
relocated build differs from the approved PDF only in the absolute-path-derived
cover XObject name and mechanically affected object references, stream lengths,
offsets, cross-reference values, and file size. Both complete hashes are pinned;
all parsed objects are identical after replacing only the two documented names.

## Recovered source

- Source repository: `D:\PSPMAN\PSPMAN-Japanese-Fallback`
- Branch: `codex/pspman-operating-instructions-rewrite`
- Commit: `3e2fb4c11886f69ff89800edadd9545377e83acb`
- Tree: `df5a3b9d3d9ab2ae6865f48de7fc5ed6b6a4e826`
- Generator root: `docs/manual`
- Worktree at recovery: clean

The complete manual history was present in the local branch from the initial
rewrite through the final page-chrome cleanup. The recent sequence was
`d8ce33d`, `b751a53`, `d524e3a`, `c67fd9c`, `4daf042`, `44484d5`, and
`3e2fb4c`.

An older 16-page Operating Instructions generator was also found at
`D:\PSPMAN\documentation\tmp\pdfs\manual-adaptation-source`. Its outputs and
content are obsolete and were not substituted for the approved source. Other
older Operating Instructions PDFs were found under
`D:\PSPMAN\documentation\output\pdf` and `D:\PSPMAN\documentation\tmp\pdfs`.

The source worktree had no stash and no untracked manual source. Ignored manual
items were reproducible page/spread PNG renders and Python `__pycache__` files;
they were inspected but not copied as preservation inputs. Unreachable Git
objects were enumerated during recovery, but none superseded the tracked
approved generator.

## Original generator inventory

Generator and validation:

- `source/build_manual.py`
- `source/layout.py`
- `source/styles.py`
- `source/diagrams.py`
- `source/manual_provenance.py`
- `source/validate_manual.py`

Content and configuration:

- `content/manual.yaml` (JSON syntax valid as YAML 1.2)
- `content/facts.json`
- `content/compatibility.json`
- `content/controls.json`
- `.gitattributes`
- `README.md`
- repository-root `package.json` (version and provenance input)

Assets:

- four Inter/Inter Display TrueType fonts and SIL OFL 1.1 license
- owner-supplied PSPMAN3 source logo and its cover rendering
- retained PSPMAN wordmark PNG and SVG
- CC0 PSP-2000 diagram PNG and SVG
- five native 480x272 public-safe screenshots
- five nearest-neighbor 960x544 print screenshots

Tracked outputs:

- `output/PSPMAN-User-Guide.pdf`
- `output/PSPMAN-User-Guide-Print.pdf`
- `output/PSPMAN-User-Guide-Spreads.pdf`
- `output/checksums.json`
- `output/preflight.json`
- `output/layout-review.json`
- `output/measurement-report.json`

## Build and validation assumptions

The source resolves its own directory and expects `content`, `assets`, and
`output` beside `source`; it expects a `package.json` two levels above the manual
directory. It verifies that Git's `origin` URL is
`https://github.com/obsoletesony/PSPMAN`. The preservation wrappers provide this
URL through a disposable bare Git context under the operating-system temporary
directory because this local repository intentionally has no configured remote.
The context is removed after each command and is never used for network access.

Original commands from the PSPMAN repository root:

```powershell
python docs/manual/source/build_manual.py
python docs/manual/source/validate_manual.py --render --determinism
```

The generator uses ReportLab `Canvas(..., invariant=1)` for deterministic PDF
objects and timestamps. The approved artifact itself records both CreationDate
and ModDate as `D:20000101000000+00'00'`. This observed value is authoritative
for byte reproduction even though the recovery ticket described it as a 1999
timestamp.

Metadata is set in `source/build_manual.py`:

- Title: `PSPMAN User's Guide`
- Subject: `User's guide for PSPMAN`
- Author: `ObsoleteSony`
- Creator: `ObsoleteSony`
- Producer: `ReportLab PDF Library - (opensource)`

The validator uses pypdf for PDF inspection, Pillow for image comparison, and
pypdfium2 at 2.5x scale for page and spread rendering. It does not invoke
Poppler. No build-affecting environment variables were set; the observed locale
was `en-US` with UTF-8 console output.

## Font provenance

The font files are exact copies of `vendor/pocketjs/assets/fonts` in the source
PSPMAN checkout. They are Inter Project files licensed under the SIL Open Font
License 1.1, preserved in `assets/fonts/LICENSE.txt` and
`LICENSES/Inter-OFL-1.1.txt`.

| File | Family/style | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `Inter-Regular.ttf` | Inter Regular | 411640 | `40d692fce188e4471e2b3cba937be967878f631ad3ebbbdcd587687c7ebe0c82` |
| `Inter-Bold.ttf` | Inter Bold | 420428 | `288316099b1e0a47a4716d159098005eef7c0066921f34e3200393dbdb01947f` |
| `InterDisplay-Regular.ttf` | Inter Display Regular | 408972 | `99614bda7ff423aaf470990692dd93613a5971ab4446e4a6d5a83b3d74865074` |
| `InterDisplay-Bold.ttf` | Inter Display Bold | 418856 | `b74c8e0dd744b3347faca4c96bc7b2e32f7d6f62300a79b1d1a99331e44a5bc4` |

The reader PDF embeds subsets of all four TrueType files. ReportLab also creates
an unused Base-14 Helvetica resource on each page; Helvetica is not embedded or
used for visible typography.

## Asset provenance

- `PSPMAN3-owner-source.png`: unmodified owner-supplied 8000x2728 RGBA logo.
- `pspman3-cover-white.png`: preserved 2400x356 RGBA cover rendering.
- Screenshot set: internal PSP framebuffer captures using the project-owned
  demonstration metadata PSPMAN / ObsoleteSony / Digital Music Player and no
  commercial audio or artwork.
- `psp-2000-black-cc0.svg`: Todd Partridge / Gen2ly OpenClipart PSP 2000 Black,
  public domain under CC0 1.0; matching PNG is the render cache.

The approved reader PDF contains the 2400x356 cover logo on pages 1 and 15 and
three 960x544 grayscale screenshot images on pages 5, 7, and 9. All source
assets are preserved because they are included in the recovered generator's
input provenance digest, including currently unused reference assets.

## Approved reference and path-sensitivity analysis

The immutable approved reader PDF is:

`manuals/pspman/reference/PSPMAN-User-Guide-approved.pdf`

It was copied byte-for-byte from the recovered tracked output at source commit
`3e2fb4c11886f69ff89800edadd9545377e83acb`. It must never be regenerated or
overwritten. Its identity is 227,124 bytes and SHA-256
`1c8d586db251fbde9d96d20fc58685b3cf99dee0a129677d311431130a90201b`.

Building the copied source at its relocated path produced:

- 227,120 bytes
- SHA-256 `2f2da3de2b749e99eef21461a5f85c1c1bb2d1deeeac33a8976b043f2cc501b8`

The approved PDF is 227,124 bytes with SHA-256
`1c8d586db251fbde9d96d20fc58685b3cf99dee0a129677d311431130a90201b`.
The first binary difference is the cover image XObject resource name:

- approved: `/FormXob.0a5a692857f3d4c7b01de761e63a0cbb`
- relocated: `/FormXob.0819ac937093cb9a14c6e855026d3781`

The decoded cover payload is identical in both PDFs: 2,563,200 bytes, SHA-256
`76a2e933dbb6b56f23318d85b77557a0d693cea326346c22c3c2ce8963f1a6f2`.
All metadata, extracted text, font resources, decoded image payloads, and all 15
page renders are identical. The name changes because the cover is supplied to
ReportLab `drawImage` as an absolute path string, unlike the screenshot path
that is converted through `ImageReader`.

A controlled build using the unchanged generator at its original absolute path
and an external output directory reproduced all three approved PDF hashes
exactly. Its reader PDF is 227,124 bytes and has the approved SHA-256. This
proves that absolute-path-sensitive ReportLab resource naming is the first
differing stage; it is not a font, asset-byte, dependency, metadata, locale, or
rendering change.

The exact control output is retained under
`manuals/pspman/historical/original-path-control-output`. The recovered original
reader, print, and spread editions and their reports are retained under
`manuals/pspman/historical/recovered-output`. Transient approved-versus-relocated
page renders are generated under `manuals/pspman/tests/rendered` and ignored.

The explicit verifier result for the accepted exception is:

`PRESERVATION-EQUIVALENT-PATH-SENSITIVE`

The exception does not permit any other byte or object difference. It fails if
either complete PDF hash changes, if the raw differing object set is not exactly
`5`, `34`, `68`, and `82`, or if any parsed object remains different after only
the two documented XObject names are normalized.

The preservation-root verifier remains available as
`manuals/pspman/tests/verify_historical_path_sensitive.py`. It is intended for
commit `6e1ce48372faa523c370aadb885cee32d1e36ebb`; the complete root commit and its
original verifier also remain recoverable from Git history and
`D:\PSPMAN\manuals-preservation.bundle`.

## Path-independent canonical generator

The portability follow-up changes only cover-image loading in
`source/build_manual.py`: the unchanged PNG bytes are wrapped in ReportLab
`ImageReader(BytesIO(...))` before `drawImage`. Screenshot and diagram paths
already use byte-backed `ImageReader` instances. No dimensions, coordinates,
masks, scaling, interpolation, assets, content, metadata, or PDF bytes are
post-processed.

The content-derived cover resource name is
`/FormXob.491de1e9ee92f99a1d59f3282f625ebe`. Current canonical outputs are:

| Edition | Bytes | SHA-256 |
| --- | ---: | --- |
| Reader | 227118 | `01680c55b20ab944593cf600f1f6824a83cc0f1c136bafc287c3290ab937d12a` |
| Print | 229260 | `37f54941b87c3730de925c5a4ca32d24f65cb0ca71f6ca6e7f85ec9da3ca294e` |
| Spreads | 506415 | `07c05ea3b71e09c99a0458290ebf3bf51ac6ec4a108df166fcb9a2d974009f4b` |

These hashes were established using Python 3.12.13, ReportLab 4.4.9, pypdf
6.10.0, pypdfium2 5.12.1, Pillow 12.3.0, Git 2.53.0.windows.2, Windows locale
`en-US`, and UTF-8 console encoding. `SOURCE_DATE_EPOCH`, `PYTHONHASHSEED`,
`LANG`, `LC_ALL`, and `TZ` were unset.

`verify_cross_root_portability.py` creates two clean clones at different
absolute paths, builds every edition twice in each clone, and compares file
size, SHA-256, and raw bytes within each root and across roots. It uses only
explicit temporary directories and removes them through Python's scoped
temporary-directory handling.

The current verifier proves the portable Reader remains semantically and
pixel-identical to the immutable approved reference. The approved PDF remains
the authoritative released artifact; portability establishes reproducible
future builds without changing that historical status.
