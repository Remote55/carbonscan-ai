# TreeQ judge demo launcher

`TreeQ-Demo-Start.bat` is the canonical one-click entry point. Legacy Desktop
scripts are not a source of truth and are never changed or deleted by this
launcher.

## Modes

- `Auto` starts the local web and authenticated API, then attempts a Cloudflare
  quick tunnel. It uses public live mode only after the public endpoint returns
  the correct challenge HMAC. Otherwise it falls back to Local or Frozen.
- `Local` starts only the local web and authenticated API. It never starts a
  tunnel.
- `Frozen` starts only the standalone web. It never starts Python, the API, or
  cloudflared, and prints `NOT A LIVE RUN`.

All modes verify the tracked public manifest and every frozen artifact hash
before starting a process. They also reject a mixed standalone build by
checking `BUILD_ID`, server manifests, the `/demo` route, and referenced static
files. The runtime copy of `public` and `.next/static` is cleared, copied, then
verified against the source file set, sizes, and SHA-256 hashes. Local and
production Frozen readiness fetch `/demo`, its manifest, and all three evidence
artifacts without redirects and require byte-for-byte matches. The launcher
never runs a build, Vercel command, or deployment.

```powershell
scripts\demo\TreeQ-Demo-Start.bat
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo\start-treeq-demo.ps1 -Mode Frozen
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo\start-treeq-demo.ps1 -Mode Local
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo\start-treeq-demo.ps1 -Mode Auto -CloudflaredPath C:\tools\cloudflared.exe
```

Use `-NoBrowser -ExitAfterReady` for automated checks. `-ExitAfterReady` still
enters `finally` and stops only processes recorded by this invocation.

## Runtime resolution and repair

The launcher resolves Node from `TREEQ_NODE` and then `PATH`. It resolves API
and ML Python independently from `TREEQ_API_PYTHON` / `TREEQ_ML_PYTHON`, each
repository `.venv`, and then `python.exe` on `PATH`. Every Python candidate must
import code from this checkout before it is accepted.

If a copied `.venv` reports that its base Python 3.11 path no longer exists,
replace that environment deliberately with an installed Python 3.11:

```powershell
cd services\api
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
cd ..\ml
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

Alternatively point to compatible interpreters without changing the checkout:

```powershell
$env:TREEQ_API_PYTHON = 'C:\path\to\api-python.exe'
$env:TREEQ_ML_PYTHON = 'C:\path\to\ml-python.exe'
$env:TREEQ_CLOUDFLARED = 'C:\path\to\cloudflared.exe'
```

The launcher does not silently borrow service code from another checkout.

## Desktop wrapper and ownership

Install a small wrapper into a directory that already contains
`cloudflared.exe`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo\install-desktop-wrapper.ps1 -DestinationDirectory C:\path\to\demo-folder
```

The wrapper sets `TREEQ_CLOUDFLARED` and calls the canonical repository batch
file. It leaves every legacy file untouched.

Owned process identities are stored in `temp/demo-runtime/processes.json`.
Cleanup rechecks both executable path and process start time; a stale PID,
foreign port occupant, or unrelated process is never killed. The 64-character
lowercase demo token is inherited by the API only, removed from the launcher
environment immediately, handed to the web in the URL fragment (never query),
and redacted while child stdout and stderr are drained into log files. Child
arguments are launched directly with Windows command-line quoting, preserving
empty values, spaces, quotes, and trailing backslashes. The registry must be a
regular file; if persistence fails after launch, the new child is synchronously
stopped and removed from the in-memory ownership list.
