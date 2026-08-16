param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$builder = Join-Path $repoRoot "manuals\pspman\source\build_manual.py"
$validator = Join-Path $repoRoot "manuals\pspman\source\validate_manual.py"
$preservation = Join-Path $repoRoot "manuals\pspman\tests\verify_preservation.py"
$temporaryRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$temporaryGit = Join-Path $temporaryRoot ("pspman-manual-origin-" + [Guid]::NewGuid().ToString("N") + ".git")

$saved = @{}
foreach ($name in @("GIT_DIR")) {
    $saved[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
}

try {
    & git init --bare --quiet $temporaryGit
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create the disposable Git origin context"
    }
    & git --git-dir=$temporaryGit remote add origin "https://github.com/obsoletesony/PSPMAN.git"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not configure the disposable Git origin context"
    }
    $env:GIT_DIR = $temporaryGit

    & $Python $builder
    if ($LASTEXITCODE -ne 0) {
        throw "PSPMAN manual build failed with exit code $LASTEXITCODE"
    }

    & $Python $validator --render --determinism
    if ($LASTEXITCODE -ne 0) {
        throw "Recovered PSPMAN validator failed with exit code $LASTEXITCODE"
    }

    & $Python $preservation
    if ($LASTEXITCODE -ne 0) {
        throw "PSPMAN preservation comparison failed with exit code $LASTEXITCODE"
    }
}
finally {
    foreach ($name in $saved.Keys) {
        [Environment]::SetEnvironmentVariable($name, $saved[$name], "Process")
    }
    if (Test-Path -LiteralPath $temporaryGit) {
        $resolvedTemporaryGit = (Resolve-Path -LiteralPath $temporaryGit).Path
        $temporaryLeaf = Split-Path -Leaf $resolvedTemporaryGit
        if (-not $resolvedTemporaryGit.StartsWith($temporaryRoot, [StringComparison]::OrdinalIgnoreCase) -or
            -not $temporaryLeaf.StartsWith("pspman-manual-origin-", [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove unexpected temporary Git path: $resolvedTemporaryGit"
        }
        Remove-Item -LiteralPath $resolvedTemporaryGit -Recurse -Force
    }
}
