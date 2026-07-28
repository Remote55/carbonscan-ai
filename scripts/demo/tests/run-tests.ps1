[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$script:Passed = 0
$script:Failed = 0

function Assert-True {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Name
    )

    if ($Condition) {
        $script:Passed++
        Write-Output "PASS $Name"
    }
    else {
        $script:Failed++
        Write-Output "FAIL $Name"
    }
}

function Assert-Equal {
    param(
        [Parameter(Mandatory = $false)]$Actual,
        [Parameter(Mandatory = $false)]$Expected,
        [Parameter(Mandatory = $true)][string]$Name
    )

    Assert-True -Condition ($Actual -eq $Expected) -Name $Name
}

function Assert-Null {
    param(
        [Parameter(Mandatory = $false)]$Actual,
        [Parameter(Mandatory = $true)][string]$Name
    )

    Assert-True -Condition ($null -eq $Actual) -Name $Name
}

function Assert-Throws {
    param(
        [Parameter(Mandatory = $true)][scriptblock]$Action,
        [Parameter(Mandatory = $true)][string]$Name
    )

    try {
        & $Action
        Assert-True -Condition $false -Name $Name
    }
    catch {
        Assert-True -Condition $true -Name $Name
    }
}

function New-TestProcessEntry {
    param(
        [Parameter(Mandatory = $true)][System.Diagnostics.Process]$Process,
        [Parameter(Mandatory = $true)][string]$Role
    )

    $Process.Refresh()
    return [ordered]@{
        pid = $Process.Id
        executable_path = $Process.Path
        start_time_utc = $Process.StartTime.ToUniversalTime().ToString('o')
        role = $Role
    }
}

function Write-TestRegistry {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][object[]]$Entries
    )

    $payload = [ordered]@{
        schema_version = 1
        processes = $Entries
    } | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText($Path, $payload, [System.Text.UTF8Encoding]::new($false))
}

function Get-FreeTcpPort {
    $listener = [System.Net.Sockets.TcpListener]::new(
        [System.Net.IPAddress]::Loopback,
        0
    )
    $listener.Start()
    try {
        return ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port
    }
    finally {
        $listener.Stop()
    }
}

function Start-TestProcess {
    param([Parameter(Mandatory = $true)][hashtable]$StartProcessArguments)

    try {
        return Start-Process @StartProcessArguments
    }
    catch {
        if ($_.Exception.Message -notmatch "Key in dictionary: 'Path'.*'PATH'") {
            throw
        }
        $preservedPath = [Environment]::GetEnvironmentVariable(
            'Path',
            [EnvironmentVariableTarget]::Process
        )
        [Environment]::SetEnvironmentVariable(
            'PATH',
            $null,
            [EnvironmentVariableTarget]::Process
        )
        if ([string]::IsNullOrWhiteSpace(
            [Environment]::GetEnvironmentVariable(
                'Path',
                [EnvironmentVariableTarget]::Process
            )
        )) {
            [Environment]::SetEnvironmentVariable(
                'Path',
                $preservedPath,
                [EnvironmentVariableTarget]::Process
            )
        }
        return Start-Process @StartProcessArguments
    }
}

function Start-TestReadinessServer {
    param(
        [Parameter(Mandatory = $true)][string]$PowerShellPath,
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$Token,
        [Parameter(Mandatory = $true)][bool]$Tamper
    )

    $port = Get-FreeTcpPort
    $serverPath = Join-Path $Directory ("readiness-server-{0}.ps1" -f $port)
    $readyPath = Join-Path $Directory ("readiness-ready-{0}" -f $port)
    $stdoutPath = Join-Path $Directory ("readiness-{0}.out" -f $port)
    $stderrPath = Join-Path $Directory ("readiness-{0}.err" -f $port)
    $serverSource = @'
param([int]$Port)
$ErrorActionPreference = 'Stop'
$listener = New-Object System.Net.Sockets.TcpListener(
    [System.Net.IPAddress]::Loopback,
    $Port
)
$listener.Start()
[System.IO.File]::WriteAllText($env:TREEQ_TEST_READY_FILE, 'ready')
try {
    $client = $listener.AcceptTcpClient()
    $stream = $client.GetStream()
    $reader = New-Object System.IO.StreamReader(
        $stream,
        [System.Text.Encoding]::ASCII,
        $false,
        1024,
        $true
    )
    $challenge = ''
    while (($line = $reader.ReadLine()) -ne $null -and $line -ne '') {
        if ($line.StartsWith('X-TreeQ-Demo-Challenge:', [StringComparison]::OrdinalIgnoreCase)) {
            $challenge = $line.Substring($line.IndexOf(':') + 1).Trim()
        }
    }
    $key = [byte[]]::new(32)
    for ($index = 0; $index -lt 32; $index++) {
        $key[$index] = [Convert]::ToByte($env:TREEQ_TEST_TOKEN.Substring($index * 2, 2), 16)
    }
    $hmac = New-Object System.Security.Cryptography.HMACSHA256
    try {
        $hmac.Key = $key
        $proofBytes = $hmac.ComputeHash([System.Text.Encoding]::ASCII.GetBytes($challenge))
    }
    finally {
        $hmac.Dispose()
    }
    $proof = ([BitConverter]::ToString($proofBytes)).Replace('-', '').ToLowerInvariant()
    if ($env:TREEQ_TEST_TAMPER -eq 'true') {
        $proof = '0' * 64
    }
    $body = '{"status":"ready","mode":"demo","pipeline_version":"0.3.0","challenge_hmac":"' + $proof + '"}'
    $response = "HTTP/1.1 200 OK`r`nContent-Type: application/json`r`nContent-Length: $([System.Text.Encoding]::UTF8.GetByteCount($body))`r`nConnection: close`r`n`r`n$body"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($response)
    $stream.Write($bytes, 0, $bytes.Length)
    $stream.Flush()
    $reader.Dispose()
    $stream.Dispose()
    $client.Dispose()
}
finally {
    $listener.Stop()
}
'@
    [System.IO.File]::WriteAllText(
        $serverPath,
        $serverSource,
        [System.Text.UTF8Encoding]::new($false)
    )

    $oldToken = $env:TREEQ_TEST_TOKEN
    $oldTamper = $env:TREEQ_TEST_TAMPER
    $oldReady = $env:TREEQ_TEST_READY_FILE
    try {
        $env:TREEQ_TEST_TOKEN = $Token
        $env:TREEQ_TEST_TAMPER = if ($Tamper) { 'true' } else { 'false' }
        $env:TREEQ_TEST_READY_FILE = $readyPath
        $process = Start-TestProcess -StartProcessArguments @{
            FilePath = $PowerShellPath
            ArgumentList = @(
                '-NoProfile',
                '-ExecutionPolicy', 'Bypass',
                '-File', ('"{0}"' -f $serverPath),
                '-Port', $port
            )
            RedirectStandardOutput = $stdoutPath
            RedirectStandardError = $stderrPath
            PassThru = $true
        }
    }
    finally {
        if ($null -eq $oldToken) { Remove-Item Env:TREEQ_TEST_TOKEN -ErrorAction SilentlyContinue }
        else { $env:TREEQ_TEST_TOKEN = $oldToken }
        if ($null -eq $oldTamper) { Remove-Item Env:TREEQ_TEST_TAMPER -ErrorAction SilentlyContinue }
        else { $env:TREEQ_TEST_TAMPER = $oldTamper }
        if ($null -eq $oldReady) { Remove-Item Env:TREEQ_TEST_READY_FILE -ErrorAction SilentlyContinue }
        else { $env:TREEQ_TEST_READY_FILE = $oldReady }
    }

    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    while (-not (Test-Path -LiteralPath $readyPath) -and [DateTime]::UtcNow -lt $deadline) {
        if ($process.HasExited) { break }
        Start-Sleep -Milliseconds 50
    }
    if (-not (Test-Path -LiteralPath $readyPath)) {
        $detail = if (Test-Path -LiteralPath $stderrPath) {
            [System.IO.File]::ReadAllText($stderrPath).Trim()
        }
        else {
            'no stderr'
        }
        throw "Readiness test server did not start: $detail"
    }

    return [pscustomobject]@{
        Process = $process
        Endpoint = "http://127.0.0.1:$port"
    }
}

$modulePath = Join-Path $PSScriptRoot '..\DemoLauncher.psm1'
try {
    Import-Module $modulePath -Force -ErrorAction Stop
}
catch {
    Write-Output "FAIL module import: $($_.Exception.Message)"
    Write-Output "TESTS FAILED: 1 failed, 0 passed"
    exit 1
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$powerShellPath = (Get-Process -Id $PID).Path
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) (
    'treeq-demo-tests-{0}' -f [Guid]::NewGuid().ToString('N')
)
[void](New-Item -ItemType Directory -Path $tempRoot)

try {
    $token = New-TreeQDemoToken
    Assert-True ($token -match '^[0-9a-f]{64}$') 'token is 256-bit lowercase hex'
    Assert-True ((New-TreeQDemoToken) -ne $token) 'token generation is not constant'

    $url = Get-TreeQTunnelUrl 'INF Visit https://green-tree.trycloudflare.com now'
    Assert-Equal $url 'https://green-tree.trycloudflare.com' 'parse exact tunnel URL'
    Assert-Null (
        Get-TreeQTunnelUrl 'https://evil.trycloudflare.com.attacker.test'
    ) 'reject tunnel suffix attack'
    Assert-Null (
        Get-TreeQTunnelUrl 'https://green-tree.trycloudflare.com@attacker.test'
    ) 'reject tunnel user-info attack'

    $redacted = Protect-TreeQLog -Text "token=$token" -Secrets @($token)
    Assert-True (-not $redacted.Contains($token)) 'redact token'
    Assert-True ($redacted.Contains('[REDACTED]')) 'redaction is explicit'

    $manifestPath = Join-Path $repoRoot 'apps\web\public\demo\manifest.json'
    Assert-Equal (
        Get-TreeQSha256 -Path $manifestPath -Root $repoRoot
    ) '68d865aff59d07552221a9c5f42c9ec6242066269ce7eeb926fcb8152e7adc64' `
        'hash public frozen manifest bytes'
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    foreach ($artifactName in @('input', 'result', 'segmented')) {
        $artifact = $manifest.artifacts.$artifactName
        $artifactPath = Join-Path (
            Join-Path $repoRoot 'apps\web\public'
        ) $artifact.path.TrimStart('/')
        Assert-Equal (
            Get-TreeQSha256 -Path $artifactPath -Root $repoRoot
        ) $artifact.sha256 "hash frozen $artifactName artifact bytes"
    }
    Assert-Throws {
        Get-TreeQSha256 -Path $manifestPath -Root (Join-Path $tempRoot 'other')
    } 'reject hash path outside allowed root'

    $standalone = Get-TreeQStandaloneServer -RepoRoot $repoRoot
    $expectedStandalone = Join-Path $repoRoot 'apps\web\.next\standalone\apps\web\server.js'
    Assert-Equal $standalone $expectedStandalone 'resolve monorepo standalone server'
    Assert-Null (
        Get-TreeQStandaloneServer -RepoRoot (Join-Path $tempRoot 'missing-root')
    ) 'missing standalone returns null'

    $handoff = New-TreeQHandoffUrl `
        -BaseUrl 'https://treeqcarbon.vercel.app' `
        -ApiEndpoint 'https://green-tree.trycloudflare.com' `
        -Token $token
    $handoffUri = [Uri]$handoff
    Assert-Equal $handoffUri.Query '' 'handoff has no query'
    Assert-True ($handoffUri.AbsolutePath -eq '/demo') 'handoff uses demo path'
    Assert-True ($handoffUri.Fragment.Contains($token)) 'handoff token is fragment-only'
    Assert-True (
        -not $handoff.Substring(0, $handoff.IndexOf('#')).Contains($token)
    ) 'handoff token never precedes fragment'
    Assert-True (
        $handoffUri.Fragment.Contains('api=https%3A%2F%2Fgreen-tree.trycloudflare.com')
    ) 'handoff escapes API endpoint'
    $redactedHandoff = Protect-TreeQLog -Text $handoff -Secrets @($token)
    Assert-True (-not $redactedHandoff.Contains($token)) 'redact handoff URL'
    Assert-Throws {
        New-TreeQHandoffUrl `
            -BaseUrl 'https://treeqcarbon.vercel.app' `
            -ApiEndpoint 'https://green-tree.trycloudflare.com.attacker.test' `
            -Token $token
    } 'handoff rejects endpoint suffix attack'
    Assert-Throws {
        New-TreeQHandoffUrl `
            -BaseUrl 'https://treeqcarbon.vercel.app' `
            -ApiEndpoint 'https://green-tree.trycloudflare.com?token=bad' `
            -Token $token
    } 'handoff rejects API query'
    Assert-Throws {
        New-TreeQHandoffUrl `
            -BaseUrl 'https://attacker.test' `
            -ApiEndpoint 'https://green-tree.trycloudflare.com' `
            -Token $token
    } 'handoff rejects unknown web origin'
    Assert-Throws {
        New-TreeQHandoffUrl `
            -BaseUrl 'http://127.0.0.1:3000' `
            -ApiEndpoint 'http://127.0.0.1:8000' `
            -Token $token.ToUpperInvariant()
    } 'handoff rejects non-lowercase token'

    $goodServer = Start-TestReadinessServer `
        -PowerShellPath $powerShellPath `
        -Directory $tempRoot `
        -Token $token `
        -Tamper $false
    try {
        $readiness = Test-TreeQReadiness `
            -Endpoint $goodServer.Endpoint `
            -Token $token `
            -TimeoutSec 5
        Assert-True $readiness.Ready 'authenticated readiness verifies HMAC'
        Assert-Equal $readiness.PipelineVersion '0.3.0' 'readiness returns pipeline version'
    }
    finally {
        if (-not $goodServer.Process.HasExited) { $goodServer.Process.Kill() }
        [void]$goodServer.Process.WaitForExit(5000)
    }

    $badServer = Start-TestReadinessServer `
        -PowerShellPath $powerShellPath `
        -Directory $tempRoot `
        -Token $token `
        -Tamper $true
    try {
        $readiness = Test-TreeQReadiness `
            -Endpoint $badServer.Endpoint `
            -Token $token `
            -TimeoutSec 5
        Assert-True (-not $readiness.Ready) 'authenticated readiness rejects bad HMAC'
    }
    finally {
        if (-not $badServer.Process.HasExited) { $badServer.Process.Kill() }
        [void]$badServer.Process.WaitForExit(5000)
    }

    $self = Get-Process -Id $PID
    $selfEntry = New-TestProcessEntry -Process $self -Role 'test-self'
    Assert-True (
        Test-TreeQOwnedProcess -Entry ([pscustomobject]$selfEntry)
    ) 'owned process matches executable and start time'
    $wrongStart = [ordered]@{} + $selfEntry
    $wrongStart.start_time_utc = [DateTime]::UtcNow.AddDays(-1).ToString('o')
    Assert-True (
        -not (Test-TreeQOwnedProcess -Entry ([pscustomobject]$wrongStart))
    ) 'stale process start time is rejected'
    $wrongPath = [ordered]@{} + $selfEntry
    $wrongPath.executable_path = Join-Path $tempRoot 'foreign.exe'
    Assert-True (
        -not (Test-TreeQOwnedProcess -Entry ([pscustomobject]$wrongPath))
    ) 'foreign executable path is rejected'

    $ownedChild = Start-TestProcess -StartProcessArguments @{
        FilePath = $powerShellPath
        ArgumentList = @('-NoProfile', '-Command', 'Start-Sleep -Seconds 60')
        PassThru = $true
    }
    Start-Sleep -Milliseconds 200
    $registryPath = Join-Path $tempRoot 'processes.json'
    $ownedEntry = New-TestProcessEntry -Process $ownedChild -Role 'owned-child'
    Write-TestRegistry -Path $registryPath -Entries @(
        [pscustomobject]$wrongStart,
        [pscustomobject]$ownedEntry
    )
    $stopped = @(
        Stop-TreeQOwnedProcesses -RegistryPath $registryPath -AllowedRoot $tempRoot
    )
    $ownedChild.Refresh()
    Assert-True $ownedChild.HasExited 'owned lifecycle stops recorded child'
    Assert-True ($stopped -contains $ownedChild.Id) 'owned lifecycle reports stopped PID'
    Assert-True (-not $self.HasExited) 'foreign registry entry is not stopped'

    $malformedChild = Start-TestProcess -StartProcessArguments @{
        FilePath = $powerShellPath
        ArgumentList = @('-NoProfile', '-Command', 'Start-Sleep -Seconds 60')
        PassThru = $true
    }
    Start-Sleep -Milliseconds 200
    [System.IO.File]::WriteAllText($registryPath, '{"schema_version":1,"processes":')
    Assert-Throws {
        Stop-TreeQOwnedProcesses -RegistryPath $registryPath -AllowedRoot $tempRoot
    } 'malformed registry fails closed'
    $malformedChild.Refresh()
    Assert-True (-not $malformedChild.HasExited) 'malformed registry cannot stop a process'
    if (-not $malformedChild.HasExited) {
        $malformedChild.Kill()
        [void]$malformedChild.WaitForExit(5000)
    }

    $destination = Join-Path $tempRoot 'desktop-wrapper'
    [void](New-Item -ItemType Directory -Path $destination)
    [System.IO.File]::WriteAllText(
        (Join-Path $destination 'cloudflared.exe'),
        'test fixture only'
    )
    $legacyPath = Join-Path $destination 'start_backend.bat'
    [System.IO.File]::WriteAllText($legacyPath, 'legacy sentinel')
    $installerPath = Join-Path $repoRoot 'scripts\demo\install-desktop-wrapper.ps1'
    $installerOutput = & $powerShellPath `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File $installerPath `
        -DestinationDirectory $destination 2>&1 | Out-String
    Assert-Equal $LASTEXITCODE 0 'desktop wrapper installer exits zero'
    Assert-Equal (
        [System.IO.File]::ReadAllText($legacyPath)
    ) 'legacy sentinel' 'installer leaves legacy scripts unchanged'
    $wrapperPath = Join-Path $destination 'TreeQ-Demo-Start.bat'
    Assert-True (Test-Path -LiteralPath $wrapperPath -PathType Leaf) `
        'installer creates desktop wrapper'

    $wrapperOutput = & $wrapperPath `
        -Mode Frozen `
        -NoBrowser `
        -ExitAfterReady 2>&1 | Out-String
    $wrapperExit = $LASTEXITCODE
    Assert-Equal $wrapperExit 0 'installed wrapper executes canonical launcher'
    Assert-True (
        $wrapperOutput.Contains('Mode: FROZEN - NOT A LIVE RUN')
    ) 'frozen wrapper reports truthful mode'
    Assert-True (
        $wrapperOutput.Contains('Cleanup complete')
    ) 'ExitAfterReady enters cleanup'
    $pidMatch = [regex]::Match($wrapperOutput, 'Started web process PID ([0-9]+)')
    Assert-True $pidMatch.Success 'launcher reports owned web process identity'
    if ($pidMatch.Success) {
        $launchedPid = [int]$pidMatch.Groups[1].Value
        Assert-True (
            $null -eq (Get-Process -Id $launchedPid -ErrorAction SilentlyContinue)
        ) 'ExitAfterReady stops owned web process'
    }

    $missingDestination = Join-Path $tempRoot 'missing-cloudflared'
    [void](New-Item -ItemType Directory -Path $missingDestination)
    $missingOutput = & $powerShellPath `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File $installerPath `
        -DestinationDirectory $missingDestination 2>&1 | Out-String
    Assert-True ($LASTEXITCODE -ne 0) 'installer fails without cloudflared'
    Assert-True (
        -not (Test-Path -LiteralPath (
            Join-Path $missingDestination 'TreeQ-Demo-Start.bat'
        ))
    ) 'failed installer does not create wrapper'
}
catch {
    $script:Failed++
    Write-Output "FAIL unexpected harness error: $($_.Exception.Message)"
}
finally {
    if (
        (Test-Path -LiteralPath $tempRoot) -and
        $tempRoot.StartsWith(
            [System.IO.Path]::GetTempPath(),
            [System.StringComparison]::OrdinalIgnoreCase
        )
    ) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

if ($script:Failed -gt 0) {
    Write-Output ("TESTS FAILED: {0} failed, {1} passed" -f $script:Failed, $script:Passed)
    exit 1
}

Write-Output ("TESTS PASSED: {0} passed" -f $script:Passed)
exit 0
