param(
    [Parameter(Mandatory = $true)]
    [string]$Slug,

    [Parameter(Mandatory = $true)]
    [string]$Title,

    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
& $Python -m manualkit.cli new --repo-root $repoRoot --slug $Slug --title $Title
if ($LASTEXITCODE -ne 0) {
    throw "Manual creation failed with exit code $LASTEXITCODE"
}
