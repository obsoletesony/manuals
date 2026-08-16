# ObsoleteSony manuals preservation

This repository preserves the exact PSPMAN manual generator recovered from
`D:\PSPMAN\PSPMAN-Japanese-Fallback` at commit
`3e2fb4c11886f69ff89800edadd9545377e83acb` (tree
`df5a3b9d3d9ab2ae6865f48de7fc5ed6b6a4e826`). It is a preservation checkpoint,
not a generalized manual framework.

The relocated generator is deterministic. Its one accepted difference from the
approved reference is the absolute-path-derived cover XObject name and the PDF
bookkeeping mechanically affected by that name. Complete PDF hashes remain
pinned, and the verifier rejects every other content, resource, metadata, text,
dimension, or render difference. See `RECOVERY.md`.

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
- `manuals/pspman/tests/verify_preservation.py`: independent identity comparison
- `LICENSES/Inter-OFL-1.1.txt`: bundled Inter font license
- `package.json`: preserved generator input used only to resolve PSPMAN version

No PSPMAN runtime, audio, firmware, application, website, or private-media source
is included.

## Exact environment used for this checkpoint

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

## Build

From the repository root in PowerShell:

```powershell
$python = 'C:\Users\Eddie\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-pspman-manual.ps1 -Python $python
```

The recovered generator validates the canonical PSPMAN origin. This repository
intentionally has no remote, so the wrapper creates a disposable bare Git
context under the operating-system temporary directory, supplies the expected
origin there, and removes the context afterward. It never adds a remote to this
repository and performs no network operation.

The recovered generator's original command was:

```powershell
python docs/manual/source/build_manual.py
```

## Verify

```powershell
$python = 'C:\Users\Eddie\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-pspman-manual.ps1 -Python $python
```

The verification wrapper runs the recovered build, the recovered structural and
visual validator (`--render --determinism`), and the preservation comparison. The
last step pins both complete PDF hashes, performs two additional clean relocated
builds, and compares page count, size, metadata, extracted text, embedded fonts,
decoded images, parsed objects, and every page render against the approved
artifact. Success is reported as `PRESERVATION-EQUIVALENT-PATH-SENSITIVE`.

See `RECOVERY.md` for the discovery and provenance inventory.
