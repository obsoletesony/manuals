# ObsoleteSony manuals

This repository preserves the exact PSPMAN manual generator recovered from
`D:\PSPMAN\PSPMAN-Japanese-Fallback` at commit
`3e2fb4c11886f69ff89800edadd9545377e83acb` (tree
`df5a3b9d3d9ab2ae6865f48de7fc5ed6b6a4e826`). The immutable preservation root is
commit `6e1ce48372faa523c370aadb885cee32d1e36ebb`. This remains a focused PSPMAN
manual repository, not a generalized framework.

The preservation root records the recovered path-sensitive ReportLab behavior.
The current generator makes image identity content-derived by passing the cover
PNG to ReportLab as an `ImageReader` backed by its bytes. Builds are now
byte-identical across different absolute checkout paths. See `RECOVERY.md`.

The immutable approved reader artifact is
`manuals/pspman/reference/PSPMAN-User-Guide-approved.pdf`:

- 15 pages
- 227,124 bytes
- SHA-256 `1c8d586db251fbde9d96d20fc58685b3cf99dee0a129677d311431130a90201b`
- 340.1575 x 340.1575 points per page (reported as 340.158 x 340.158)

## Preserved layout

- `manuals/pspman/source/`: recovered generator and validator, byte-for-byte
- `manuals/pspman/content/`: recovered PSPMAN manual data
- `manuals/pspman/assets/`: recovered fonts, branding, diagrams, and screenshots
- `manuals/pspman/output/`: ignored regenerated outputs and reports
- `manuals/pspman/reference/`: immutable approved reader artifact
- `manuals/pspman/historical/`: recovered editions, reports, and path-control output
- `manuals/pspman/tests/verify_historical_path_sensitive.py`: archived preservation-root verifier
- `manuals/pspman/tests/verify_preservation.py`: current build/reference comparison
- `manuals/pspman/tests/verify_cross_root_portability.py`: clean-checkout portability test
- `LICENSES/Inter-OFL-1.1.txt`: bundled Inter font license
- `package.json`: preserved generator input used only to resolve PSPMAN version

No PSPMAN runtime, audio, firmware, application, website, or private-media source
is included.

## Reproducible environment

- Python 3.12.13
- ReportLab 4.4.9
- pypdf 6.10.0
- pypdfium2 5.12.1
- Pillow 12.3.0
- Git 2.53.0.windows.2
- Windows locale `en-US`; console encoding `utf-8`
- `SOURCE_DATE_EPOCH`, `PYTHONHASHSEED`, `LANG`, `LC_ALL`, and `TZ` unset

The exact dependency pins are in `pyproject.toml`. The original build does not
use Poppler; it renders through pypdfium2. Poppler 26.05.0 was available for
external inspection only.

Current canonical outputs:

| Edition | Bytes | SHA-256 |
| --- | ---: | --- |
| Reader | 227118 | `01680c55b20ab944593cf600f1f6824a83cc0f1c136bafc287c3290ab937d12a` |
| Print | 229260 | `37f54941b87c3730de925c5a4ca32d24f65cb0ca71f6ca6e7f85ec9da3ca294e` |
| Spreads | 506415 | `07c05ea3b71e09c99a0458290ebf3bf51ac6ec4a108df166fcb9a2d974009f4b` |

## Build

From the repository root in PowerShell:

```powershell
$python = 'C:\Users\Eddie\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-pspman-manual.ps1 -Python $python
```

The recovered generator validates the canonical PSPMAN application origin. The
wrapper creates a disposable bare Git context under the operating-system
temporary directory, supplies that application origin there, and removes the
context afterward. It does not alter this repository's remote and performs no
network operation during a build.

The recovered generator's original command was:

```powershell
python docs/manual/source/build_manual.py
```

## Verify

```powershell
$python = 'C:\Users\Eddie\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-pspman-manual.ps1 -Python $python
```

The verification wrapper runs the build, structural and visual validation
(`--render --determinism`), and current build/reference comparison. It pins the
complete PDF hashes and compares page count, size, metadata, text, embedded
fonts, decoded images, parsed objects, and every page render against the approved
artifact. Success is reported as `PORTABLE-BUILD-MATCHES-APPROVED-RENDER`.

After committing a clean candidate, verify two builds in each of two genuinely
different clean checkout paths:

```powershell
& $python .\manuals\pspman\tests\verify_cross_root_portability.py
```

Success is reported as `PATH-INDEPENDENT-BUILDS-VERIFIED` and requires raw-byte,
size, and SHA-256 identity for Reader, Print, and Spreads both within and across
the two roots.

See `RECOVERY.md` for the discovery and provenance inventory.
