[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [ValidateSet('Auto', 'Local', 'Frozen')]
    [string]$Mode = 'Auto',

    [Parameter(Mandatory = $false)]
    [string]$CloudflaredPath = '',

    [Parameter(Mandatory = $false)]
    [switch]$NoBrowser,

    [Parameter(Mandatory = $false)]
    [switch]$ExitAfterReady
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$modulePath = Join-Path $PSScriptRoot 'DemoLauncher.psm1'
Import-Module $modulePath -Force -ErrorAction Stop

$script:RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$script:RuntimeRoot = Join-Path $script:RepoRoot 'temp\demo-runtime'
$script:RegistryPath = Join-Path $script:RuntimeRoot 'processes.json'
$script:ManagedProcesses = New-Object System.Collections.ArrayList
$script:LogSecrets = New-Object System.Collections.ArrayList
$script:ExitCode = 0

function Write-TreeQMessage {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text)

    [Console]::Out.WriteLine(
        (Protect-TreeQLog -Text $Text -Secrets @($script:LogSecrets))
    )
}

function Test-TreeQPathContained {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Root
    )

    $pathFull = [System.IO.Path]::GetFullPath($Path)
    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    )
    return $pathFull.StartsWith(
        $rootFull + [System.IO.Path]::DirectorySeparatorChar,
        [System.StringComparison]::OrdinalIgnoreCase
    )
}

function Assert-TreeQDirectorySafe {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Root
    )

    if (-not (Test-TreeQPathContained -Path $Path -Root $Root)) {
        throw "Runtime directory is outside the repository"
    }
    if (Test-Path -LiteralPath $Path) {
        $item = Get-Item -LiteralPath $Path -Force
        if (
            -not $item.PSIsContainer -or
            ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
        ) {
            throw "Runtime directory is not a regular contained directory"
        }
    }
    else {
        [void](New-Item -ItemType Directory -Path $Path)
    }
}

function Initialize-TreeQRuntime {
    $tempRoot = Join-Path $script:RepoRoot 'temp'
    Assert-TreeQDirectorySafe -Path $tempRoot -Root $script:RepoRoot
    Assert-TreeQDirectorySafe -Path $script:RuntimeRoot -Root $script:RepoRoot
}

function Repair-TreeQDuplicatePathEnvironment {
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
}

function Test-TreeQFrozenBundle {
    $publicRoot = Join-Path $script:RepoRoot 'apps\web\public'
    $manifestPath = Join-Path $publicRoot 'demo\manifest.json'
    $docsManifestPath = Join-Path $script:RepoRoot 'docs\evidence\judge_demo_manifest.json'
    $identityPath = Join-Path (
        $script:RepoRoot
    ) 'apps\web\src\generated\judge-demo-evidence.ts'

    $identity = [System.IO.File]::ReadAllText($identityPath)
    $identityMatch = [regex]::Match(
        $identity,
        "manifestSha256:\s*'([0-9a-f]{64})'"
    )
    if (-not $identityMatch.Success) {
        throw "Frozen manifest identity is invalid"
    }
    $expectedManifestHash = $identityMatch.Groups[1].Value
    $actualManifestHash = Get-TreeQSha256 -Path $manifestPath -Root $script:RepoRoot
    if ($actualManifestHash -cne $expectedManifestHash) {
        throw "Frozen manifest hash mismatch"
    }
    if (
        (Get-TreeQSha256 -Path $docsManifestPath -Root $script:RepoRoot) -cne
        $actualManifestHash
    ) {
        throw "Public and documentation manifests differ"
    }

    try {
        $manifest = [System.IO.File]::ReadAllText(
            $manifestPath,
            [System.Text.UTF8Encoding]::new($false, $true)
        ) | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        throw "Frozen manifest is not strict UTF-8 JSON"
    }
    if ($manifest.schema_version -ne 1) {
        throw "Frozen manifest schema is unsupported"
    }
    $expectedPaths = [ordered]@{
        input = '/demo/input.ply'
        result = '/demo/result.json'
        segmented = '/demo/segmented.ply'
    }
    $verifiedArtifacts = New-Object System.Collections.ArrayList
    foreach ($name in $expectedPaths.Keys) {
        $artifact = $manifest.artifacts.$name
        if (
            [string]$artifact.path -cne $expectedPaths[$name] -or
            [string]$artifact.sha256 -cnotmatch '^[0-9a-f]{64}$' -or
            [long]$artifact.size_bytes -le 0
        ) {
            throw "Frozen $name artifact identity is invalid"
        }
        $artifactPath = Join-Path $publicRoot ([string]$artifact.path).TrimStart('/')
        if (-not (Test-TreeQPathContained -Path $artifactPath -Root $publicRoot)) {
            throw "Frozen artifact path escapes the public directory"
        }
        $artifactItem = Get-Item -LiteralPath $artifactPath -Force -ErrorAction Stop
        if (
            $artifactItem.PSIsContainer -or
            ($artifactItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
            $artifactItem.Length -ne [long]$artifact.size_bytes -or
            (Get-TreeQSha256 -Path $artifactPath -Root $publicRoot) -cne
                [string]$artifact.sha256
        ) {
            throw "Frozen $name artifact verification failed"
        }
        [void]$verifiedArtifacts.Add([pscustomobject]@{
            Name = $name
            UrlPath = [string]$artifact.path
            FilePath = $artifactPath
            Sha256 = [string]$artifact.sha256
            Size = [long]$artifact.size_bytes
        })
    }
    $pagePath = Join-Path $script:RepoRoot 'apps\web\.next\server\app\demo.html'
    $pageItem = Get-Item -LiteralPath $pagePath -Force -ErrorAction Stop
    if (
        $pageItem.PSIsContainer -or
        ($pageItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
    ) {
        throw 'Tracked Frozen page is not a regular build file'
    }
    return [pscustomobject]@{
        ManifestHash = $actualManifestHash
        ManifestPath = $manifestPath
        Page = [pscustomobject]@{
            UrlPath = '/demo'
            FilePath = $pagePath
            Sha256 = Get-TreeQSha256 -Path $pagePath -Root $script:RepoRoot
            Size = $pageItem.Length
        }
        Manifest = [pscustomobject]@{
            UrlPath = '/demo/manifest.json'
            FilePath = $manifestPath
            Sha256 = $actualManifestHash
            Size = (Get-Item -LiteralPath $manifestPath).Length
        }
        Artifacts = @($verifiedArtifacts)
    }
}

function Resolve-TreeQNode {
    $configured = [Environment]::GetEnvironmentVariable(
        'TREEQ_NODE',
        [EnvironmentVariableTarget]::Process
    )
    $candidates = New-Object System.Collections.ArrayList
    if (-not [string]::IsNullOrWhiteSpace($configured)) {
        [void]$candidates.Add($configured)
    }
    $command = Get-Command node.exe -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -ne $command) {
        [void]$candidates.Add($command.Source)
    }
    foreach ($candidate in @($candidates | Select-Object -Unique)) {
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            continue
        }
        try {
            $version = & $candidate '--version' 2>&1
            if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace(
                [string]($version | Select-Object -First 1)
            )) {
                return [System.IO.Path]::GetFullPath($candidate)
            }
        }
        catch {
        }
    }
    return $null
}

function Get-TreeQPythonCandidates {
    param(
        [Parameter(Mandatory = $true)][string]$EnvironmentName,
        [Parameter(Mandatory = $true)][string]$RepositoryVenvPath
    )

    $candidates = New-Object System.Collections.ArrayList
    $configured = [Environment]::GetEnvironmentVariable(
        $EnvironmentName,
        [EnvironmentVariableTarget]::Process
    )
    if (-not [string]::IsNullOrWhiteSpace($configured)) {
        [void]$candidates.Add([pscustomobject]@{
            Path = $configured
            Source = $EnvironmentName
        })
        return @($candidates)
    }
    if (Test-Path -LiteralPath $RepositoryVenvPath -PathType Leaf) {
        [void]$candidates.Add([pscustomobject]@{
            Path = $RepositoryVenvPath
            Source = 'repository venv'
        })
    }
    $command = Get-Command python.exe -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -ne $command) {
        [void]$candidates.Add([pscustomobject]@{
            Path = $command.Source
            Source = 'PATH'
        })
    }
    return @($candidates)
}

function Resolve-TreeQPython {
    param(
        [Parameter(Mandatory = $true)][ValidateSet('API', 'ML')][string]$Role
    )

    if ($Role -eq 'API') {
        $environmentName = 'TREEQ_API_PYTHON'
        $workingDirectory = Join-Path $script:RepoRoot 'services\api'
        $venvPath = Join-Path $workingDirectory '.venv\Scripts\python.exe'
        # No quotes in the probe: PowerShell rewrites quoting when it builds a
        # native command line, so `print("treeq-api-ok")` reached Python as
        # `print(treeq-api-ok)` and every API probe died with a NameError. The
        # ML probe only worked because it happens to need no string literal.
        $probe = 'from app.main import app; print(app.version)'
    }
    else {
        $environmentName = 'TREEQ_ML_PYTHON'
        $workingDirectory = Join-Path $script:RepoRoot 'services\ml'
        $venvPath = Join-Path $workingDirectory '.venv\Scripts\python.exe'
        $probe = 'from pipeline.main import PIPELINE_VERSION; print(PIPELINE_VERSION)'
    }

    $candidates = @(
        Get-TreeQPythonCandidates `
            -EnvironmentName $environmentName `
            -RepositoryVenvPath $venvPath
    )
    foreach ($candidate in $candidates) {
        $path = [string]$candidate.Path
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            Write-TreeQMessage "$Role Python candidate missing ($($candidate.Source)): $path"
            continue
        }
        Push-Location $workingDirectory
        try {
            $probeOutput = & $path '-c' $probe 2>&1
            $probeExit = $LASTEXITCODE
        }
        catch {
            $probeOutput = @($_.Exception.Message)
            $probeExit = 1
        }
        finally {
            Pop-Location
        }
        if ($probeExit -eq 0) {
            Write-TreeQMessage "$Role Python ready from $($candidate.Source)."
            return [System.IO.Path]::GetFullPath($path)
        }
        # A captured traceback arrives as one multi-line record, so taking the
        # last element reported "Traceback (most recent call last):" and hid the
        # exception itself. Split first, then take the last meaningful line.
        $detail = [string](
            ($probeOutput | ForEach-Object { $_.ToString() -split "`r?`n" }) |
                Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
                Select-Object -Last 1
        )
        if ([string]::IsNullOrWhiteSpace($detail)) {
            $detail = "exit $probeExit"
        }
        Write-TreeQMessage "$Role Python failed ($($candidate.Source)): $detail"
    }
    Write-TreeQMessage (
        "$Role Python unavailable. Recreate services/$($Role.ToLower())/.venv " +
        "with Python 3.11 and install the service, or set $environmentName to a " +
        "compatible python.exe. The launcher will not use another checkout's code."
    )
    return $null
}

function Start-TreeQWeb {
    param(
        [Parameter(Mandatory = $true)][string]$NodePath,
        [Parameter(Mandatory = $true)][string]$ServerPath,
        [Parameter(Mandatory = $true)][string]$ServerRoot
    )

    $oldPort = [Environment]::GetEnvironmentVariable('PORT', 'Process')
    $oldHostname = [Environment]::GetEnvironmentVariable('HOSTNAME', 'Process')
    try {
        [Environment]::SetEnvironmentVariable('PORT', '3000', 'Process')
        [Environment]::SetEnvironmentVariable('HOSTNAME', '127.0.0.1', 'Process')
        $managed = Start-TreeQManagedProcess `
            -FilePath $NodePath `
            -ArgumentList @($ServerPath) `
            -WorkingDirectory $ServerRoot `
            -StandardOutputPath (Join-Path $script:RuntimeRoot 'web.stdout.log') `
            -StandardErrorPath (Join-Path $script:RuntimeRoot 'web.stderr.log') `
            -Secrets @($script:LogSecrets) `
            -OwnedProcesses $script:ManagedProcesses `
            -RegistryPath $script:RegistryPath `
            -AllowedRoot $script:RuntimeRoot `
            -Role 'web'
    }
    finally {
        [Environment]::SetEnvironmentVariable('PORT', $oldPort, 'Process')
        [Environment]::SetEnvironmentVariable('HOSTNAME', $oldHostname, 'Process')
    }
    Write-TreeQMessage "Started web process PID $($managed.Process.Id)"
    return $managed
}

function Test-TreeQWebReady {
    param(
        [Parameter(Mandatory = $true)]$Web,
        [Parameter(Mandatory = $true)]$Bundle,
        [Parameter(Mandatory = $false)][int]$TimeoutSec = 30
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSec)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (-not (Test-TreeQOwnedProcess -Entry $Web.Entry)) {
            return $false
        }
        if (Test-TreeQFrozenHttpBundle `
            -BaseUrl 'http://127.0.0.1:3000' `
            -Bundle $Bundle `
            -TimeoutMs 3000) {
            return $true
        }
        Start-Sleep -Milliseconds 250
    }
    return $false
}

function Start-TreeQApi {
    param(
        [Parameter(Mandatory = $true)][string]$ApiPython,
        [Parameter(Mandatory = $true)][string]$MlPython,
        [Parameter(Mandatory = $true)][string]$Token
    )

    $names = @(
        'TREEQ_DEMO_MODE',
        'TREEQ_DEMO_TOKEN',
        'ML_DIR',
        'ML_PYTHON',
        'APP_DEBUG',
        'PYTHONIOENCODING'
    )
    $oldValues = @{}
    foreach ($name in $names) {
        $oldValues[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
    }
    try {
        [Environment]::SetEnvironmentVariable('TREEQ_DEMO_MODE', 'true', 'Process')
        [Environment]::SetEnvironmentVariable('TREEQ_DEMO_TOKEN', $Token, 'Process')
        [Environment]::SetEnvironmentVariable(
            'ML_DIR',
            (Join-Path $script:RepoRoot 'services\ml'),
            'Process'
        )
        [Environment]::SetEnvironmentVariable('ML_PYTHON', $MlPython, 'Process')
        [Environment]::SetEnvironmentVariable('APP_DEBUG', 'false', 'Process')
        [Environment]::SetEnvironmentVariable('PYTHONIOENCODING', 'utf-8', 'Process')
        $managed = Start-TreeQManagedProcess `
            -FilePath $ApiPython `
            -ArgumentList @(
                '-m', 'uvicorn', 'app.main:app',
                '--host', '127.0.0.1',
                '--port', '8000'
            ) `
            -WorkingDirectory (Join-Path $script:RepoRoot 'services\api') `
            -StandardOutputPath (Join-Path $script:RuntimeRoot 'api.stdout.log') `
            -StandardErrorPath (Join-Path $script:RuntimeRoot 'api.stderr.log') `
            -Secrets @($Token) `
            -OwnedProcesses $script:ManagedProcesses `
            -RegistryPath $script:RegistryPath `
            -AllowedRoot $script:RuntimeRoot `
            -Role 'api'
    }
    finally {
        [Environment]::SetEnvironmentVariable('TREEQ_DEMO_TOKEN', $null, 'Process')
        foreach ($name in $names | Where-Object { $_ -ne 'TREEQ_DEMO_TOKEN' }) {
            [Environment]::SetEnvironmentVariable($name, $oldValues[$name], 'Process')
        }
    }
    Write-TreeQMessage "Started API process PID $($managed.Process.Id)"
    return $managed
}

function Wait-TreeQReadiness {
    param(
        [Parameter(Mandatory = $true)]$Api,
        [Parameter(Mandatory = $true)][string]$Endpoint,
        [Parameter(Mandatory = $true)][string]$Token,
        [Parameter(Mandatory = $false)][int]$TimeoutSec = 40
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSec)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (-not (Test-TreeQOwnedProcess -Entry $Api.Entry)) {
            return [pscustomobject]@{
                Ready = $false
                PipelineVersion = $null
                Detail = 'process exited'
            }
        }
        $readiness = Test-TreeQReadiness `
            -Endpoint $Endpoint `
            -Token $Token `
            -TimeoutSec 5
        if ($readiness.Ready) {
            return $readiness
        }
        Start-Sleep -Milliseconds 500
    }
    return [pscustomobject]@{
        Ready = $false
        PipelineVersion = $null
        Detail = 'readiness timeout'
    }
}

function Resolve-TreeQCloudflared {
    param([Parameter(Mandatory = $false)][string]$RequestedPath)

    if (-not [string]::IsNullOrWhiteSpace($RequestedPath)) {
        if (Test-Path -LiteralPath $RequestedPath -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($RequestedPath)
        }
        Write-TreeQMessage "Cloudflared path does not exist: $RequestedPath"
        return $null
    }
    $configured = [Environment]::GetEnvironmentVariable(
        'TREEQ_CLOUDFLARED',
        [EnvironmentVariableTarget]::Process
    )
    if (-not [string]::IsNullOrWhiteSpace($configured)) {
        if (Test-Path -LiteralPath $configured -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($configured)
        }
        Write-TreeQMessage "TREEQ_CLOUDFLARED does not identify a file."
        return $null
    }
    $command = Get-Command cloudflared.exe -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -ne $command) {
        return $command.Source
    }
    Write-TreeQMessage (
        'Cloudflared unavailable. Pass -CloudflaredPath, set TREEQ_CLOUDFLARED, ' +
        'or add cloudflared.exe to PATH.'
    )
    return $null
}

function Start-TreeQTunnel {
    param([Parameter(Mandatory = $true)][string]$ExecutablePath)

    $managed = Start-TreeQManagedProcess `
        -FilePath $ExecutablePath `
        -ArgumentList @(
            'tunnel',
            '--url', 'http://127.0.0.1:8000',
            '--no-autoupdate'
        ) `
        -WorkingDirectory $script:RepoRoot `
        -StandardOutputPath (Join-Path $script:RuntimeRoot 'tunnel.stdout.log') `
        -StandardErrorPath (Join-Path $script:RuntimeRoot 'tunnel.stderr.log') `
        -Secrets @($script:LogSecrets) `
        -OwnedProcesses $script:ManagedProcesses `
        -RegistryPath $script:RegistryPath `
        -AllowedRoot $script:RuntimeRoot `
        -Role 'tunnel'
    Write-TreeQMessage "Started tunnel process PID $($managed.Process.Id)"
    return $managed
}

function Wait-TreeQTunnelUrl {
    param(
        [Parameter(Mandatory = $true)]$Tunnel,
        [Parameter(Mandatory = $false)][int]$TimeoutSec = 30
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSec)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (-not (Test-TreeQOwnedProcess -Entry $Tunnel.Entry)) {
            return $null
        }
        $text = Get-TreeQManagedProcessLogText -ManagedProcess $Tunnel
        $url = Get-TreeQTunnelUrl -Text $text
        if ($null -ne $url) {
            return $url
        }
        Start-Sleep -Milliseconds 250
    }
    return $null
}

function Test-TreeQProductionFrozen {
    param([Parameter(Mandatory = $true)]$Bundle)

    return Test-TreeQFrozenHttpBundle `
        -BaseUrl 'https://treeqcarbon.vercel.app' `
        -Bundle $Bundle `
        -TimeoutMs 5000
}

function Open-TreeQBrowser {
    param([Parameter(Mandatory = $true)][string]$Url)

    try {
        Start-Process -FilePath $Url | Out-Null
    }
    catch {
        if ($_.Exception.Message -notmatch "Key in dictionary: 'Path'.*'PATH'") {
            throw
        }
        Repair-TreeQDuplicatePathEnvironment
        Start-Process -FilePath $Url | Out-Null
    }
}

function Stop-TreeQRegisteredProcesses {
    $stopped = New-Object System.Collections.ArrayList
    foreach ($processId in @(
        Stop-TreeQManagedProcesses -OwnedProcesses $script:ManagedProcesses
    )) {
        [void]$stopped.Add($processId)
    }
    if (Test-Path -LiteralPath $script:RegistryPath) {
        [void](Assert-TreeQProcessRegistryPath `
            -RegistryPath $script:RegistryPath `
            -AllowedRoot $script:RuntimeRoot)
        foreach ($processId in @(
            Stop-TreeQOwnedProcesses `
                -RegistryPath $script:RegistryPath `
                -AllowedRoot $script:RuntimeRoot
        )) {
            if (-not $stopped.Contains($processId)) {
                [void]$stopped.Add($processId)
            }
        }
        Remove-Item -LiteralPath $script:RegistryPath -Force
    }
    return @($stopped)
}

try {
    Write-TreeQMessage "TreeQ demo launcher preflight started."
    $bundle = Test-TreeQFrozenBundle
    Write-TreeQMessage "Frozen evidence verified: manifest and 3 artifact hashes."

    $webServerEntry = Get-TreeQWebServerEntry -RepoRoot $script:RepoRoot
    if ($null -eq $webServerEntry) {
        throw (
            'No reviewed web build was found. Run "npm run build" in apps/web before ' +
            'the demo; the launcher never builds or deploys.'
        )
    }
    $nodePath = Resolve-TreeQNode
    if ($null -eq $nodePath) {
        throw 'Node is unavailable. Set TREEQ_NODE or add node.exe to PATH.'
    }

    Initialize-TreeQRuntime
    if (Test-Path -LiteralPath $script:RegistryPath) {
        [void](Assert-TreeQProcessRegistryPath `
            -RegistryPath $script:RegistryPath `
            -AllowedRoot $script:RuntimeRoot)
        $staleStopped = @(Stop-TreeQRegisteredProcesses)
        Write-TreeQMessage (
            "Previous registry checked; stopped $($staleStopped.Count) verified owned process(es)."
        )
    }

    # Ports must be free *after* our own leftovers are stopped. Anything still
    # listening belongs to someone else, and starting anyway means the demo
    # drives a server this launcher did not configure. That is not theoretical:
    # an abandoned API with demo mode enabled kept port 8000, the operator's own
    # API could not bind, and every upload came back 401 with nothing on screen
    # explaining why.
    Assert-TreeQPortFree -Port 3000 -Role 'web server'
    if ($Mode -ne 'Frozen') {
        Assert-TreeQPortFree -Port 8000 -Role 'API'
    }

    $webBuild = Test-TreeQWebBuild -RepoRoot $script:RepoRoot
    $web = Start-TreeQWeb `
        -NodePath $nodePath `
        -ServerPath $webServerEntry `
        -ServerRoot $webBuild.ServerRoot
    $webReady = Test-TreeQWebReady `
        -Web $web `
        -Bundle $bundle
    if ($webReady) {
        Write-TreeQMessage 'Web readiness passed.'
    }
    else {
        Write-TreeQMessage 'Web readiness failed.'
    }

    $token = $null
    $apiReady = $false
    $publicReady = $false
    $pipelineVersion = $null
    $tunnelUrl = $null
    if ($Mode -ne 'Frozen') {
        $mlPython = Resolve-TreeQPython -Role ML
        $apiPython = Resolve-TreeQPython -Role API
        if ($null -ne $mlPython -and $null -ne $apiPython) {
            $token = New-TreeQDemoToken
            [void]$script:LogSecrets.Add($token)
            $api = Start-TreeQApi `
                -ApiPython $apiPython `
                -MlPython $mlPython `
                -Token $token
            $localReadiness = Wait-TreeQReadiness `
                -Api $api `
                -Endpoint 'http://127.0.0.1:8000' `
                -Token $token
            $apiReady = $localReadiness.Ready
            $pipelineVersion = $localReadiness.PipelineVersion
            if ($apiReady) {
                Write-TreeQMessage "Authenticated local readiness passed ($pipelineVersion)."
            }
            else {
                Write-TreeQMessage 'Authenticated local readiness failed; live mode is disabled.'
            }

            if ($Mode -eq 'Auto' -and $apiReady) {
                $cloudflared = Resolve-TreeQCloudflared -RequestedPath $CloudflaredPath
                if ($null -ne $cloudflared) {
                    $tunnel = Start-TreeQTunnel -ExecutablePath $cloudflared
                    $tunnelUrl = Wait-TreeQTunnelUrl -Tunnel $tunnel
                    if ($null -ne $tunnelUrl) {
                        $publicReadiness = Test-TreeQReadiness `
                            -Endpoint $tunnelUrl `
                            -Token $token `
                            -TimeoutSec 30
                        $publicReady = $publicReadiness.Ready
                    }
                    if ($publicReady) {
                        Write-TreeQMessage 'Authenticated public readiness passed.'
                    }
                    else {
                        Write-TreeQMessage (
                            'Public readiness was not proven; Auto will use a truthful fallback.'
                        )
                    }
                }
            }
        }
        else {
            Write-TreeQMessage 'Live preflight is incomplete; using Frozen fallback.'
        }
    }

    $targetUrl = $null
    if ($Mode -eq 'Auto' -and $publicReady) {
        $targetUrl = New-TreeQHandoffUrl `
            -BaseUrl 'https://treeqcarbon.vercel.app' `
            -ApiEndpoint $tunnelUrl `
            -Token $token
        Write-TreeQMessage 'Mode: AUTO PUBLIC LIVE'
        Write-TreeQMessage "Pipeline: $pipelineVersion"
    }
    elseif ($Mode -ne 'Frozen' -and $apiReady -and $webReady) {
        $targetUrl = New-TreeQHandoffUrl `
            -BaseUrl 'http://127.0.0.1:3000' `
            -ApiEndpoint 'http://127.0.0.1:8000' `
            -Token $token
        Write-TreeQMessage 'Mode: LOCAL LIVE'
        Write-TreeQMessage "Pipeline: $pipelineVersion"
    }
    else {
        if ($webReady) {
            $targetUrl = 'http://127.0.0.1:3000/demo'
        }
        elseif (Test-TreeQProductionFrozen -Bundle $bundle) {
            $targetUrl = 'https://treeqcarbon.vercel.app/demo'
        }
        else {
            throw 'No verified local or reachable production Frozen demo is available.'
        }
        Write-TreeQMessage 'Mode: FROZEN - NOT A LIVE RUN'
    }

    if ($targetUrl.Contains('#')) {
        Write-TreeQMessage "Handoff prepared: $targetUrl"
    }
    else {
        Write-TreeQMessage "Demo URL: $targetUrl"
    }
    if ($NoBrowser) {
        Write-TreeQMessage 'Browser launch skipped (-NoBrowser).'
    }
    else {
        Open-TreeQBrowser -Url $targetUrl
    }

    if (-not $ExitAfterReady) {
        [void](Read-Host 'Press Enter to stop launcher-owned processes')
    }
}
catch {
    $script:ExitCode = 1
    Write-TreeQMessage "ERROR: $($_.Exception.Message)"
}
finally {
    [Environment]::SetEnvironmentVariable(
        'TREEQ_DEMO_TOKEN',
        $null,
        [EnvironmentVariableTarget]::Process
    )
    try {
        $stopped = @(Stop-TreeQRegisteredProcesses)
        Write-TreeQMessage "Cleanup complete; stopped $($stopped.Count) owned process(es)."
    }
    catch {
        $script:ExitCode = 1
        Write-TreeQMessage "ERROR: cleanup failed: $($_.Exception.Message)"
    }
}

exit $script:ExitCode
