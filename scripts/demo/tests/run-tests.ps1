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

function Write-TestFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text
    )

    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent)) {
        [void](New-Item -ItemType Directory -Path $parent -Force)
    }
    [System.IO.File]::WriteAllText(
        $Path,
        $Text,
        [System.Text.UTF8Encoding]::new($false)
    )
}

function Get-TestSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)

    $stream = [System.IO.File]::OpenRead($Path)
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

function New-TestBuildFixture {
    param([Parameter(Mandatory = $true)][string]$Root)

    $repo = Join-Path $Root 'fixture repo with spaces'
    $web = Join-Path $repo 'apps\web'
    $build = Join-Path $web '.next'
    $standalone = Join-Path $build 'standalone\apps\web'
    $standaloneBuild = Join-Path $standalone '.next'
    $buildId = 'fixture-build-id'
    $manifests = [ordered]@{
        'BUILD_ID' = $buildId
        'build-manifest.json' = '{"rootMainFiles":["static/chunks/root.js"],"pages":{}}'
        'app-build-manifest.json' = '{"pages":{"/demo":["static/chunks/demo.js"]}}'
        'app-path-routes-manifest.json' = '{"/demo/page":"/demo"}'
        'routes-manifest.json' = '{"version":3,"staticRoutes":[{"page":"/demo"}]}'
        'prerender-manifest.json' = '{"version":4,"routes":{"/demo":{"initialRevalidateSeconds":false}}}'
        'react-loadable-manifest.json' = '{}'
        'required-server-files.json' = '{"version":1,"files":[".next\\routes-manifest.json",".next\\server\\app-paths-manifest.json",".next\\build-manifest.json",".next\\prerender-manifest.json",".next\\app-path-routes-manifest.json",".next\\app-build-manifest.json",".next\\BUILD_ID"]}'
        'server\app-paths-manifest.json' = '{"/demo/page":"app/demo/page.js"}'
    }
    foreach ($relative in $manifests.Keys) {
        Write-TestFile -Path (Join-Path $build $relative) -Text $manifests[$relative]
        Write-TestFile -Path (Join-Path $standaloneBuild $relative) -Text $manifests[$relative]
    }

    $page = '<!doctype html><html><body>fixture-build-id<script src="/_next/static/chunks/demo.js"></script></body></html>'
    $routeFiles = [ordered]@{
        'server\app\demo.html' = $page
        'server\app\demo.rsc' = 'fixture-rsc'
        'server\app\demo.meta' = '{}'
        'server\app\demo\page.js' = 'module.exports = {}'
        'server\app\demo\page.js.nft.json' = '{"version":1,"files":[]}'
        'server\app\demo\page_client-reference-manifest.js' = 'globalThis.__fixture=true'
    }
    foreach ($relative in $routeFiles.Keys) {
        Write-TestFile -Path (Join-Path $build $relative) -Text $routeFiles[$relative]
        Write-TestFile -Path (Join-Path $standaloneBuild $relative) -Text $routeFiles[$relative]
    }
    Write-TestFile -Path (Join-Path $build 'static\chunks\root.js') -Text 'root-chunk'
    Write-TestFile -Path (Join-Path $build 'static\chunks\demo.js') -Text 'demo-chunk'
    Write-TestFile `
        -Path (Join-Path $build "static\$buildId\_buildManifest.js") `
        -Text 'build-manifest'
    Write-TestFile `
        -Path (Join-Path $build "static\$buildId\_ssgManifest.js") `
        -Text 'ssg-manifest'

    $publicDemo = Join-Path $web 'public\demo'
    Write-TestFile -Path (Join-Path $publicDemo 'input.ply') -Text 'input-bytes'
    Write-TestFile -Path (Join-Path $publicDemo 'result.json') -Text '{"ok":true}'
    Write-TestFile -Path (Join-Path $publicDemo 'segmented.ply') -Text 'segmented-bytes'
    $artifacts = New-Object System.Collections.ArrayList
    foreach ($name in @('input', 'result', 'segmented')) {
        $extension = if ($name -eq 'result') { '.json' } else { '.ply' }
        $filePath = Join-Path $publicDemo "$name$extension"
        [void]$artifacts.Add([pscustomobject]@{
            Name = $name
            UrlPath = "/demo/$name$extension"
            FilePath = $filePath
            Sha256 = Get-TestSha256 $filePath
            Size = (Get-Item -LiteralPath $filePath).Length
        })
    }
    $manifestData = [ordered]@{
        schema_version = 1
        artifacts = [ordered]@{}
    }
    foreach ($artifact in $artifacts) {
        $manifestData.artifacts[$artifact.Name] = [ordered]@{
            path = $artifact.UrlPath
            sha256 = $artifact.Sha256
            size_bytes = $artifact.Size
        }
    }
    $manifestPath = Join-Path $publicDemo 'manifest.json'
    Write-TestFile `
        -Path $manifestPath `
        -Text ($manifestData | ConvertTo-Json -Depth 6 -Compress)
    Write-TestFile -Path (Join-Path $standalone 'server.js') -Text '// fixture server'
    # `next start` serves apps/web/public in place, so the fixture needs one.
    Write-TestFile -Path (Join-Path $web 'public\demo\manifest.json') -Text '{"fixture":true}'
    Write-TestFile `
        -Path (Join-Path $standalone 'public\stale.txt') `
        -Text 'must be cleared'
    Write-TestFile `
        -Path (Join-Path $standaloneBuild 'static\stale.js') `
        -Text 'must be cleared'

    return [pscustomobject]@{
        RepoRoot = $repo
        ServerPath = Join-Path $standalone 'server.js'
        BuildRoot = $build
        StandaloneBuildRoot = $standaloneBuild
        StalePublic = Join-Path $standalone 'public\stale.txt'
        StaleStatic = Join-Path $standaloneBuild 'static\stale.js'
        Bundle = [pscustomobject]@{
            Page = [pscustomobject]@{
                UrlPath = '/demo'
                FilePath = Join-Path $build 'server\app\demo.html'
                Sha256 = Get-TestSha256 (Join-Path $build 'server\app\demo.html')
                Size = (Get-Item -LiteralPath (Join-Path $build 'server\app\demo.html')).Length
            }
            Manifest = [pscustomobject]@{
                UrlPath = '/demo/manifest.json'
                FilePath = $manifestPath
                Sha256 = Get-TestSha256 $manifestPath
                Size = (Get-Item -LiteralPath $manifestPath).Length
            }
            Artifacts = @($artifacts)
        }
    }
}

function Start-TestFrozenServer {
    param(
        [Parameter(Mandatory = $true)][string]$NodePath,
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)]$Fixture,
        [Parameter(Mandatory = $true)][ValidateSet('Good', 'Redirect', 'Tamper')][string]$Mode
    )

    $port = Get-FreeTcpPort
    $scriptPath = Join-Path $Directory 'frozen-http-server.js'
    $readyPath = Join-Path $Directory ("frozen-http-ready-{0}" -f $port)
    $serverSource = @'
const fs = require('fs');
const http = require('http');
const path = require('path');
const root = process.env.TREEQ_TEST_HTTP_ROOT;
const mode = process.env.TREEQ_TEST_HTTP_MODE;
const files = {
  '/demo': path.join(root, 'apps', 'web', '.next', 'server', 'app', 'demo.html'),
  '/else': path.join(root, 'apps', 'web', '.next', 'server', 'app', 'demo.html'),
  '/demo/manifest.json': path.join(root, 'apps', 'web', 'public', 'demo', 'manifest.json'),
  '/demo/input.ply': path.join(root, 'apps', 'web', 'public', 'demo', 'input.ply'),
  '/demo/result.json': path.join(root, 'apps', 'web', 'public', 'demo', 'result.json'),
  '/demo/segmented.ply': path.join(root, 'apps', 'web', 'public', 'demo', 'segmented.ply'),
};
const server = http.createServer((request, response) => {
  if (mode === 'Redirect' && request.url === '/demo') {
    response.writeHead(302, {Location: '/else'});
    response.end();
    return;
  }
  if (!(request.url in files)) {
    response.writeHead(404);
    response.end();
    return;
  }
  const bytes = mode === 'Tamper' && request.url === '/demo/input.ply'
    ? Buffer.from('tampered')
    : fs.readFileSync(files[request.url]);
  response.writeHead(200, {'Content-Length': bytes.length});
  response.end(bytes);
});
server.listen(Number(process.env.TREEQ_TEST_HTTP_PORT), '127.0.0.1', () => {
  fs.writeFileSync(process.env.TREEQ_TEST_HTTP_READY, 'ready');
});
'@
    Write-TestFile -Path $scriptPath -Text $serverSource
    $old = @{}
    foreach ($name in @(
        'TREEQ_TEST_HTTP_ROOT',
        'TREEQ_TEST_HTTP_MODE',
        'TREEQ_TEST_HTTP_PORT',
        'TREEQ_TEST_HTTP_READY'
    )) {
        $old[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
    }
    try {
        [Environment]::SetEnvironmentVariable('TREEQ_TEST_HTTP_ROOT', $Fixture.RepoRoot, 'Process')
        [Environment]::SetEnvironmentVariable('TREEQ_TEST_HTTP_MODE', $Mode, 'Process')
        [Environment]::SetEnvironmentVariable('TREEQ_TEST_HTTP_PORT', [string]$port, 'Process')
        [Environment]::SetEnvironmentVariable('TREEQ_TEST_HTTP_READY', $readyPath, 'Process')
        $process = Start-TestProcess -StartProcessArguments @{
            FilePath = $NodePath
            ArgumentList = @($scriptPath)
            WindowStyle = 'Hidden'
            PassThru = $true
        }
    }
    finally {
        foreach ($name in $old.Keys) {
            [Environment]::SetEnvironmentVariable($name, $old[$name], 'Process')
        }
    }
    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    while (-not (Test-Path -LiteralPath $readyPath) -and [DateTime]::UtcNow -lt $deadline) {
        if ($process.HasExited) { break }
        Start-Sleep -Milliseconds 50
    }
    if (-not (Test-Path -LiteralPath $readyPath)) {
        if (-not $process.HasExited) { $process.Kill() }
        throw 'Frozen HTTP test server did not start'
    }
    return [pscustomobject]@{
        Process = $process
        BaseUrl = "http://127.0.0.1:$port"
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

    $fixture = New-TestBuildFixture -Root $tempRoot
    try {
        $buildResult = Test-TreeQWebBuild -RepoRoot $fixture.RepoRoot
        Assert-True $buildResult.Verified 'web build verification accepts a complete build'
        Assert-Equal $buildResult.ServerRoot (Join-Path $fixture.RepoRoot 'apps\web') `
            'web build reports the apps/web server root'
        Assert-Equal $buildResult.BuildId 'fixture-build-id' 'web build reports its build identity'
    }
    catch {
        Assert-True $false 'web build verification accepts a complete build'
        Assert-True $false 'web build reports the apps/web server root'
        Assert-True $false 'web build reports its build identity'
    }
    $demoHtml = Join-Path $fixture.BuildRoot 'server\app\demo.html'
    $demoHtmlBackup = "$demoHtml.bak"
    Move-Item -LiteralPath $demoHtml -Destination $demoHtmlBackup
    Assert-Throws {
        Test-TreeQWebBuild -RepoRoot $fixture.RepoRoot
    } 'web build verification rejects a build missing the /demo output'
    Move-Item -LiteralPath $demoHtmlBackup -Destination $demoHtml
    Write-TestFile -Path (Join-Path $fixture.BuildRoot 'BUILD_ID') -Text 'not a valid id!'
    Assert-Throws {
        Test-TreeQWebBuild -RepoRoot $fixture.RepoRoot
    } 'web build verification rejects a malformed build identity'
    Write-TestFile -Path (Join-Path $fixture.BuildRoot 'BUILD_ID') -Text 'fixture-build-id'

    $nodePath = (Get-Command node.exe -CommandType Application -ErrorAction Stop).Source
    foreach ($httpCase in @(
        [pscustomobject]@{ Mode = 'Good'; Expected = $true; Name = 'frozen HTTP verifies exact page and evidence bytes' },
        [pscustomobject]@{ Mode = 'Redirect'; Expected = $false; Name = 'frozen HTTP rejects redirects' },
        [pscustomobject]@{ Mode = 'Tamper'; Expected = $false; Name = 'frozen HTTP rejects artifact byte mismatch' }
    )) {
        $httpServer = Start-TestFrozenServer `
            -NodePath $nodePath `
            -Directory $tempRoot `
            -Fixture $fixture `
            -Mode $httpCase.Mode
        try {
            try {
                $verified = Test-TreeQFrozenHttpBundle `
                    -BaseUrl $httpServer.BaseUrl `
                    -Bundle $fixture.Bundle `
                    -TimeoutMs 3000
                Assert-Equal $verified $httpCase.Expected $httpCase.Name
            }
            catch {
                Assert-True $false $httpCase.Name
            }
        }
        finally {
            if (-not $httpServer.Process.HasExited) { $httpServer.Process.Kill() }
            [void]$httpServer.Process.WaitForExit(5000)
        }
    }

    $managedRoot = Join-Path $tempRoot 'managed process path with spaces'
    [void](New-Item -ItemType Directory -Path $managedRoot)
    $argumentOutput = Join-Path $managedRoot 'arguments.json'
    $childScript = Join-Path $managedRoot 'child script with spaces.ps1'
    $childSource = @'
[System.IO.File]::WriteAllText(
    $env:TREEQ_TEST_ARGUMENT_OUTPUT,
    (ConvertTo-Json -InputObject ([object[]]$args) -Compress),
    [System.Text.UTF8Encoding]::new($false)
)
[Console]::Out.WriteLine("stdout=" + $env:TREEQ_TEST_CHILD_SECRET)
[Console]::Error.WriteLine("stderr=" + $env:TREEQ_TEST_CHILD_SECRET)
'@
    Write-TestFile -Path $childScript -Text $childSource
    $managedRegistry = Join-Path $managedRoot 'processes.json'
    $managedOut = Join-Path $managedRoot 'child.stdout.log'
    $managedErr = Join-Path $managedRoot 'child.stderr.log'
    $managedList = New-Object System.Collections.ArrayList
    $oldArgumentOutput = $env:TREEQ_TEST_ARGUMENT_OUTPUT
    $oldChildSecret = $env:TREEQ_TEST_CHILD_SECRET
    try {
        $env:TREEQ_TEST_ARGUMENT_OUTPUT = $argumentOutput
        $env:TREEQ_TEST_CHILD_SECRET = $token
        try {
            $managed = Start-TreeQManagedProcess `
                -FilePath $powerShellPath `
                -ArgumentList @(
                    '-NoProfile',
                    '-ExecutionPolicy', 'Bypass',
                    '-File', $childScript,
                    'alpha beta',
                    '',
                    'tail\',
                    'quote"value'
                ) `
                -WorkingDirectory $managedRoot `
                -StandardOutputPath $managedOut `
                -StandardErrorPath $managedErr `
                -Secrets @($token) `
                -OwnedProcesses $managedList `
                -RegistryPath $managedRegistry `
                -AllowedRoot $managedRoot `
                -Role 'argument-test'
            [void]$managed.Process.WaitForExit(10000)
            Complete-TreeQManagedProcessLogs -ManagedProcess $managed
            $parsedArguments = (
                [System.IO.File]::ReadAllText($argumentOutput) | ConvertFrom-Json
            )
            $receivedArguments = @()
            foreach ($argument in $parsedArguments) {
                $receivedArguments += [string]$argument
            }
            Assert-Equal ($receivedArguments -join '|') `
                'alpha beta||tail\|quote"value' `
                'managed process preserves argument boundaries under spaces'
            $capturedLogs = (
                [System.IO.File]::ReadAllText($managedOut) +
                [System.IO.File]::ReadAllText($managedErr)
            )
            Assert-True (-not $capturedLogs.Contains($token)) `
                'managed child logs redact inherited secret'
            Assert-True $capturedLogs.Contains('[REDACTED]') `
                'managed child log redaction is explicit'
        }
        catch {
            Assert-True $false 'managed process preserves argument boundaries under spaces'
            Assert-True $false 'managed child logs redact inherited secret'
            Assert-True $false 'managed child log redaction is explicit'
        }
    }
    finally {
        if ($null -eq $oldArgumentOutput) { Remove-Item Env:TREEQ_TEST_ARGUMENT_OUTPUT -ErrorAction SilentlyContinue }
        else { $env:TREEQ_TEST_ARGUMENT_OUTPUT = $oldArgumentOutput }
        if ($null -eq $oldChildSecret) { Remove-Item Env:TREEQ_TEST_CHILD_SECRET -ErrorAction SilentlyContinue }
        else { $env:TREEQ_TEST_CHILD_SECRET = $oldChildSecret }
    }

    $directoryRegistry = Join-Path $managedRoot 'directory-processes.json'
    [void](New-Item -ItemType Directory -Path $directoryRegistry)
    if ($null -ne (Get-Command Assert-TreeQProcessRegistryPath -ErrorAction SilentlyContinue)) {
        Assert-Throws {
            Assert-TreeQProcessRegistryPath `
                -RegistryPath $directoryRegistry `
                -AllowedRoot $managedRoot
        } 'directory process registry is rejected before launch'
    }
    else {
        Assert-True $false 'directory process registry is rejected before launch'
    }

    $failureOwned = New-Object System.Collections.ArrayList
    $failureCaught = $false
    $failedChildPid = 0
    try {
        Start-TreeQManagedProcess `
            -FilePath $powerShellPath `
            -ArgumentList @('-NoProfile', '-Command', 'Start-Sleep -Seconds 60') `
            -WorkingDirectory $managedRoot `
            -StandardOutputPath (Join-Path $managedRoot 'failure.stdout.log') `
            -StandardErrorPath (Join-Path $managedRoot 'failure.stderr.log') `
            -Secrets @() `
            -OwnedProcesses $failureOwned `
            -RegistryPath $directoryRegistry `
            -AllowedRoot $managedRoot `
            -Role 'registration-failure' |
            Out-Null
    }
    catch {
        $failureCaught = $true
        if ($_.Exception.Data.Contains('TreeQProcessId')) {
            $failedChildPid = [int]$_.Exception.Data['TreeQProcessId']
        }
    }
    Assert-True $failureCaught 'registration persistence failure is surfaced'
    Assert-True ($failedChildPid -gt 0) 'registration failure reports created child identity'
    if ($failedChildPid -gt 0) {
        Assert-Null (
            Get-Process -Id $failedChildPid -ErrorAction SilentlyContinue
        ) 'registration failure synchronously stops created child'
    }
    else {
        Assert-True $false 'registration failure synchronously stops created child'
    }
    Assert-Equal $failureOwned.Count 0 'registration failure removes in-memory ownership entry'

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

    $webEntry = Get-TreeQWebServerEntry -RepoRoot $repoRoot
    $expectedEntry = Join-Path $repoRoot 'apps\web\demo-server.cjs'
    Assert-Equal $webEntry $expectedEntry 'resolve the next start entry point'
    Assert-Null (
        Get-TreeQWebServerEntry -RepoRoot (Join-Path $tempRoot 'missing-root')
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
