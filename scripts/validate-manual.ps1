param(
    [Parameter(Mandatory = $true)]
    [string]$Slug,

    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
& $Python -m manualkit.cli validate --repo-root $repoRoot --slug $Slug
if ($LASTEXITCODE -ne 0) {
    throw "Manual validation failed with exit code $LASTEXITCODE"
}
