Set-StrictMode -Version Latest

function Get-TreeQContainedFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Root
    )

    $rootItem = Get-Item -LiteralPath $Root -Force -ErrorAction Stop
    if (-not $rootItem.PSIsContainer) {
        throw "Allowed root is not a directory"
    }

    $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    if ($item.PSIsContainer) {
        throw "Expected a regular file"
    }

    $rootFull = [System.IO.Path]::GetFullPath($rootItem.FullName).TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    )
    $fileFull = [System.IO.Path]::GetFullPath($item.FullName)
    $rootPrefix = $rootFull + [System.IO.Path]::DirectorySeparatorChar
    if (-not $fileFull.StartsWith(
        $rootPrefix,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw "File is outside the allowed root"
    }

    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Reparse points are not allowed"
    }
    $cursor = $item.Directory
    while ($null -ne $cursor) {
        if (($cursor.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Reparse points are not allowed"
        }
        if ($cursor.FullName.Equals(
            $rootFull,
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            break
        }
        $cursor = $cursor.Parent
    }

    return $fileFull
}

function ConvertFrom-TreeQHex {
    param([Parameter(Mandatory = $true)][string]$Hex)

    if ($Hex -notmatch '^[0-9a-f]+$' -or ($Hex.Length % 2) -ne 0) {
        throw "Hex input is invalid"
    }
    $bytes = New-Object byte[] ($Hex.Length / 2)
    for ($index = 0; $index -lt $bytes.Length; $index++) {
        $bytes[$index] = [Convert]::ToByte($Hex.Substring($index * 2, 2), 16)
    }
    return $bytes
}

function Test-TreeQApiEndpoint {
    param(
        [Parameter(Mandatory = $true)][string]$Endpoint,
        [switch]$AllowAnyLoopbackPort
    )

    if ($Endpoint.Contains('?') -or $Endpoint.Contains('#')) {
        return $false
    }
    try {
        $uri = [Uri]$Endpoint
    }
    catch {
        return $false
    }
    if (
        -not $uri.IsAbsoluteUri -or
        $uri.UserInfo -or
        $uri.Query -or
        $uri.Fragment -or
        $uri.AbsolutePath -ne '/'
    ) {
        return $false
    }

    $isTunnel = (
        $uri.Scheme -eq 'https' -and
        $uri.IsDefaultPort -and
        $uri.DnsSafeHost -match '^[a-z0-9-]+\.trycloudflare\.com$'
    )
    $localPortAllowed = $uri.Port -eq 8000
    if ($AllowAnyLoopbackPort) {
        $localPortAllowed = $uri.Port -ge 1 -and $uri.Port -le 65535
    }
    $isLocal = (
        $uri.Scheme -eq 'http' -and
        ($uri.DnsSafeHost -eq '127.0.0.1' -or $uri.DnsSafeHost -eq 'localhost') -and
        $localPortAllowed
    )
    return ($isTunnel -or $isLocal)
}

function Test-TreeQWebOrigin {
    param([Parameter(Mandatory = $true)][string]$Origin)

    if ($Origin.Contains('?') -or $Origin.Contains('#')) {
        return $false
    }
    try {
        $uri = [Uri]$Origin
    }
    catch {
        return $false
    }
    if (
        -not $uri.IsAbsoluteUri -or
        $uri.UserInfo -or
        $uri.Query -or
        $uri.Fragment -or
        $uri.AbsolutePath -ne '/'
    ) {
        return $false
    }
    if (
        $uri.Scheme -eq 'https' -and
        $uri.IsDefaultPort -and
        $uri.DnsSafeHost -eq 'treeqcarbon.vercel.app'
    ) {
        return $true
    }
    return (
        $uri.Scheme -eq 'http' -and
        $uri.Port -eq 3000 -and
        ($uri.DnsSafeHost -eq '127.0.0.1' -or $uri.DnsSafeHost -eq 'localhost')
    )
}

function Get-TreeQOwnedProcessObject {
    param([Parameter(Mandatory = $true)]$Entry)

    try {
        $entryPid = [int]$Entry.pid
        $entryPath = [string]$Entry.executable_path
        $entryStart = [string]$Entry.start_time_utc
    }
    catch {
        return $null
    }
    if (
        $entryPid -le 0 -or
        -not [System.IO.Path]::IsPathRooted($entryPath) -or
        [string]::IsNullOrWhiteSpace($entryStart)
    ) {
        return $null
    }

    $expectedStart = [DateTimeOffset]::MinValue
    $parsed = [DateTimeOffset]::TryParse(
        $entryStart,
        [System.Globalization.CultureInfo]::InvariantCulture,
        [System.Globalization.DateTimeStyles]::RoundtripKind,
        [ref]$expectedStart
    )
    if (-not $parsed) {
        return $null
    }

    try {
        $process = Get-Process -Id $entryPid -ErrorAction Stop
        $null = $process.Handle
        $actualPath = [System.IO.Path]::GetFullPath($process.Path)
        $expectedPath = [System.IO.Path]::GetFullPath($entryPath)
        $actualStart = $process.StartTime.ToUniversalTime()
    }
    catch {
        return $null
    }
    if (-not $actualPath.Equals(
        $expectedPath,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        $process.Dispose()
        return $null
    }
    if ($actualStart.Ticks -ne $expectedStart.UtcDateTime.Ticks) {
        $process.Dispose()
        return $null
    }
    return $process
}

function New-TreeQDemoToken {
    [CmdletBinding()]
    param()

    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $rng.GetBytes($bytes)
    }
    finally {
        $rng.Dispose()
    }
    return ([BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
}

function Get-TreeQTunnelUrl {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text)

    $matches = [regex]::Matches($Text, 'https://[^\s<>"'']+')
    foreach ($match in $matches) {
        $candidate = $match.Value.TrimEnd('.', ',', ';', ':', ')', ']', '}')
        if (Test-TreeQApiEndpoint -Endpoint $candidate) {
            $uri = [Uri]$candidate
            return "https://$($uri.DnsSafeHost.ToLowerInvariant())"
        }
    }
    return $null
}

function Protect-TreeQLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text,
        [Parameter(Mandatory = $false)][string[]]$Secrets = @()
    )

    $protected = $Text
    $orderedSecrets = @(
        $Secrets |
            Where-Object { -not [string]::IsNullOrEmpty($_) } |
            Sort-Object Length -Descending -Unique
    )
    foreach ($secret in $orderedSecrets) {
        $protected = $protected.Replace($secret, '[REDACTED]')
    }
    return $protected
}

function Get-TreeQSha256 {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $false)][string]$Root
    )

    if ([string]::IsNullOrWhiteSpace($Root)) {
        $Root = Split-Path -Parent $Path
    }
    $filePath = Get-TreeQContainedFile -Path $Path -Root $Root
    $stream = [System.IO.File]::Open(
        $filePath,
        [System.IO.FileMode]::Open,
        [System.IO.FileAccess]::Read,
        [System.IO.FileShare]::Read
    )
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hash = $sha.ComputeHash($stream)
    }
    finally {
        $sha.Dispose()
        $stream.Dispose()
    }
    return ([BitConverter]::ToString($hash)).Replace('-', '').ToLowerInvariant()
}

function Get-TreeQStandaloneServer {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$RepoRoot)

    if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) {
        return $null
    }
    $candidates = @(
        (Join-Path $RepoRoot 'apps\web\.next\standalone\apps\web\server.js'),
        (Join-Path $RepoRoot 'apps\web\.next\standalone\server.js')
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            try {
                return Get-TreeQContainedFile -Path $candidate -Root $RepoRoot
            }
            catch {
                return $null
            }
        }
    }
    return $null
}

function New-TreeQHandoffUrl {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$BaseUrl,
        [Parameter(Mandatory = $true)][string]$ApiEndpoint,
        [Parameter(Mandatory = $true)][string]$Token
    )

    if (-not (Test-TreeQWebOrigin -Origin $BaseUrl)) {
        throw "Web origin is not allowed"
    }
    if (-not (Test-TreeQApiEndpoint -Endpoint $ApiEndpoint)) {
        throw "API endpoint is not allowed"
    }
    if ($Token -cnotmatch '^[0-9a-f]{64}$') {
        throw "Demo token must be exactly 64 lowercase hex characters"
    }

    $baseUri = [Uri]$BaseUrl
    $apiUri = [Uri]$ApiEndpoint
    $baseOrigin = "{0}://{1}" -f $baseUri.Scheme, $baseUri.Authority
    $apiOrigin = "{0}://{1}" -f $apiUri.Scheme, $apiUri.Authority
    $escapedApi = [Uri]::EscapeDataString($apiOrigin)
    $escapedToken = [Uri]::EscapeDataString($Token)
    return "$baseOrigin/demo#api=$escapedApi&token=$escapedToken"
}

function Test-TreeQOwnedProcess {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)]$Entry)

    $process = Get-TreeQOwnedProcessObject -Entry $Entry
    if ($null -eq $process) {
        return $false
    }
    $process.Dispose()
    return $true
}

function Stop-TreeQOwnedProcesses {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$RegistryPath,
        [Parameter(Mandatory = $true)][string]$AllowedRoot
    )

    $safeRegistry = Get-TreeQContainedFile -Path $RegistryPath -Root $AllowedRoot
    $registryItem = Get-Item -LiteralPath $safeRegistry -Force
    if ($registryItem.Length -gt 1048576) {
        throw "Process registry is too large"
    }
    try {
        $registry = [System.IO.File]::ReadAllText(
            $safeRegistry,
            [System.Text.UTF8Encoding]::new($false, $true)
        ) | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        throw "Process registry is not valid JSON"
    }
    if (
        $null -eq $registry -or
        $registry.schema_version -ne 1 -or
        $null -eq $registry.processes
    ) {
        throw "Process registry schema is invalid"
    }

    $validatedEntries = New-Object System.Collections.ArrayList
    foreach ($entry in @($registry.processes)) {
        $propertyNames = @($entry.PSObject.Properties.Name | Sort-Object)
        if (
            ($propertyNames -join ',') -ne
                'executable_path,pid,role,start_time_utc' -or
            $entry.pid -isnot [int] -and $entry.pid -isnot [long] -or
            [string]::IsNullOrWhiteSpace([string]$entry.executable_path) -or
            -not [System.IO.Path]::IsPathRooted([string]$entry.executable_path) -or
            [string]::IsNullOrWhiteSpace([string]$entry.start_time_utc) -or
            [string]::IsNullOrWhiteSpace([string]$entry.role)
        ) {
            throw "Process registry entry is invalid"
        }
        $parsedStart = [DateTimeOffset]::MinValue
        if (-not [DateTimeOffset]::TryParse(
            [string]$entry.start_time_utc,
            [System.Globalization.CultureInfo]::InvariantCulture,
            [System.Globalization.DateTimeStyles]::RoundtripKind,
            [ref]$parsedStart
        )) {
            throw "Process registry start time is invalid"
        }
        [void]$validatedEntries.Add($entry)
    }

    $stopped = New-Object System.Collections.ArrayList
    foreach ($entry in $validatedEntries) {
        $process = Get-TreeQOwnedProcessObject -Entry $entry
        if ($null -eq $process) {
            continue
        }
        try {
            $process.Kill()
            [void]$process.WaitForExit(5000)
            [void]$stopped.Add([int]$entry.pid)
        }
        catch {
            throw "Could not stop an owned process"
        }
        finally {
            $process.Dispose()
        }
    }
    return @($stopped)
}

function Test-TreeQReadiness {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Endpoint,
        [Parameter(Mandatory = $true)][string]$Token,
        [Parameter(Mandatory = $false)][ValidateRange(1, 120)][int]$TimeoutSec = 30
    )

    if (
        $Token -cnotmatch '^[0-9a-f]{64}$' -or
        -not (Test-TreeQApiEndpoint -Endpoint $Endpoint -AllowAnyLoopbackPort)
    ) {
        return [pscustomobject]@{
            Ready = $false
            PipelineVersion = $null
            Detail = 'invalid input'
        }
    }

    $challenge = New-TreeQDemoToken
    try {
        $response = Invoke-RestMethod `
            -Method Get `
            -Uri "$($Endpoint.TrimEnd('/'))/api/v1/health/demo-ready" `
            -Headers @{
                'X-TreeQ-Demo-Token' = $Token
                'X-TreeQ-Demo-Challenge' = $challenge
            } `
            -TimeoutSec $TimeoutSec `
            -ErrorAction Stop
    }
    catch {
        return [pscustomobject]@{
            Ready = $false
            PipelineVersion = $null
            Detail = 'unavailable'
        }
    }

    try {
        $hmac = New-Object System.Security.Cryptography.HMACSHA256
        try {
            $hmac.Key = ConvertFrom-TreeQHex -Hex $Token
            $proofBytes = $hmac.ComputeHash(
                [System.Text.Encoding]::ASCII.GetBytes($challenge)
            )
        }
        finally {
            $hmac.Dispose()
        }
        $expectedProof = (
            [BitConverter]::ToString($proofBytes)
        ).Replace('-', '').ToLowerInvariant()
        $receivedProof = [string]$response.challenge_hmac
        $pipelineVersion = [string]$response.pipeline_version
        if (
            [string]$response.status -ne 'ready' -or
            [string]::IsNullOrWhiteSpace($pipelineVersion) -or
            $receivedProof -notmatch '^[0-9a-f]{64}$' -or
            $receivedProof.Length -ne $expectedProof.Length
        ) {
            throw "Readiness response is invalid"
        }
        $difference = 0
        for ($index = 0; $index -lt $expectedProof.Length; $index++) {
            $difference = $difference -bor (
                [int]$expectedProof[$index] -bxor [int]$receivedProof[$index]
            )
        }
        if ($difference -ne 0) {
            throw "Readiness proof does not match"
        }
    }
    catch {
        return [pscustomobject]@{
            Ready = $false
            PipelineVersion = $null
            Detail = 'proof mismatch'
        }
    }

    return [pscustomobject]@{
        Ready = $true
        PipelineVersion = $pipelineVersion
        Detail = 'ready'
    }
}

Export-ModuleMember -Function @(
    'New-TreeQDemoToken',
    'Get-TreeQTunnelUrl',
    'Protect-TreeQLog',
    'Get-TreeQSha256',
    'Get-TreeQStandaloneServer',
    'New-TreeQHandoffUrl',
    'Test-TreeQOwnedProcess',
    'Stop-TreeQOwnedProcesses',
    'Test-TreeQReadiness'
)
