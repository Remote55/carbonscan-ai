Set-StrictMode -Version Latest

if ($null -eq ('TreeQProcessCapture' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

public sealed class TreeQProcessCapture
{
    private readonly string[] secrets;
    private readonly StreamWriter stdoutWriter;
    private readonly StreamWriter stderrWriter;
    private readonly StringBuilder stdout = new StringBuilder();
    private readonly StringBuilder stderr = new StringBuilder();
    private readonly object stdoutGate = new object();
    private readonly object stderrGate = new object();
    private Task stdoutTask;
    private Task stderrTask;
    private bool completed;

    public TreeQProcessCapture(string stdoutPath, string stderrPath, string[] secrets)
    {
        this.secrets = secrets ?? new string[0];
        stdoutWriter = NewWriter(stdoutPath);
        stderrWriter = NewWriter(stderrPath);
    }

    private static StreamWriter NewWriter(string path)
    {
        FileStream stream = new FileStream(
            path,
            FileMode.Create,
            FileAccess.Write,
            FileShare.Read
        );
        return new StreamWriter(stream, new UTF8Encoding(false));
    }

    public void Start(Process process)
    {
        stdoutTask = StartDrain(process.StandardOutput, stdoutWriter, stdout, stdoutGate);
        stderrTask = StartDrain(process.StandardError, stderrWriter, stderr, stderrGate);
    }

    private Task StartDrain(
        StreamReader reader,
        StreamWriter writer,
        StringBuilder buffer,
        object gate
    )
    {
        return Task.Factory.StartNew(
            () => Drain(reader, writer, buffer, gate),
            CancellationToken.None,
            TaskCreationOptions.LongRunning,
            TaskScheduler.Default
        );
    }

    private void Drain(
        StreamReader reader,
        StreamWriter writer,
        StringBuilder buffer,
        object gate
    )
    {
        string line;
        while ((line = reader.ReadLine()) != null)
        {
            string safe = Redact(line);
            lock (gate)
            {
                buffer.AppendLine(safe);
                writer.WriteLine(safe);
                writer.Flush();
            }
        }
    }

    private string Redact(string text)
    {
        string safe = text;
        foreach (string secret in secrets)
        {
            if (!String.IsNullOrEmpty(secret))
            {
                safe = safe.Replace(secret, "[REDACTED]");
            }
        }
        return safe;
    }

    public string Snapshot()
    {
        string first;
        string second;
        lock (stdoutGate) { first = stdout.ToString(); }
        lock (stderrGate) { second = stderr.ToString(); }
        return first + second;
    }

    public void Complete(int timeoutMilliseconds)
    {
        if (completed) { return; }
        Task[] tasks = new Task[] { stdoutTask, stderrTask };
        if (!Task.WaitAll(tasks, timeoutMilliseconds))
        {
            throw new TimeoutException("Child output pipes did not drain");
        }
        stdoutWriter.Dispose();
        stderrWriter.Dispose();
        completed = true;
    }
}
'@
}

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

function Get-TreeQWebServerEntry {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$RepoRoot)

    if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) {
        return $null
    }
    # The launcher never builds. Refuse to resolve a server entry unless a
    # completed production build is already present.
    $buildId = Join-Path $RepoRoot 'apps\web\.next\BUILD_ID'
    if (-not (Test-Path -LiteralPath $buildId -PathType Leaf)) {
        return $null
    }
    # A reviewed in-repo entry point, not node_modules: pnpm materialises
    # node_modules through junctions and this launcher refuses to execute
    # anything reached through a reparse point.
    $candidates = @(
        (Join-Path $RepoRoot 'apps\web\demo-server.cjs')
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

function ConvertTo-TreeQWindowsArgument {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Argument)

    $builder = New-Object System.Text.StringBuilder
    [void]$builder.Append('"')
    $backslashes = 0
    foreach ($character in $Argument.ToCharArray()) {
        if ($character -eq '\') {
            $backslashes++
            continue
        }
        if ($character -eq '"') {
            [void]$builder.Append(('\' * (($backslashes * 2) + 1)))
            [void]$builder.Append('"')
            $backslashes = 0
            continue
        }
        if ($backslashes -gt 0) {
            [void]$builder.Append(('\' * $backslashes))
            $backslashes = 0
        }
        [void]$builder.Append($character)
    }
    if ($backslashes -gt 0) {
        [void]$builder.Append(('\' * ($backslashes * 2)))
    }
    [void]$builder.Append('"')
    return $builder.ToString()
}

function ConvertTo-TreeQWindowsCommandLine {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [AllowEmptyString()]
        [string[]]$ArgumentList
    )

    return (@(
        $ArgumentList | ForEach-Object { ConvertTo-TreeQWindowsArgument -Argument $_ }
    ) -join ' ')
}

function Assert-TreeQProcessRegistryPath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$RegistryPath,
        [Parameter(Mandatory = $true)][string]$AllowedRoot
    )

    $rootItem = Get-Item -LiteralPath $AllowedRoot -Force -ErrorAction Stop
    if (
        -not $rootItem.PSIsContainer -or
        ($rootItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
    ) {
        throw 'Process registry root is unsafe'
    }
    $rootFull = [System.IO.Path]::GetFullPath($rootItem.FullName).TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    )
    $registryFull = [System.IO.Path]::GetFullPath($RegistryPath)
    if (-not $registryFull.StartsWith(
        $rootFull + [System.IO.Path]::DirectorySeparatorChar,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw 'Process registry is outside the allowed root'
    }

    $parent = Get-Item -LiteralPath (Split-Path -Parent $registryFull) -Force -ErrorAction Stop
    while ($null -ne $parent) {
        if (($parent.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'Process registry ancestors cannot be reparse points'
        }
        if ($parent.FullName.Equals(
            $rootFull,
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            break
        }
        $parent = $parent.Parent
    }
    if (Test-Path -LiteralPath $registryFull) {
        $item = Get-Item -LiteralPath $registryFull -Force
        if (
            $item.PSIsContainer -or
            ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
        ) {
            throw 'Process registry must be a regular file'
        }
    }
    return $registryFull
}

function Write-TreeQManagedRegistry {
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [System.Collections.ArrayList]$OwnedProcesses,
        [Parameter(Mandatory = $true)][string]$RegistryPath,
        [Parameter(Mandatory = $true)][string]$AllowedRoot
    )

    $safeRegistry = Assert-TreeQProcessRegistryPath `
        -RegistryPath $RegistryPath `
        -AllowedRoot $AllowedRoot
    $entries = @(
        $OwnedProcesses |
            Where-Object { $null -ne $_.Entry } |
            ForEach-Object { $_.Entry }
    )
    $payload = [ordered]@{
        schema_version = 1
        processes = $entries
    } | ConvertTo-Json -Depth 5
    $temporaryPath = Join-Path $AllowedRoot (
        'processes.{0}.tmp' -f [Guid]::NewGuid().ToString('N')
    )
    try {
        $stream = New-Object System.IO.FileStream(
            $temporaryPath,
            [System.IO.FileMode]::CreateNew,
            [System.IO.FileAccess]::Write,
            [System.IO.FileShare]::None
        )
        $writer = New-Object System.IO.StreamWriter(
            $stream,
            [System.Text.UTF8Encoding]::new($false)
        )
        try {
            $writer.Write($payload)
            $writer.Flush()
            $stream.Flush()
        }
        finally {
            $writer.Dispose()
            $stream.Dispose()
        }
        if (Test-Path -LiteralPath $safeRegistry) {
            # [NullString]::Value, not $null: PowerShell converts $null to an
            # empty string when binding to a String parameter, and File.Replace
            # rejects "" as a backup path with "The path is not of a legal
            # form." That made every registry write after the first one throw,
            # so the launcher could never start a second process.
            [System.IO.File]::Replace($temporaryPath, $safeRegistry, [NullString]::Value)
        }
        else {
            [System.IO.File]::Move($temporaryPath, $safeRegistry)
        }
    }
    finally {
        if (Test-Path -LiteralPath $temporaryPath -PathType Leaf) {
            Remove-Item -LiteralPath $temporaryPath -Force
        }
    }
}

function Complete-TreeQManagedProcessLogs {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)]$ManagedProcess)

    if (-not $ManagedProcess.LogsCompleted) {
        $ManagedProcess.Capture.Complete(10000)
        $ManagedProcess.LogsCompleted = $true
    }
}

function Get-TreeQManagedProcessLogText {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)]$ManagedProcess)

    return $ManagedProcess.Capture.Snapshot()
}

function Start-TreeQManagedProcess {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [AllowEmptyString()]
        [string[]]$ArgumentList,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string]$StandardOutputPath,
        [Parameter(Mandatory = $true)][string]$StandardErrorPath,
        [Parameter(Mandatory = $false)]
        [AllowEmptyCollection()]
        [string[]]$Secrets = @(),
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [System.Collections.ArrayList]$OwnedProcesses,
        [Parameter(Mandatory = $true)][string]$RegistryPath,
        [Parameter(Mandatory = $true)][string]$AllowedRoot,
        [Parameter(Mandatory = $true)][string]$Role
    )

    $process = $null
    $managed = $null
    $createdPid = 0
    try {
        $startInfo = New-Object System.Diagnostics.ProcessStartInfo
        $startInfo.FileName = [System.IO.Path]::GetFullPath($FilePath)
        $startInfo.Arguments = ConvertTo-TreeQWindowsCommandLine -ArgumentList $ArgumentList
        $startInfo.WorkingDirectory = [System.IO.Path]::GetFullPath($WorkingDirectory)
        $startInfo.UseShellExecute = $false
        $startInfo.CreateNoWindow = $true
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $startInfo
        if (-not $process.Start()) {
            throw 'Child process did not start'
        }
        $createdPid = $process.Id
        $managed = [pscustomobject]@{
            Process = $process
            Entry = $null
            Capture = $null
            LogsCompleted = $false
        }
        [void]$OwnedProcesses.Add($managed)

        $capture = New-Object TreeQProcessCapture(
            [System.IO.Path]::GetFullPath($StandardOutputPath),
            [System.IO.Path]::GetFullPath($StandardErrorPath),
            @($Secrets)
        )
        $managed.Capture = $capture
        $capture.Start($process)
        $process.Refresh()
        $managed.Entry = [pscustomobject][ordered]@{
            pid = $process.Id
            executable_path = $process.Path
            start_time_utc = $process.StartTime.ToUniversalTime().ToString('o')
            role = $Role
        }
        Write-TreeQManagedRegistry `
            -OwnedProcesses $OwnedProcesses `
            -RegistryPath $RegistryPath `
            -AllowedRoot $AllowedRoot
        return $managed
    }
    catch {
        $failure = $_.Exception
        if ($createdPid -gt 0) {
            $failure.Data['TreeQProcessId'] = $createdPid
        }
        if ($null -ne $process) {
            try {
                if (-not $process.HasExited) {
                    $process.Kill()
                }
                [void]$process.WaitForExit(5000)
            }
            catch {
            }
        }
        if ($null -ne $managed -and $null -ne $managed.Capture) {
            try { Complete-TreeQManagedProcessLogs -ManagedProcess $managed } catch { }
        }
        if ($null -ne $managed) {
            [void]$OwnedProcesses.Remove($managed)
        }
        throw $failure
    }
}

function Stop-TreeQManagedProcesses {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [System.Collections.ArrayList]$OwnedProcesses
    )

    $stopped = New-Object System.Collections.ArrayList
    foreach ($managed in @($OwnedProcesses)) {
        try {
            if (
                $null -ne $managed.Entry -and
                -not $managed.Process.HasExited -and
                (Test-TreeQOwnedProcess -Entry $managed.Entry)
            ) {
                $managed.Process.Kill()
                [void]$managed.Process.WaitForExit(5000)
                [void]$stopped.Add([int]$managed.Entry.pid)
            }
            elseif (-not $managed.Process.HasExited) {
                [void]$managed.Process.WaitForExit(5000)
            }
            Complete-TreeQManagedProcessLogs -ManagedProcess $managed
        }
        finally {
            [void]$OwnedProcesses.Remove($managed)
        }
    }
    return @($stopped)
}

function Get-TreeQDirectoryIdentity {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Root
    )

    $identity = @{}
    foreach ($item in Get-ChildItem -LiteralPath $Path -Recurse -Force) {
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'Asset trees cannot contain reparse points'
        }
        if (-not $item.PSIsContainer) {
            $relative = $item.FullName.Substring($Path.Length).TrimStart('\', '/')
            $identity[$relative] = [pscustomobject]@{
                Size = $item.Length
                Sha256 = Get-TreeQSha256 -Path $item.FullName -Root $Root
            }
        }
    }
    return $identity
}

function Assert-TreeQDirectoryIdentity {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Expected,
        [Parameter(Mandatory = $true)][hashtable]$Actual
    )

    if ($Expected.Count -ne $Actual.Count) {
        throw 'Copied asset file set differs from source'
    }
    foreach ($relative in $Expected.Keys) {
        if (
            -not $Actual.ContainsKey($relative) -or
            $Actual[$relative].Size -ne $Expected[$relative].Size -or
            $Actual[$relative].Sha256 -cne $Expected[$relative].Sha256
        ) {
            throw 'Copied asset bytes differ from source'
        }
    }
}

function Remove-TreeQContainedDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Root
    )

    if (-not (Test-Path -LiteralPath $Path)) { return }
    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
    $pathFull = [System.IO.Path]::GetFullPath($Path)
    if (-not $pathFull.StartsWith(
        $rootFull + [System.IO.Path]::DirectorySeparatorChar,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw 'Runtime-copy destination escapes the standalone root'
    }
    $item = Get-Item -LiteralPath $pathFull -Force
    if (
        -not $item.PSIsContainer -or
        ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
    ) {
        throw 'Runtime-copy destination is unsafe'
    }
    foreach ($child in Get-ChildItem -LiteralPath $pathFull -Recurse -Force) {
        if (($child.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'Runtime-copy destination contains a reparse point'
        }
    }
    Remove-Item -LiteralPath $pathFull -Recurse -Force
}

function Copy-TreeQExactDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    [void](New-Item -ItemType Directory -Path $Destination)
    foreach ($item in Get-ChildItem -LiteralPath $Source -Force) {
        Copy-Item -LiteralPath $item.FullName -Destination $Destination -Recurse -Force | Out-Null
    }
}

function Test-TreeQWebBuild {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot
    )

    $webRoot = Join-Path $RepoRoot 'apps\web'
    $buildRoot = Join-Path $webRoot '.next'
    $requiredFiles = @(
        'BUILD_ID',
        'build-manifest.json',
        'app-build-manifest.json',
        'app-path-routes-manifest.json',
        'routes-manifest.json',
        'prerender-manifest.json',
        'react-loadable-manifest.json',
        'required-server-files.json',
        'server\app-paths-manifest.json'
    )
    foreach ($relative in $requiredFiles) {
        [void](Get-TreeQContainedFile -Path (Join-Path $buildRoot $relative) -Root $buildRoot)
    }
    $buildId = [System.IO.File]::ReadAllText(
        (Join-Path $buildRoot 'BUILD_ID')
    ).Trim()
    if ($buildId -cnotmatch '^[A-Za-z0-9_-]{1,128}$') {
        throw 'BUILD_ID is invalid'
    }
    $appPaths = [System.IO.File]::ReadAllText(
        (Join-Path $buildRoot 'server\app-paths-manifest.json')
    ) | ConvertFrom-Json
    $routePath = [string]$appPaths.'/demo/page'
    if ([string]::IsNullOrWhiteSpace($routePath)) {
        throw 'Web build does not contain the /demo route'
    }
    $routeFiles = @(
        (Join-Path 'server' $routePath),
        'server\app\demo\page.js.nft.json',
        'server\app\demo\page_client-reference-manifest.js',
        'server\app\demo.html',
        'server\app\demo.rsc',
        'server\app\demo.meta'
    )
    foreach ($relative in $routeFiles) {
        [void](Get-TreeQContainedFile -Path (Join-Path $buildRoot $relative) -Root $buildRoot)
    }
    $required = [System.IO.File]::ReadAllText(
        (Join-Path $buildRoot 'required-server-files.json')
    ) | ConvertFrom-Json
    foreach ($requiredPath in @($required.files)) {
        if (-not ([string]$requiredPath).StartsWith('.next\')) { continue }
        $relative = ([string]$requiredPath).Substring(6)
        [void](Get-TreeQContainedFile -Path (Join-Path $buildRoot $relative) -Root $buildRoot)
    }

    $referenceText = [System.IO.File]::ReadAllText(
        (Join-Path $buildRoot 'build-manifest.json')
    ) + [System.IO.File]::ReadAllText(
        (Join-Path $buildRoot 'app-build-manifest.json')
    ) + [System.IO.File]::ReadAllText(
        (Join-Path $buildRoot 'server\app\demo.html')
    )
    $staticReferences = New-Object System.Collections.ArrayList
    foreach ($match in [regex]::Matches(
        $referenceText,
        '(?:/_next/)?static/[A-Za-z0-9_./-]+'
    )) {
        $relative = $match.Value
        if ($relative.StartsWith('/_next/')) { $relative = $relative.Substring(7) }
        $relative = $relative.Replace('/', '\')
        if (-not $relative.EndsWith('\')) {
            [void]$staticReferences.Add($relative)
        }
    }
    [void]$staticReferences.Add("static\$buildId\_buildManifest.js")
    [void]$staticReferences.Add("static\$buildId\_ssgManifest.js")
    foreach ($relative in @($staticReferences | Select-Object -Unique)) {
        [void](Get-TreeQContainedFile -Path (Join-Path $buildRoot $relative) -Root $buildRoot)
    }

    # `next start` serves apps/web/public and .next/static in place, so there is
    # no duplicated tree to reconcile. Read both so a truncated or unreadable
    # asset tree still fails preflight rather than at the first judge click.
    $sourcePublic = Join-Path $webRoot 'public'
    $sourceStatic = Join-Path $buildRoot 'static'
    [void](Get-TreeQDirectoryIdentity -Path $sourcePublic -Root $sourcePublic)
    [void](Get-TreeQDirectoryIdentity -Path $sourceStatic -Root $sourceStatic)
    return [pscustomobject]@{
        Verified = $true
        ServerRoot = $webRoot
        BuildId = $buildId
        PagePath = Join-Path $buildRoot 'server\app\demo.html'
    }
}

function Get-TreeQExactHttpBytes {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][int]$TimeoutMs
    )

    $requestUri = [Uri]$Url
    $request = [System.Net.HttpWebRequest]::Create($requestUri)
    $request.Timeout = $TimeoutMs
    $request.ReadWriteTimeout = $TimeoutMs
    $request.AllowAutoRedirect = $false
    $request.Proxy = $null
    $response = $request.GetResponse()
    try {
        if (
            [int]$response.StatusCode -ne 200 -or
            $response.ResponseUri.AbsoluteUri -cne $requestUri.AbsoluteUri
        ) {
            throw 'Frozen response origin, path, or status is invalid'
        }
        $memory = New-Object System.IO.MemoryStream
        try {
            $response.GetResponseStream().CopyTo($memory)
            return ,$memory.ToArray()
        }
        finally {
            $memory.Dispose()
        }
    }
    finally {
        $response.Dispose()
    }
}

function Test-TreeQFrozenHttpBundle {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$BaseUrl,
        [Parameter(Mandatory = $true)]$Bundle,
        [Parameter(Mandatory = $false)][ValidateRange(100, 30000)][int]$TimeoutMs = 5000
    )

    try {
        $baseUri = [Uri]$BaseUrl
        if (
            -not $baseUri.IsAbsoluteUri -or
            $baseUri.UserInfo -or
            $baseUri.Query -or
            $baseUri.Fragment -or
            $baseUri.AbsolutePath -ne '/'
        ) {
            return $false
        }
        $isLocal = (
            $baseUri.Scheme -eq 'http' -and
            ($baseUri.DnsSafeHost -eq '127.0.0.1' -or $baseUri.DnsSafeHost -eq 'localhost')
        )
        $isProduction = (
            $baseUri.Scheme -eq 'https' -and
            $baseUri.IsDefaultPort -and
            $baseUri.DnsSafeHost -eq 'treeqcarbon.vercel.app'
        )
        if (-not ($isLocal -or $isProduction)) { return $false }
        foreach ($expected in @($Bundle.Page, $Bundle.Manifest) + @($Bundle.Artifacts)) {
            $url = ([Uri]::new($baseUri, [string]$expected.UrlPath)).AbsoluteUri
            $bytes = Get-TreeQExactHttpBytes -Url $url -TimeoutMs $TimeoutMs
            $sourceBytes = [System.IO.File]::ReadAllBytes([string]$expected.FilePath)
            if (
                $bytes.Length -ne [long]$expected.Size -or
                -not [System.Collections.StructuralComparisons]::StructuralEqualityComparer.Equals(
                    $bytes,
                    $sourceBytes
                )
            ) {
                return $false
            }
            $sha = [System.Security.Cryptography.SHA256]::Create()
            try { $actualHash = $sha.ComputeHash($bytes) }
            finally { $sha.Dispose() }
            $actualHex = ([BitConverter]::ToString($actualHash)).Replace('-', '').ToLowerInvariant()
            if ($actualHex -cne [string]$expected.Sha256) { return $false }
        }
        return $true
    }
    catch {
        return $false
    }
}

Export-ModuleMember -Function @(
    'New-TreeQDemoToken',
    'Get-TreeQTunnelUrl',
    'Protect-TreeQLog',
    'Get-TreeQSha256',
    'Get-TreeQWebServerEntry',
    'New-TreeQHandoffUrl',
    'Test-TreeQOwnedProcess',
    'Stop-TreeQOwnedProcesses',
    'Test-TreeQReadiness',
    'ConvertTo-TreeQWindowsCommandLine',
    'Assert-TreeQProcessRegistryPath',
    'Start-TreeQManagedProcess',
    'Complete-TreeQManagedProcessLogs',
    'Get-TreeQManagedProcessLogText',
    'Stop-TreeQManagedProcesses',
    'Test-TreeQWebBuild',
    'Test-TreeQFrozenHttpBundle'
)
