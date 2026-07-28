[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$DestinationDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-BatchSafePath {
    param([Parameter(Mandatory = $true)][string]$Path)

    if ($Path.IndexOfAny([char[]]@("`r", "`n", '"', '%', '!')) -ge 0) {
        throw "Path contains characters that are unsafe in a batch wrapper"
    }
}

try {
    $destination = (Get-Item -LiteralPath $DestinationDirectory -Force).FullName
    if (-not (Test-Path -LiteralPath $destination -PathType Container)) {
        throw "DestinationDirectory must identify an existing directory"
    }
    $cloudflared = Join-Path $destination 'cloudflared.exe'
    if (-not (Test-Path -LiteralPath $cloudflared -PathType Leaf)) {
        throw "cloudflared.exe was not found in DestinationDirectory"
    }
    $canonicalBatch = (Get-Item -LiteralPath (
        Join-Path $PSScriptRoot 'TreeQ-Demo-Start.bat'
    ) -Force).FullName
    Assert-BatchSafePath -Path $cloudflared
    Assert-BatchSafePath -Path $canonicalBatch

    $wrapperPath = Join-Path $destination 'TreeQ-Demo-Start.bat'
    $wrapper = @(
        '@echo off'
        'setlocal'
        ('set "TREEQ_CLOUDFLARED={0}"' -f $cloudflared)
        ('call "{0}" %*' -f $canonicalBatch)
        'set "TREEQ_EXIT_CODE=%ERRORLEVEL%"'
        'endlocal & exit /b %TREEQ_EXIT_CODE%'
        ''
    ) -join "`r`n"
    [System.IO.File]::WriteAllText(
        $wrapperPath,
        $wrapper,
        [System.Text.Encoding]::ASCII
    )
    Write-Output "Installed TreeQ-Demo-Start.bat"
    Write-Output "Legacy scripts were not modified."
    exit 0
}
catch {
    Write-Output "ERROR: $($_.Exception.Message)"
    exit 1
}
