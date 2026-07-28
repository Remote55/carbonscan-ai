# TreeQ Judge Demo Sprint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้าง Judge Demo บน desktop เส้นทางเดียวที่เปิดได้ในคลิกเดียว รองรับ Production Live, Local Live และ hash-verified Frozen Evidence พร้อม Live Upload, diagnostics, provenance และ UX แบบ Forest Observatory ภายในเวลา 3–5 นาที

**Architecture:** FastAPI รับ ephemeral demo token เฉพาะเมื่อเปิด `TREEQ_DEMO_MODE=1` และมี authenticated readiness challenge; Next.js รับ endpoint/token ผ่าน URL fragment เพียงครั้งเดียวแล้วเลือก mode ด้วย state machine กลาง Canonical PowerShell launcher เริ่ม local API, standalone web และ Cloudflare Quick Tunnel โดยไม่ deploy ส่วน frozen bundle สร้างจาก deterministic `tlsep` fixture และตรวจ SHA-256 ก่อนแสดงผล

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, pytest, NumPy/Open3D, Next.js 14 App Router, React 18, TypeScript 5.4, Tailwind CSS, Three.js/react-three-fiber, Vitest, Playwright, Windows PowerShell 5.1 และ Cloudflare Quick Tunnel

## Global Constraints

- ตอบสนองเส้นทางแข่งขันบน desktop เท่านั้น; target viewports คือ `1440×900` และ `1366×768`
- รอบ sample-first ต้องจบภายใน 4 นาที; Live Upload ของ known-good `.ply` ต้องจบภายใน 5 นาที
- `tlsep` เป็น default; PointNet++ ต้องแสดง `Experimental` และห้าม promote ใน sprint นี้
- Species classification ขั้นที่ 7 ยังคงเป็น `Stub`
- ไม่ทำ mobile completion, marketplace, payment, certification หรือ production GPU deployment
- ไม่เปลี่ยน allometric equations/coefficient ใน `species_db.csv` และไม่ redesign dashboard ทุกหน้า
- ห้ามเรียก CO₂e estimate ว่า certified หรือ tradable carbon credit
- Landing ใช้ Tailwind และ server components; ห้าม `styled-jsx` และห้าม canvas 3D
- Judge route ต้องไม่บังคับ login และไม่เรียก Supabase/third-party analytics
- Demo token ต้องมี entropy อย่างน้อย 256 bits, อยู่ใน URL fragment เท่านั้น, เก็บใน `sessionStorage` ของ tab ปัจจุบัน และไม่ปรากฏใน query string, console, logs, UI หรือ commit
- Endpoint allowlist รับเฉพาะ `https://<one-label>.trycloudflare.com`, `http://127.0.0.1:8000` และ `http://localhost:8000`
- Judge upload รับเฉพาะ PLY ขนาดไม่เกิน 100 MB และ declared vertex count ไม่เกิน 2,000,000 จุด
- Sync API แสดงเพียงสถานะที่พิสูจน์ได้; ช่วงประมวลผลเป็น indeterminate และห้ามจำลองเปอร์เซ็นต์
- `total_trees` ต้องคงเป็น backward-compatible alias ของ `measured_trees`
- `detected_trees == measured_trees + excluded_trees` และ `len(excluded_segments) == excluded_trees`
- Frozen UI ต้องแสดง `FROZEN EVIDENCE — NOT A LIVE RUN` ก่อนหรือใกล้ตัวเลขผลรวม
- ตัวเลข mockup `20 / 18 / 2` และ `93.135 tCO₂e` ไม่ใช่ evidence และห้าม hard-code
- Python output ที่ใช้บน Windows ต้องเป็น ASCII-safe; ห้าม emoji ใน `print()`
- Launcher ห้าม deploy Vercel, เปลี่ยน branch, pull, reset, checkout หรือ kill process ที่ตนไม่ได้สร้าง
- Freeze ต้องเสร็จไม่ช้ากว่า `2026-08-04T00:00:00+07:00` ซึ่งเป็นเวลา 24 ชั่วโมงก่อนต้นวันแข่งขัน

---

## Scope and sequencing

แผนนี้เป็น vertical slice เดียว ไม่แยกเป็นหลาย subsystem plans เพราะ output ของแต่ละส่วนต้องประกอบกันจึงทดสอบ Judge Journey ได้จริง ลำดับงานรักษา P0 ก่อน P1: ปิด security/runtime boundary, สร้าง frozen bundle, เปิด judge route และ launcher ให้รอดสาม mode ก่อนเพิ่ม diagnostics และ visual polish

## File responsibility map

### API/runtime boundary

- `services/api/app/core/demo_security.py` — constant-time token check, protected-path policy, readiness HMAC และ upload rate limiter
- `services/api/app/core/config.py` — typed demo-mode limits/settings
- `services/api/app/main.py` — middleware order ที่ให้ CORS ครอบ response จาก demo guard
- `services/api/app/api/v1/health.py` — liveness เดิมและ authenticated `/health/demo-ready`
- `services/api/app/services/upload_validation.py` — bounded streaming read, PLY signature/header/vertex validation
- `services/api/app/services/pipeline_runner.py` — ML readiness, secret-stripped subprocess env และ sanitized operator detail
- `services/api/app/api/v1/upload.py` — judge upload boundary และ public error ที่ไม่เผย internals

### Frozen evidence

- `services/ml/pipeline/ply_export.py` — deterministic raw XYZ PLY writer
- `services/ml/scripts/run_judge_demo.py` — สร้าง input/result/segmented artifacts สองรอบและ fail เมื่อ hash ต่าง
- `scripts/judge_demo_manifest.py` — validate/seal/copy artifacts และ generate typed web evidence
- `docs/evidence/judge_demo_manifest.json` — reviewed source manifest
- `apps/web/public/demo/*` — committed input PLY, segmented PLY, result JSON และ public manifest
- `apps/web/src/generated/judge-demo-evidence.ts` — immutable manifest identity สำหรับ browser verification

### Web runtime and workspace

- `apps/web/src/lib/demo-runtime.ts` — fragment parsing, endpoint allowlist และ one-time handoff
- `apps/web/src/lib/demo-mode.ts` — pure three-mode reducer
- `apps/web/src/lib/demo-api.ts` — authenticated readiness และ XHR upload phases
- `apps/web/src/lib/frozen-demo.ts` — fetch + SHA-256 verification แบบ fail closed
- `apps/web/src/lib/result-view-model.ts` — map API/frozen result เป็น truthful labels/counts/reasons
- `apps/web/src/app/demo/page.tsx` — public judge route shell
- `apps/web/src/components/demo/*` — workspace, upload, summary, table, provenance, mode badge และ pipeline status
- `apps/web/src/components/viewer/point-cloud-viewer.tsx` — neutral/classification rendering และ class visibility
- `apps/web/src/app/page.tsx` กับ `apps/web/src/components/landing/*` — Forest Observatory landing
- `apps/web/src/app/layout.tsx` กับ `apps/web/src/assets/fonts/*` — self-hosted Thai fonts

### Launcher, verification and release

- `scripts/demo/DemoLauncher.psm1` — pure/testable launcher helpers
- `scripts/demo/start-treeq-demo.ps1` — orchestration และ owned-process lifecycle
- `scripts/demo/TreeQ-Demo-Start.bat` — canonical one-click entry
- `scripts/demo/tests/run-tests.ps1` — dependency-free PowerShell assertion harness
- `scripts/demo/freeze-treeq-demo.ps1` — clean-tree/build/artifact/video/release-lock gate
- `scripts/demo/verify_backup_video.py` — 1080p และ duration gate
- `apps/web/e2e/judge-demo.spec.ts` — browser journey/failure/viewport gates
- `.github/workflows/ci-demo.yml` — Windows launcher + web E2E + manifest checks
- `docs/demo/JUDGE_DEMO_RUNBOOK.md` และ `docs/demo/JUDGE_SCRIPT_TH.md` — operator and presenter source of truth

## Execution preflight

ก่อน Task 1 ให้ใช้ `superpowers:using-git-worktrees` สร้าง isolated implementation worktree และ branch `codex/judge-demo-sprint-impl` จาก commit ที่มี spec และ plan นี้ แล้วรัน baseline:

~~~powershell
git status --short
pnpm --dir apps/web exec vitest run
pnpm --dir apps/web type-check
& 'services/api/.venv/Scripts/python.exe' -m pytest services/api/tests -q
& 'services/ml/.venv/Scripts/python.exe' -m pytest services/ml/tests/test_pipeline_orchestrator.py services/ml/tests/test_core_demo.py -q --no-cov
~~~

Expected: worktree clean; ทุก command exit `0` หาก baseline ใดล้มเหลวให้หยุดและรายงานเป็น pre-existing failure ก่อนแก้ไฟล์

---

### Task 1: P0 API demo guard, readiness and bounded upload

**Files:**
- Create: `services/api/app/core/demo_security.py`
- Create: `services/api/tests/test_demo_security.py`
- Modify: `services/api/app/core/config.py`
- Modify: `services/api/app/main.py`
- Modify: `services/api/app/api/v1/health.py`
- Modify: `services/api/app/services/upload_validation.py`
- Modify: `services/api/app/services/pipeline_runner.py`
- Modify: `services/api/app/api/v1/upload.py`
- Modify: `services/api/app/api/v1/jobs.py`
- Modify: `services/api/tests/test_health.py`
- Modify: `services/api/tests/test_upload_validation.py`
- Modify: `services/api/tests/test_upload_analyze.py`
- Modify: `services/api/.env.example`

**Interfaces:**
- Consumes: `X-TreeQ-Demo-Token`, `X-TreeQ-Demo-Challenge` และ settings จาก environment
- Produces: `DemoGuardMiddleware(app)`, `compute_readiness_hmac(token: str, nonce: str) -> str`, `read_upload_limited(file: UploadFile, max_bytes: int) -> bytes`, `validate_demo_ply(data: bytes, max_points: int) -> int` และ `GET /api/v1/health/demo-ready`
- Task 2 ใช้ response `{"status":"ready","mode":"demo","pipeline_version":str,"challenge_hmac":64-hex}`

- [ ] **Step 1: เขียน failing security and upload tests**

สร้าง tests ที่ล็อก behavior จริง:

~~~python
# services/api/tests/test_demo_security.py
def test_token_comparison_is_constant_contract():
    assert token_matches("a" * 64, "a" * 64)
    assert not token_matches("a" * 64, "b" * 64)

@pytest.mark.asyncio
async def test_demo_guard_rejects_missing_token(client, monkeypatch):
    monkeypatch.setattr(settings, "TREEQ_DEMO_MODE", True)
    monkeypatch.setattr(settings, "TREEQ_DEMO_TOKEN", "a" * 64)
    response = await client.post(
        "/api/v1/upload/analyze",
        files={"file": ("tree.ply", MINIMAL_ASCII_PLY, "application/octet-stream")},
    )
    assert response.status_code == 401
    assert "a" * 64 not in response.text

@pytest.mark.asyncio
async def test_demo_ready_returns_hmac_only_after_auth(client, monkeypatch):
    token = "a" * 64
    nonce = "b" * 64
    monkeypatch.setattr(settings, "TREEQ_DEMO_MODE", True)
    monkeypatch.setattr(settings, "TREEQ_DEMO_TOKEN", token)
    response = await client.get(
        "/api/v1/health/demo-ready",
        headers={
            "X-TreeQ-Demo-Token": token,
            "X-TreeQ-Demo-Challenge": nonce,
        },
    )
    assert response.status_code == 200
    assert response.json()["challenge_hmac"] == compute_readiness_hmac(token, nonce)
~~~

เพิ่มใน `test_upload_validation.py` ให้พิสูจน์ว่า bad signature, missing `end_header`, vertex count `2_000_001` และ byte stream เกิน limit ถูกปฏิเสธก่อน pipeline

- [ ] **Step 2: รัน tests เพื่อยืนยัน RED**

~~~powershell
& 'services/api/.venv/Scripts/python.exe' -m pytest services/api/tests/test_demo_security.py services/api/tests/test_upload_validation.py services/api/tests/test_health.py -q
~~~

Expected: FAIL เพราะ module/functions/settings และ demo-ready route ยังไม่มี

- [ ] **Step 3: เพิ่ม typed settings และ middleware**

เพิ่มค่าใน `Settings`:

~~~python
TREEQ_DEMO_MODE: bool = False
TREEQ_DEMO_TOKEN: str = ""
TREEQ_DEMO_MAX_UPLOAD_SIZE_MB: int = 100
TREEQ_DEMO_MAX_POINTS: int = 2_000_000
TREEQ_DEMO_ALLOWED_ORIGINS: str = (
    "https://treeqcarbon.vercel.app,http://127.0.0.1:3000,http://localhost:3000"
)

@property
def TREEQ_DEMO_MAX_UPLOAD_SIZE_BYTES(self) -> int:
    return self.TREEQ_DEMO_MAX_UPLOAD_SIZE_MB * 1024 * 1024
~~~

`DemoGuardMiddleware` ต้อง:

1. pass-through ทันทีเมื่อ demo mode ปิด
2. ปกป้องเฉพาะ `/api/v1/upload/analyze` และ `/api/v1/health/demo-ready`
3. ใช้ `hmac.compare_digest` เทียบ token
4. limit `POST /api/v1/upload/analyze` ตาม `RATE_LIMIT_UPLOAD` ต่อ client/minute
5. คืน generic `401` หรือ `429` โดยไม่ echo header

ใน `main.py` ให้ add demo guard ก่อน add `CORSMiddleware` เพื่อให้ CORS เป็น outer middleware และเติม origin จาก `TREEQ_DEMO_ALLOWED_ORIGINS` เมื่อ demo mode เปิด

- [ ] **Step 4: ทำ readiness HMAC, bounded reader และ secret-stripped subprocess**

ใช้ interface:

~~~python
def compute_readiness_hmac(token: str, nonce: str) -> str:
    return hmac.new(bytes.fromhex(token), nonce.encode("ascii"), hashlib.sha256).hexdigest()

async def read_upload_limited(file: UploadFile, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    size = 0
    while chunk := await file.read(1024 * 1024):
        size += len(chunk)
        if size > max_bytes:
            raise HTTPException(status_code=413, detail="File too large")
        chunks.append(chunk)
    return b"".join(chunks)
~~~

`validate_demo_ply` ต้องอ่าน ASCII header เท่านั้นจนถึง `end_header`, ยืนยัน magic `ply`, format `ascii 1.0` หรือ `binary_little_endian 1.0`, หา `element vertex N` หนึ่งค่า และคืน `N`

ก่อน `subprocess.run` ใน pipeline runner ให้สร้าง `child_env = os.environ.copy()` แล้ว `pop` keys `TREEQ_DEMO_TOKEN` และ `SUPABASE_SERVICE_KEY` ออก ส่ง `env=child_env` ทุกครั้ง เพิ่ม `probe_pipeline_runtime(timeout=30) -> str` ที่ import `pipeline.main` ใน ML interpreter และคืน pipeline version

`PipelineError` ต้องแยก `public_message` จาก `operator_detail`; HTTP response คืนเพียง `"Pipeline execution failed"` ส่วน operator log redact repo/temp paths

- [ ] **Step 5: รัน API tests และ lint**

~~~powershell
& 'services/api/.venv/Scripts/python.exe' -m pytest services/api/tests/test_demo_security.py services/api/tests/test_upload_validation.py services/api/tests/test_health.py services/api/tests/test_upload_analyze.py -q
& 'services/api/.venv/Scripts/ruff.exe' check services/api/app services/api/tests
~~~

Expected: PASS; test ต้องยืนยัน subprocess env ไม่มี demo token และ error body ไม่มี path/raw stderr

- [ ] **Step 6: Commit Task 1**

~~~powershell
git add services/api/app services/api/tests services/api/.env.example
git commit -m "feat(api): secure the ephemeral judge demo"
~~~

---

### Task 2: P0 browser runtime handoff and honest mode state

**Files:**
- Create: `apps/web/src/lib/demo-runtime.ts`
- Create: `apps/web/src/lib/demo-runtime.test.ts`
- Create: `apps/web/src/lib/demo-mode.ts`
- Create: `apps/web/src/lib/demo-mode.test.ts`
- Create: `apps/web/src/lib/demo-api.ts`
- Create: `apps/web/src/lib/demo-api.test.ts`
- Modify: `apps/web/src/middleware.ts`
- Modify: `apps/web/next.config.mjs`

**Interfaces:**
- Consumes: fragment `#api=<encoded-origin>&token=<64-hex>` และ Task 1 demo-ready contract
- Produces: `RuntimeCredentials`, `consumeRuntimeHandoff(browser)`, `demoModeReducer(state,event)`, `createDemoApiClient(credentials)`
- Task 4 ใช้ `DemoModeState` และ `DemoApiClient` โดยไม่อ่าน environment API URL

- [ ] **Step 1: เขียน failing pure-function tests**

~~~typescript
it('accepts only exact demo origins', () => {
  expect(validateDemoEndpoint('https://green-tree.trycloudflare.com')).toBe(
    'https://green-tree.trycloudflare.com',
  );
  expect(validateDemoEndpoint('https://evil.trycloudflare.com.attacker.test')).toBeNull();
  expect(validateDemoEndpoint('http://127.0.0.1:8000')).toBe('http://127.0.0.1:8000');
  expect(validateDemoEndpoint('http://127.0.0.1:9000')).toBeNull();
});

it('stores a valid fragment once and scrubs history', () => {
  const browser = makeFakeBrowser(
    '#api=https%3A%2F%2Fgreen-tree.trycloudflare.com&token=' + 'a'.repeat(64),
  );
  const credentials = consumeRuntimeHandoff(browser);
  expect(credentials?.token).toBe('a'.repeat(64));
  expect(browser.history.replaceState).toHaveBeenCalledWith(null, '', '/demo');
  expect(browser.storage.getItem(RUNTIME_STORAGE_KEY)).not.toBeNull();
});
~~~

Reducer cases ต้องครอบคลุม `BOOT_WITHOUT_HANDOFF -> frozen`, readiness success ของ tunnel/local, readiness failure -> frozen พร้อม reason และห้ามเปลี่ยน frozen เป็น live หากไม่มี verified event

- [ ] **Step 2: รัน tests เพื่อยืนยัน RED**

~~~powershell
pnpm --dir apps/web exec vitest run src/lib/demo-runtime.test.ts src/lib/demo-mode.test.ts src/lib/demo-api.test.ts
~~~

Expected: FAIL เพราะ modules ยังไม่มี

- [ ] **Step 3: สร้าง runtime types, parser และ reducer**

ใช้ discriminated unions:

~~~typescript
export type RuntimeCredentials = Readonly<{ endpoint: string; token: string }>;

export type DemoModeState =
  | { kind: 'booting' }
  | { kind: 'checking'; credentials: RuntimeCredentials }
  | { kind: 'production-live'; credentials: RuntimeCredentials; pipelineVersion: string }
  | { kind: 'local-live'; credentials: RuntimeCredentials; pipelineVersion: string }
  | { kind: 'frozen'; reason: 'sample-first' | 'invalid-handoff' | 'unreachable' | 'manual' };

export type DemoModeEvent =
  | { type: 'BOOT'; credentials: RuntimeCredentials | null; invalidHandoff: boolean }
  | { type: 'READINESS_OK'; pipelineVersion: string }
  | { type: 'READINESS_FAILED' }
  | { type: 'USE_FROZEN' };

export interface DemoApiClient {
  checkReadiness(): Promise<{ pipelineVersion: string }>;
  analyze(file: File, onPhase: (phase: UploadPhase) => void): Promise<AnalyzeResponse>;
}
~~~

Parser ต้องปฏิเสธ endpoint ที่มี username/password/query/hash/path อื่นนอกจาก `/` และปฏิเสธ token ที่ไม่ใช่ 64 lowercase/uppercase hex เก็บเฉพาะ `sessionStorage`

- [ ] **Step 4: สร้าง authenticated demo API client**

`checkReadiness()` สร้าง nonce 32 bytes, ส่ง headers สองตัว, verify HMAC ด้วย Web Crypto และคืน pipeline version เฉพาะเมื่อ HMAC ตรง

`analyze(file,onPhase)` ใช้ `XMLHttpRequest` เพื่อรายงาน phase จริง:

~~~typescript
export type UploadPhase = 'uploading' | 'processing';

xhr.upload.onload = () => onPhase('processing');
xhr.open('POST', new URL('/api/v1/upload/analyze', endpoint));
xhr.setRequestHeader('X-TreeQ-Demo-Token', token);
xhr.send(formData);
~~~

ห้ามใส่ token ใน URL/error message และต้อง map non-2xx เป็น `DemoApiError(status, publicDetail)`

- [ ] **Step 5: ทำ judge-route bypass และ security headers**

ใน middleware คืน `NextResponse.next()` ก่อนสร้าง Supabase client เมื่อ pathname เป็น `/demo` หรือขึ้นต้น `/demo/`

ใน `next.config.mjs`:

- ตั้ง `output: 'standalone'`
- ลด `serverActions.bodySizeLimit` เป็น `100mb`
- เพิ่ม headers เฉพาะ `/demo/:path*`: `Referrer-Policy: no-referrer`, `Cache-Control: no-store`, `X-Robots-Tag: noindex, nofollow`

- [ ] **Step 6: รัน web tests/typecheck**

~~~powershell
pnpm --dir apps/web exec vitest run src/lib/demo-runtime.test.ts src/lib/demo-mode.test.ts src/lib/demo-api.test.ts
pnpm --dir apps/web type-check
~~~

Expected: PASS; tests ยืนยัน URL ที่ fetch/XHR ไม่มี token และ Supabase ไม่ใช่ dependency ของ demo client

- [ ] **Step 7: Commit Task 2**

~~~powershell
git add apps/web/src/lib/demo-* apps/web/src/middleware.ts apps/web/next.config.mjs
git commit -m "feat(web): add secure demo runtime handoff"
~~~

---

### Task 3: P0 deterministic judge artifacts and manifest tooling

**Files:**
- Modify: `services/ml/pipeline/ply_export.py`
- Create: `services/ml/scripts/run_judge_demo.py`
- Create: `services/ml/tests/test_judge_demo.py`
- Create: `scripts/judge_demo_manifest.py`
- Create: `scripts/tests/test_judge_demo_manifest.py`

**Interfaces:**
- Consumes: `pipeline.synthetic.generate_synthetic_plot(**DEMO_CONFIG)`, `process_point_cloud` และ `docs/evidence/core_demo_manifest.json`
- Produces: candidate directory with `input.ply`, `result.json`, `segmented.ply`, `candidate.json`; CLI `judge_demo_manifest.py seal|finalize|check`
- Task 4 consumes committed public artifacts and generated `JUDGE_DEMO_EVIDENCE`

- [ ] **Step 1: เขียน failing PLY and two-run artifact tests**

~~~python
def test_write_xyz_ply_roundtrip(tmp_path):
    points = np.array([[0.0, 1.0, 2.0], [3.0, 4.0, 5.0]])
    path = write_xyz_ply(points, tmp_path / "input.ply")
    loaded = load_point_cloud(path)
    assert np.allclose(loaded, points, atol=1e-6)
    assert b"property uchar class" not in path.read_bytes()[:256]

def test_judge_demo_is_reproducible_and_path_free(tmp_path):
    summary = run_judge_demo(tmp_path, REPO_ROOT)
    assert summary["reproducible"] is True
    assert summary["result_sha256"][0] == summary["result_sha256"][1]
    assert summary["segmented_ply_sha256"][0] == summary["segmented_ply_sha256"][1]
    result_text = (tmp_path / "result.json").read_text(encoding="utf-8")
    assert str(tmp_path) not in result_text
~~~

- [ ] **Step 2: รัน ML tests เพื่อยืนยัน RED**

~~~powershell
& 'services/ml/.venv/Scripts/python.exe' -m pytest services/ml/tests/test_ply_export.py services/ml/tests/test_judge_demo.py -q --no-cov
~~~

Expected: FAIL เพราะ `write_xyz_ply` และ judge runner ยังไม่มี

- [ ] **Step 3: เพิ่ม raw XYZ writer และ judge runner**

`write_xyz_ply` ใช้ binary little-endian packed dtype `x/y/z float32` และ deterministic header

`run_judge_demo` ต้อง:

1. generate seed-42 points แล้วเขียน `input.ply`
2. เรียก `process_point_cloud(input.ply, segmented_ply_out=...)` สองรอบด้วย `tlsep` และ `Tectona grandis`
3. แปลง `metadata.input_file` เป็น basename `input.ply` ก่อน hash
4. serialize `metadata/summary/diagnostics/trees` โดย sort keys
5. เปรียบเทียบ normalized result และ PLY hashes
6. เขียนเฉพาะ run แรกเมื่อทั้งสองรอบตรง
7. ระบุ scope `deterministic_fixture_not_accuracy_or_credit_validation`

- [ ] **Step 4: เขียน manifest validator/sealer tests**

~~~python
def test_seal_rejects_dirty_or_non_reproducible_candidate(tmp_path):
    candidate = valid_candidate()
    candidate["git_dirty"] = True
    with pytest.raises(ValueError, match="clean"):
        validate_candidate(candidate)

def test_manifest_never_uses_layout_fixture_values(tmp_path):
    manifest = build_manifest(valid_candidate(), core_manifest_hash="a" * 64)
    encoded = json.dumps(manifest)
    assert "93135" not in encoded
    assert manifest["result"]["total_co2eq_kg"] == valid_candidate()["result"]["total_co2eq_kg"]
~~~

Sealer schema ต้องมี analyzed commit, dirty=false, pipeline/backend/dataset scope, source core-manifest hash, artifact path/hash/size, result counts/totals, viewer capabilities และ `release.status` เป็น `candidate` หรือ `frozen`

CLI contract:

- `seal --artifact-dir PATH --status candidate` สร้าง/copy artifacts จาก clean analyzed commit
- `finalize --backup-video PATH` ตรวจ manifest/artifacts เดิมแล้วแนบ hash วิดีโอโดยไม่เปลี่ยน analyzed commit
- `check [--candidate-dir PATH]` ตรวจ committed bytes และถ้ามี candidate directory ให้ตรวจ reproducibility ภายใน candidate แยกจาก commit identity ปัจจุบัน

Generated TypeScript ต้องมี contract คงที่:

~~~typescript
export interface JudgeDemoEvidenceIdentity {
  manifestSha256: string;
  manifestPath: '/demo/manifest.json';
  inputPath: '/demo/input.ply';
  segmentedPath: '/demo/segmented.ply';
  resultPath: '/demo/result.json';
}
~~~

Generator ต้องเขียนค่า `manifestSha256` 64 hex ที่คำนวณจาก public manifest bytes จริง

- [ ] **Step 5: รัน manifest tests และ focused lint**

~~~powershell
& 'services/ml/.venv/Scripts/python.exe' -m pytest services/ml/tests/test_ply_export.py services/ml/tests/test_judge_demo.py scripts/tests/test_judge_demo_manifest.py -q --no-cov
& 'services/ml/.venv/Scripts/ruff.exe' check services/ml/pipeline/ply_export.py services/ml/scripts/run_judge_demo.py services/ml/tests/test_judge_demo.py scripts/judge_demo_manifest.py scripts/tests/test_judge_demo_manifest.py
~~~

Expected: PASS

- [ ] **Step 6: Commit Task 3**

~~~powershell
git add services/ml/pipeline/ply_export.py services/ml/scripts/run_judge_demo.py services/ml/tests/test_ply_export.py services/ml/tests/test_judge_demo.py scripts/judge_demo_manifest.py scripts/tests/test_judge_demo_manifest.py
git commit -m "feat(ml): build deterministic judge demo artifacts"
~~~

---

### Task 4: P0 hash-verified Frozen Evidence route

**Files:**
- Create generated: `docs/evidence/judge_demo_manifest.json`
- Create generated: `apps/web/public/demo/input.ply`
- Create generated: `apps/web/public/demo/segmented.ply`
- Create generated: `apps/web/public/demo/result.json`
- Create generated: `apps/web/public/demo/manifest.json`
- Create generated: `apps/web/src/generated/judge-demo-evidence.ts`
- Create: `apps/web/src/lib/frozen-demo.ts`
- Create: `apps/web/src/lib/frozen-demo.test.ts`
- Create: `apps/web/src/app/demo/page.tsx`
- Create: `apps/web/src/components/demo/demo-shell.tsx`
- Create: `apps/web/src/components/demo/mode-badge.tsx`

**Interfaces:**
- Consumes: Task 2 mode state; Task 3 artifact directory and manifest sealer
- Produces: `loadFrozenDemo(fetcher) -> Promise<FrozenDemoBundle>` และ public `/demo` route
- Task 8 replaces shell internals but keeps `FrozenDemoBundle` and mode contract

- [ ] **Step 1: Generate candidate artifacts from a clean Task 3 commit**

~~~powershell
Remove-Item -Recurse -Force -LiteralPath 'temp/judge-demo-candidate' -ErrorAction SilentlyContinue
& 'services/ml/.venv/Scripts/python.exe' services/ml/scripts/run_judge_demo.py --output-dir temp/judge-demo-candidate --repo-root .
& 'services/ml/.venv/Scripts/python.exe' scripts/judge_demo_manifest.py seal --repo-root . --artifact-dir temp/judge-demo-candidate --status candidate
~~~

Expected: five committed-target artifacts are written; manifest `analyzed_commit` equals Task 3 commit and `git_dirty` is false because cleanliness is sampled before outputs are copied

- [ ] **Step 2: เขียน failing browser hash tests**

~~~typescript
it('loads only when manifest and every artifact hash match', async () => {
  const bundle = await loadFrozenDemo(fakeFetcher(validFiles), EXPECTED_MANIFEST_SHA);
  expect(bundle.mode).toBe('frozen');
  expect(bundle.result.metadata.wood_leaf_backend).toBe('tlsep');
});

it('fails closed on a changed result byte', async () => {
  await expect(
    loadFrozenDemo(fakeFetcher({ ...validFiles, result: changedResult }), EXPECTED_MANIFEST_SHA),
  ).rejects.toThrow(/hash mismatch/i);
});
~~~

- [ ] **Step 3: รัน browser test เพื่อยืนยัน RED**

~~~powershell
pnpm --dir apps/web exec vitest run src/lib/frozen-demo.test.ts
~~~

Expected: FAIL เพราะ loader ยังไม่มี

- [ ] **Step 4: Implement frozen loader and minimal public route**

`loadFrozenDemo` ต้อง verify public manifest bytes กับ `JUDGE_DEMO_EVIDENCE.manifestSha256` ก่อน parse จากนั้น verify `result.json`, `input.ply` และ `segmented.ply` ตาม manifest ด้วย `crypto.subtle.digest('SHA-256', bytes)`

`/demo` ต้อง:

- render blank/scrubbing shell จน `consumeRuntimeHandoff` ทำงาน
- default เป็น verified frozen sample เมื่อไม่มี handoff
- แสดง badge ตัวพิมพ์ชัด `FROZEN EVIDENCE — NOT A LIVE RUN`
- แสดง `loading failed` และไม่แสดงตัวเลขเมื่อ hash ใดผิด
- ไม่ import Supabase client, generic `api.ts` หรือ auth layout

- [ ] **Step 5: Verify manifest, web tests and build**

~~~powershell
& 'services/ml/.venv/Scripts/python.exe' scripts/judge_demo_manifest.py check --repo-root .
pnpm --dir apps/web exec vitest run src/lib/frozen-demo.test.ts src/lib/demo-runtime.test.ts src/lib/demo-mode.test.ts
pnpm --dir apps/web type-check
pnpm --dir apps/web build
~~~

Expected: PASS; build creates `apps/web/.next/standalone` and `/demo` is static/server renderable without Supabase env

- [ ] **Step 6: Commit Task 4**

~~~powershell
git add docs/evidence/judge_demo_manifest.json apps/web/public/demo apps/web/src/generated/judge-demo-evidence.ts apps/web/src/lib/frozen-demo.ts apps/web/src/lib/frozen-demo.test.ts apps/web/src/app/demo apps/web/src/components/demo
git commit -m "feat(web): add verified frozen judge demo"
~~~

---

### Task 5: P0 canonical one-click launcher and three-mode fallback

**Files:**
- Create: `scripts/demo/DemoLauncher.psm1`
- Create: `scripts/demo/start-treeq-demo.ps1`
- Create: `scripts/demo/TreeQ-Demo-Start.bat`
- Create: `scripts/demo/install-desktop-wrapper.ps1`
- Create: `scripts/demo/tests/run-tests.ps1`
- Create: `scripts/demo/README.md`

**Interfaces:**
- Consumes: Task 1 readiness HMAC, Task 2 fragment contract, Task 4 standalone build/manifest
- Produces: one-click launcher with parameters `-Mode Auto|Local|Frozen`, `-CloudflaredPath PATH`, `-NoBrowser`, `-ExitAfterReady` และ process registry `temp/demo-runtime/processes.json`
- Task 10 invokes helper harness on Windows CI; Task 11 packages these files

- [ ] **Step 1: เขียน dependency-free failing assertion harness**

Harness ต้อง test:

~~~powershell
$token = New-TreeQDemoToken
Assert-True ($token -match '^[0-9a-f]{64}$') 'token is 256-bit hex'

$url = Get-TreeQTunnelUrl 'INF Visit https://green-tree.trycloudflare.com now'
Assert-Equal $url 'https://green-tree.trycloudflare.com' 'parse exact tunnel URL'

Assert-Null (Get-TreeQTunnelUrl 'https://evil.trycloudflare.com.attacker.test') 'reject suffix attack'

$redacted = Protect-TreeQLog -Text "token=$token" -Secrets @($token)
Assert-True (-not $redacted.Contains($token)) 'redact token'
~~~

Harness ต้อง exit `1` หาก assertion ใดล้ม และ exit `0` พร้อม ASCII summary เมื่อผ่าน

- [ ] **Step 2: รัน harness เพื่อยืนยัน RED**

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo/tests/run-tests.ps1
~~~

Expected: FAIL เพราะ module ยังไม่มี

- [ ] **Step 3: Implement pure launcher helpers**

`DemoLauncher.psm1` ต้อง export:

~~~powershell
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
~~~

`New-TreeQHandoffUrl` ใช้ `Uri.EscapeDataString` และสร้าง token ใน fragment ห้าม query; `Test-TreeQReadiness` ส่ง nonce และ verify HMAC locally

- [ ] **Step 4: Implement orchestration with owned PIDs**

`start-treeq-demo.ps1` ทำตามลำดับ:

1. resolve repo root จากตำแหน่ง script ไม่ใช้ absolute user path
2. verify public frozen manifest และ artifact hashes ก่อนเสมอ
3. หา standalone server, API Python, ML Python, Node และ cloudflared จาก parameter/env/PATH
4. อ่าน registry เก่าและ stop เฉพาะ PID ที่ executable path/start time ตรง
5. สร้าง token ใน parent environment, start API Python โดยตรง, แล้ว remove token จาก parent
6. start standalone Node server โดยตรงและบันทึก PID
7. probe local authenticated readiness
8. ถ้า `Auto` ให้ start tunnel, parse exact URL และ probe public authenticated readiness
9. เปิด production handoff เมื่อ public ready; ไม่เช่นนั้นเปิด local handoff
10. ถ้า API ไม่ ready ให้เปิด local `/demo` frozen; ถ้า local web ไม่ ready และ internet มี ให้เปิด production `/demo` frozen
11. รอ Enter/Ctrl+C แล้ว stop เฉพาะ registered PIDs ใน `finally`

เมื่อใช้ `-ExitAfterReady` ให้จบหลัง readiness/mode decision และเข้า `finally` ทันที เพื่อให้ CI ทดสอบ lifecycle ได้โดยไม่รอ input

Launcher ห้าม run `pnpm build` หรือ Vercel command ขณะ start

- [ ] **Step 5: สร้าง installer สำหรับ desktop wrapper**

Installer รับ `-DestinationDirectory` และค้น `cloudflared.exe` ใน directory นั้น แล้วสร้าง wrapper ชื่อ `TreeQ-Demo-Start.bat` ที่ตั้ง `TREEQ_CLOUDFLARED` และเรียก canonical batch ใน repo ห้ามแก้หรือลบ legacy scripts อัตโนมัติ

- [ ] **Step 6: รัน helper, dry-run and process-ownership tests**

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo/tests/run-tests.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo/start-treeq-demo.ps1 -Mode Frozen -NoBrowser -ExitAfterReady
~~~

Expected: harness PASS; frozen dry-run verify hashes/start standalone/stop owned Node โดยไม่แตะ Python หรือ cloudflared ที่เปิดโดย process อื่น

- [ ] **Step 7: Commit Task 5**

~~~powershell
git add scripts/demo
git commit -m "feat(demo): add one-click resilient launcher"
~~~

## P0 checkpoint

ก่อนเริ่ม P1 ให้ทดสอบ Frozen/Local และ Auto orchestration แบบไม่เปิด browser:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo/start-treeq-demo.ps1 -Mode Frozen
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo/start-treeq-demo.ps1 -Mode Local
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo/start-treeq-demo.ps1 -Mode Auto -CloudflaredPath $env:TREEQ_CLOUDFLARED -NoBrowser -ExitAfterReady
~~~

Expected:

- Frozen เปิดโดยไม่ start API/tunnel และแสดงป้าย NOT A LIVE RUN
- Local เปิด standalone web + authenticated local API
- Auto dry-run ต้องพิสูจน์ public readiness และสร้าง handoff URL ที่ถูก redact; browser path ทดสอบหลัง Task 12 merge/deploy แล้วเท่านั้น
- ไม่มี command ใด deploy Vercel และ runtime log ไม่มี token

---

### Task 6: P1 ML detected/measured/excluded diagnostics

**Files:**
- Modify: `services/ml/pipeline/main.py`
- Modify: `services/ml/scripts/run_core_demo.py`
- Modify: `services/ml/scripts/run_judge_demo.py`
- Modify: `services/ml/tests/test_pipeline_orchestrator.py`
- Modify: `services/ml/tests/test_core_demo.py`
- Modify: `services/ml/tests/test_judge_demo.py`

**Interfaces:**
- Consumes: existing per-tree loop and QSM result
- Produces: `ExcludedSegment`, `PipelineDiagnostics`, `pipeline_result_to_dict(result)` and new result keys
- Task 7 maps these exact values into Pydantic; Task 8 maps reason codes to Thai

- [ ] **Step 1: เขียน failing silent-drop tests**

~~~python
def test_empty_wood_is_reported_not_silently_dropped(synth_points, monkeypatch):
    from pipeline import wood_leaf_separation

    monkeypatch.setattr(
        wood_leaf_separation.WoodLeafSegmenter,
        "segment",
        lambda self, points: np.full(len(points), wood_leaf_separation.LEAF, dtype=np.uint8),
    )
    result = process_points(synth_points)
    assert result.summary["detected_trees"] > 0
    assert result.summary["measured_trees"] == 0
    assert result.summary["excluded_trees"] == result.summary["detected_trees"]
    assert {d.reason_code for d in result.diagnostics.excluded_segments} == {"WOOD_EMPTY"}

def test_unexpected_segmenter_error_fails_the_run(synth_points, monkeypatch):
    def fail(self, points):
        raise RuntimeError("segmenter exploded")

    monkeypatch.setattr(WoodLeafSegmenter, "segment", fail)
    with pytest.raises(RuntimeError, match="segmenter exploded"):
        process_points(synth_points)
~~~

เพิ่ม test QSM invalid โดย monkeypatch segment เป็น all wood และ `qsm.compute_qsm` คืน `QsmResult` ที่ `dbh_cm=0`

- [ ] **Step 2: รัน orchestrator tests เพื่อยืนยัน RED**

~~~powershell
& 'services/ml/.venv/Scripts/python.exe' -m pytest services/ml/tests/test_pipeline_orchestrator.py -q --no-cov
~~~

Expected: FAIL เพราะ result ไม่มี diagnostics/new counts

- [ ] **Step 3: เพิ่ม typed diagnostics โดยไม่เปลี่ยน measurement algorithm**

เพิ่ม:

~~~python
@dataclass(frozen=True)
class ExcludedSegment:
    tree_id: int
    stage: Literal["wood_leaf", "qsm"]
    reason_code: Literal["WOOD_EMPTY", "QSM_INVALID"]

@dataclass
class PipelineDiagnostics:
    excluded_segments: list[ExcludedSegment] = field(default_factory=list)

@dataclass
class PipelineResult:
    metadata: dict[str, Any]
    summary: dict[str, Any]
    trees: list[TreeResult]
    diagnostics: PipelineDiagnostics = field(default_factory=PipelineDiagnostics)
~~~

ใน loop:

- `len(wood) == 0` append `ExcludedSegment(tid,"wood_leaf","WOOD_EMPTY")` แล้ว continue
- DBH/height invalid append `ExcludedSegment(tid,"qsm","QSM_INVALID")` แล้ว continue
- exception อื่นปล่อยให้ propagate

Summary ต้องใช้:

~~~python
detected = len(tree_clouds)
measured = len(trees)
excluded = len(diagnostics.excluded_segments)
assert detected == measured + excluded
~~~

ตั้ง `total_trees=measured` และเพิ่ม three count fields เปลี่ยน `PIPELINE_VERSION` เป็น `0.4.0`

- [ ] **Step 4: รวม serializer ให้ runner ทุกตัวใช้ schema เดียว**

`pipeline_result_to_dict` ต้องคืน:

~~~python
{
    "metadata": result.metadata,
    "summary": result.summary,
    "diagnostics": {
        "excluded_segments": [asdict(item) for item in result.diagnostics.excluded_segments]
    },
    "trees": [asdict(tree) for tree in result.trees],
}
~~~

ให้ `process_point_cloud`, core runner และ judge runner เรียก helper นี้แทน serializer แยก

- [ ] **Step 5: รัน ML focused suite**

~~~powershell
& 'services/ml/.venv/Scripts/python.exe' -m pytest services/ml/tests/test_pipeline_orchestrator.py services/ml/tests/test_core_demo.py services/ml/tests/test_judge_demo.py -q --no-cov
& 'services/ml/.venv/Scripts/ruff.exe' check services/ml/pipeline/main.py services/ml/scripts/run_core_demo.py services/ml/scripts/run_judge_demo.py services/ml/tests/test_pipeline_orchestrator.py
~~~

Expected: PASS; existing carbon assertions ไม่เปลี่ยน และทุก result ใหม่รักษา count invariants

- [ ] **Step 6: Commit Task 6**

~~~powershell
git add services/ml/pipeline/main.py services/ml/scripts/run_core_demo.py services/ml/scripts/run_judge_demo.py services/ml/tests/test_pipeline_orchestrator.py services/ml/tests/test_core_demo.py services/ml/tests/test_judge_demo.py
git commit -m "feat(ml): explain excluded tree segments"
~~~

---

### Task 7: P1 typed API diagnostics and compatibility

**Files:**
- Modify: `services/api/app/schemas/analyze.py`
- Modify: `services/api/tests/test_upload_analyze.py`
- Modify: `services/api/tests/test_job_schemas.py`
- Modify: `apps/web/src/lib/api.ts`
- Modify: `apps/web/src/lib/api.test.ts`

**Interfaces:**
- Consumes: Task 6 output
- Produces: `AnalyzeExcludedSegment`, `AnalyzeDiagnostics` and optional compatibility fields on `AnalyzeSummary`/`AnalyzeResponse`
- Task 8 consumes these TypeScript types; old stored async-job results remain readable

- [ ] **Step 1: เขียน failing Pydantic invariant tests**

~~~python
def test_new_analyze_contract_preserves_count_invariants():
    result = AnalyzeResponse.model_validate(RESULT_WITH_DIAGNOSTICS)
    assert result.summary.total_trees == result.summary.measured_trees == 18
    assert len(result.diagnostics.excluded_segments) == 2

def test_partial_diagnostic_counts_are_rejected():
    broken = deepcopy(RESULT_WITH_DIAGNOSTICS)
    del broken["summary"]["excluded_trees"]
    with pytest.raises(ValidationError):
        AnalyzeResponse.model_validate(broken)

def test_legacy_stored_result_remains_readable():
    legacy = AnalyzeResponse.model_validate(FAKE_RESULT_WITHOUT_DIAGNOSTICS)
    assert legacy.diagnostics is None
    assert legacy.summary.detected_trees is None
~~~

- [ ] **Step 2: รัน API schema tests เพื่อยืนยัน RED**

~~~powershell
& 'services/api/.venv/Scripts/python.exe' -m pytest services/api/tests/test_upload_analyze.py services/api/tests/test_job_schemas.py -q
~~~

Expected: FAIL เพราะ schema fields ยังไม่มี

- [ ] **Step 3: เพิ่ม exact Pydantic contract**

~~~python
class AnalyzeExcludedSegment(BaseModel):
    tree_id: int
    stage: Literal["wood_leaf", "qsm"]
    reason_code: Literal["WOOD_EMPTY", "QSM_INVALID"]

class AnalyzeDiagnostics(BaseModel):
    excluded_segments: list[AnalyzeExcludedSegment] = Field(default_factory=list)

class AnalyzeSummary(BaseModel):
    total_trees: int = Field(ge=0)
    detected_trees: int | None = Field(default=None, ge=0)
    measured_trees: int | None = Field(default=None, ge=0)
    excluded_trees: int | None = Field(default=None, ge=0)
    total_carbon_kg: float
    total_co2eq_kg: float
~~~

`model_validator(mode="after")` บังคับว่า diagnostic counts ต้องมาครบทั้งสาม, alias/invariant ตรง และ `AnalyzeResponse` validator เทียบ list length เมื่อ diagnostics มีค่า

- [ ] **Step 4: Mirror exact optional fields in TypeScript**

~~~typescript
export interface AnalyzeExcludedSegment {
  tree_id: number;
  stage: 'wood_leaf' | 'qsm';
  reason_code: 'WOOD_EMPTY' | 'QSM_INVALID';
}

export interface AnalyzeSummary {
  total_trees: number;
  detected_trees?: number | null;
  measured_trees?: number | null;
  excluded_trees?: number | null;
  total_carbon_kg: number;
  total_co2eq_kg: number;
}
~~~

เพิ่ม `diagnostics?: { excluded_segments: AnalyzeExcludedSegment[] } | null` ใน `AnalyzeResponse`

- [ ] **Step 5: รัน API/web contract tests**

~~~powershell
& 'services/api/.venv/Scripts/python.exe' -m pytest services/api/tests/test_upload_analyze.py services/api/tests/test_job_schemas.py -q
pnpm --dir apps/web exec vitest run src/lib/api.test.ts
pnpm --dir apps/web type-check
~~~

Expected: PASS

- [ ] **Step 6: Commit Task 7**

~~~powershell
git add services/api/app/schemas/analyze.py services/api/tests/test_upload_analyze.py services/api/tests/test_job_schemas.py apps/web/src/lib/api.ts apps/web/src/lib/api.test.ts
git commit -m "feat(api): expose typed tree diagnostics"
~~~

---

### Task 8: P1 Results Workspace and truthful Live Upload

**Files:**
- Create: `apps/web/src/lib/result-view-model.ts`
- Create: `apps/web/src/lib/result-view-model.test.ts`
- Create: `apps/web/src/components/demo/demo-workspace.tsx`
- Create: `apps/web/src/components/demo/point-cloud-panel.tsx`
- Create: `apps/web/src/components/demo/upload-panel.tsx`
- Create: `apps/web/src/components/demo/result-summary.tsx`
- Create: `apps/web/src/components/demo/tree-result-table.tsx`
- Create: `apps/web/src/components/demo/provenance-panel.tsx`
- Create: `apps/web/src/components/demo/pipeline-status.tsx`
- Modify: `apps/web/src/app/demo/page.tsx`
- Modify: `apps/web/src/components/viewer/point-cloud-viewer.tsx`
- Modify: `apps/web/src/components/viewer/point-cloud-legend.tsx`
- Modify: `apps/web/src/lib/ply-loader.ts`
- Modify: `apps/web/src/lib/ply-loader.test.ts`

**Interfaces:**
- Consumes: `FrozenDemoBundle`, `DemoModeState`, `DemoApiClient` and `AnalyzeResponse`
- Produces: one Results Workspace shared by frozen/live data with `ResultViewModel`
- Task 9 links landing CTA here; Task 10 drives stable accessible labels

- [ ] **Step 1: เขียน failing view-model and PLY capability tests**

~~~typescript
it('calls total_trees measured, never detected', () => {
  const vm = toResultViewModel(RESPONSE_WITH_DIAGNOSTICS);
  expect(vm.counts).toEqual({ detected: 20, measured: 18, excluded: 2 });
  expect(vm.countsLabel.measured).toBe('ต้นไม้ที่คำนวณสำเร็จ');
});

it('does not invent zero when diagnostics are absent', () => {
  const vm = toResultViewModel(LEGACY_RESPONSE);
  expect(vm.counts.detected).toBeNull();
  expect(vm.counts.excluded).toBeNull();
  expect(vm.diagnosticsStatus).toBe('unavailable');
});

it('maps only typed reason codes', () => {
  expect(reasonLabel('WOOD_EMPTY')).toContain('ไม่พบจุดลำต้น');
  expect(reasonLabel('QSM_INVALID')).toContain('DBH หรือความสูง');
});
~~~

เพิ่ม field `classification: 'available' | 'unavailable'` ใน `PointCloud`: demo generator และ segmented PLY เป็น `available`, raw PLY ที่ไม่มี `class` เป็น `unavailable` และ `decimate` ต้องรักษาค่านี้ เพื่อไม่เรียก original upload ว่า segmented

- [ ] **Step 2: รัน focused tests เพื่อยืนยัน RED**

~~~powershell
pnpm --dir apps/web exec vitest run src/lib/result-view-model.test.ts src/lib/ply-loader.test.ts
~~~

Expected: FAIL เพราะ view model และ capability flag ยังไม่มี

- [ ] **Step 3: Implement truthful result adapter**

`ResultViewModel` ต้องมี:

~~~typescript
export interface ResultViewModel {
  counts: { detected: number | null; measured: number; excluded: number | null };
  diagnosticsStatus: 'available' | 'unavailable';
  excludedRows: Array<{
    treeId: number;
    stage: 'wood_leaf' | 'qsm';
    reasonCode: 'WOOD_EMPTY' | 'QSM_INVALID';
    reasonTh: string;
  }>;
  totalCarbonKg: number;
  totalCo2eqKg: number;
  isCertifiedCredit: false;
}
~~~

เมื่อ fields เก่าไม่มี ให้ measured มาจาก `total_trees` แต่ detected/excluded เป็น null และ UI แสดง `ไม่มี diagnostics จาก run นี้`

- [ ] **Step 4: เพิ่ม viewer capabilities โดยไม่สร้าง artifact ปลอม**

`PointCloudViewer` รับ:

~~~typescript
type ViewerColorMode = 'neutral' | 'classification';
type ViewerLayer = 'all' | 'wood' | 'leaf';
~~~

Filtering ต้องสร้าง index/positions subset จาก class จริง; neutral mode ใช้สี Forest Mist เดียว Original mode ของ raw uploadห้ามใช้สี ground เพื่อสื่อว่าเป็น ground classification

Results control:

- Frozen artifact: Original, Wood และ Leaf เปิด
- Live raw upload: Original เปิด; Wood/Leaf/QSM disabled พร้อม `artifact unavailable for this run`
- QSM disabled จนมี QSM geometry artifact จริง

- [ ] **Step 5: Implement upload state machine and confirmation**

Upload states:

~~~typescript
type UploadState =
  | { kind: 'idle' }
  | { kind: 'validating' }
  | { kind: 'ready'; file: File; rawSha256: string; pointCount: number }
  | { kind: 'uploading' }
  | { kind: 'processing' }
  | { kind: 'complete'; response: AnalyzeResponse }
  | { kind: 'error'; message: string };
~~~

Flow ต้อง:

1. รับเฉพาะ `.ply`
2. reject >100 MB และ declared points >2,000,000 ก่อนส่ง
3. parse preview/downsample ไม่เกิน 200,000 จุด
4. คำนวณ raw file SHA-256
5. แสดงชื่อ/ขนาด/point count/hash และขอ click ยืนยัน
6. เปิด upload เฉพาะ live readiness ผ่าน
7. ใช้ XHR phases จาก Task 2
8. แสดง server normalized XYZ hash แยกจาก raw hash

- [ ] **Step 6: Compose Results Workspace**

Desktop layout:

- header: breadcrumb, mode badge, retry/use-frozen control
- left 7 columns: 3D point-cloud panel
- right 5 columns: carbon summary, truthful counts, upload status
- lower full width: measured/excluded table, provenance, limitations

Carbon card ต้องเขียน `ค่าประมาณ CO₂e — ไม่ใช่คาร์บอนเครดิตที่ผ่านการรับรอง` และ provenance แสดง pipeline version, full input hash with copy control, git commit/dirty, `tlsep baseline`, species Stub และ allometric algorithm

- [ ] **Step 7: รัน unit/type/build gates**

~~~powershell
pnpm --dir apps/web exec vitest run src/lib/result-view-model.test.ts src/lib/ply-loader.test.ts src/lib/demo-api.test.ts src/lib/frozen-demo.test.ts
pnpm --dir apps/web lint
pnpm --dir apps/web type-check
pnpm --dir apps/web build
~~~

Expected: PASS; no text `จำนวนต้นไม้` appears as label for `total_trees` in demo components

- [ ] **Step 8: Commit Task 8**

~~~powershell
git add apps/web/src/app/demo apps/web/src/components/demo apps/web/src/components/viewer apps/web/src/lib/result-view-model.ts apps/web/src/lib/result-view-model.test.ts apps/web/src/lib/ply-loader.ts apps/web/src/lib/ply-loader.test.ts
git commit -m "feat(web): build the judge results workspace"
~~~

---

### Task 9: P1 Forest Observatory landing and offline typography

**Files:**
- Create binary: `apps/web/src/assets/fonts/NotoSerifThai[wdth,wght].ttf`
- Create binary: `apps/web/src/assets/fonts/NotoSansThai[wdth,wght].ttf`
- Create: `apps/web/src/assets/fonts/OFL-NotoSerifThai.txt`
- Create: `apps/web/src/assets/fonts/OFL-NotoSansThai.txt`
- Create: `apps/web/src/assets/fonts/THIRD_PARTY_FONTS.md`
- Create: `apps/web/src/components/landing/forest-observatory-hero.tsx`
- Create: `apps/web/src/components/landing/forest-observatory-visual.tsx`
- Create: `apps/web/src/components/landing/evidence-strip.tsx`
- Create: `apps/web/src/components/landing/pipeline-story.tsx`
- Modify: `apps/web/src/app/layout.tsx`
- Modify: `apps/web/src/app/page.tsx`
- Modify: `apps/web/src/app/globals.css`
- Modify: `apps/web/tailwind.config.ts`
- Create: `apps/web/src/lib/landing-content.test.ts`

**Interfaces:**
- Consumes: `CORE_DEMO_EVIDENCE` and `/demo` route
- Produces: server-only landing components and CSS tokens `--forest-ink`, `--moss`, `--gallery-ivory`, `--mist`, `--evidence-amber`
- Task 10 checks CTA, claims and viewport layout

- [ ] **Step 1: เขียน failing landing truth tests**

~~~typescript
it('uses the judge demo as the primary route', () => {
  expect(LANDING_CTA.primary).toEqual({ label: 'เริ่ม Judge Demo', href: '/demo' });
});

it('keeps exact evidence and limitation copy together', () => {
  expect(LANDING_EVIDENCE.woodIoU).toBe(0.418);
  expect(LANDING_EVIDENCE.leafIoU).toBe(0.808);
  expect(LANDING_EVIDENCE.dbhMaeCm).toBe(1.1673846154);
  expect(LANDING_EVIDENCE.creditClaim).toMatch(/ไม่ใช่.*คาร์บอนเครดิต/);
});
~~~

- [ ] **Step 2: รัน test เพื่อยืนยัน RED**

~~~powershell
pnpm --dir apps/web exec vitest run src/lib/landing-content.test.ts
~~~

Expected: FAIL เพราะ landing content module/components ยังไม่มี

- [ ] **Step 3: นำเข้า font ที่ redistribute ได้พร้อม license**

ใช้ไฟล์ทางการ:

- `https://raw.githubusercontent.com/google/fonts/main/ofl/notoserifthai/NotoSerifThai%5Bwdth%2Cwght%5D.ttf`
- `https://raw.githubusercontent.com/google/fonts/main/ofl/notosansthai/NotoSansThai%5Bwdth%2Cwght%5D.ttf`
- `https://raw.githubusercontent.com/google/fonts/main/ofl/notoserifthai/OFL.txt`
- `https://raw.githubusercontent.com/google/fonts/main/ofl/notosansthai/OFL.txt`

คำนวณ SHA-256 ของ binary สองไฟล์และบันทึกค่าที่ได้จริงพร้อม source URL/date ใน `THIRD_PARTY_FONTS.md` ห้ามใช้ Dribbble asset

เปลี่ยน layout เป็น `next/font/local`:

~~~typescript
const notoSerifThai = localFont({
  src: '../assets/fonts/NotoSerifThai[wdth,wght].ttf',
  variable: '--font-noto-serif-thai',
  display: 'swap',
});

const notoSansThai = localFont({
  src: '../assets/fonts/NotoSansThai[wdth,wght].ttf',
  variable: '--font-noto-sans-thai',
  display: 'swap',
});
~~~

ลบ `next/font/google` imports ทั้งหมดเพื่อให้ build ใหม่ไม่ต้อง download font

- [ ] **Step 4: Implement original Forest Observatory composition**

Hero เป็น split layout:

- ซ้าย: static SVG forest/point-cloud/QSM sculpture ที่สร้างจาก deterministic coordinates; ไม่มี canvas, photo หรือ copied asset
- ขวา: headline สั้น, explanation 2–3 บรรทัด, primary `เริ่ม Judge Demo`, secondary `ดูผลทดสอบจริง`
- ล่าง: evidence strip แสดง `0.418`, `0.808`, `1.167 cm` พร้อม cohort/scope

รักษา whitespace, max width 1400, ivory background, Forest Ink text, Moss CTA และ Evidence Amber เฉพาะ limitations ลด sections ที่ไม่ช่วย Judge Journey และไม่แสดง login/signup เป็น CTA หลัก

- [ ] **Step 5: Verify server-only and visual constraints**

~~~powershell
rg -n "'use client'|styled-jsx|<canvas|/signup" apps/web/src/components/landing apps/web/src/app/page.tsx
pnpm --dir apps/web exec vitest run src/lib/landing-content.test.ts src/lib/evidence.test.ts
pnpm --dir apps/web lint
pnpm --dir apps/web type-check
pnpm --dir apps/web build
~~~

Expected: `rg` ไม่พบ forbidden patterns; tests/build PASS

- [ ] **Step 6: Commit Task 9**

~~~powershell
git add apps/web/src/assets/fonts apps/web/src/components/landing apps/web/src/app/layout.tsx apps/web/src/app/page.tsx apps/web/src/app/globals.css apps/web/tailwind.config.ts apps/web/src/lib/landing-content.test.ts
git commit -m "feat(web): deliver the Forest Observatory journey"
~~~

---

### Task 10: P0/P1 browser verification and CI gates

**Files:**
- Create: `apps/web/playwright.config.ts`
- Create: `apps/web/e2e/judge-demo.spec.ts`
- Create: `.github/workflows/ci-demo.yml`
- Modify: `.github/workflows/ci-web.yml`
- Modify: `.github/workflows/ci-api.yml`
- Modify: `.github/workflows/ci-ml.yml`
- Modify: `apps/web/package.json`

**Interfaces:**
- Consumes: accessible UI labels and pure launcher/manifest commands
- Produces: `pnpm test:judge` and CI jobs `judge-web`, `judge-api-contract`, `judge-launcher-windows`, `judge-evidence`
- Task 12 requires all jobs green without swallowed failure

- [ ] **Step 1: เขียน failing Playwright journeys**

~~~typescript
test('sample-first opens verified frozen evidence without login', async ({ page }) => {
  await page.goto('/demo');
  await expect(page.getByText('FROZEN EVIDENCE — NOT A LIVE RUN')).toBeVisible();
  await expect(page.getByText('ต้นไม้ที่คำนวณสำเร็จ')).toBeVisible();
  await expect(page).not.toHaveURL(/login/);
});

test('invalid handoff is scrubbed and never becomes live', async ({ page }) => {
  await page.goto('/demo#api=https%3A%2F%2Fevil.example&token=' + 'a'.repeat(64));
  await expect(page).toHaveURL(/\/demo$/);
  await expect(page.getByText('FROZEN EVIDENCE — NOT A LIVE RUN')).toBeVisible();
});

test('1366 viewport has no page overflow', async ({ page }) => {
  await page.setViewportSize({ width: 1366, height: 768 });
  await page.goto('/');
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
  await expect(page.getByRole('link', { name: 'เริ่ม Judge Demo' })).toBeVisible();
});
~~~

เพิ่ม mocked live test ที่ intercept demo-ready/analyze, verify mode badge, XHR phase, detected/measured/excluded และ provenance; เพิ่ม readiness failure test ที่กลับ Frozen โดยไม่แสดง excluded เป็น zero

- [ ] **Step 2: รัน E2E เพื่อยืนยัน RED**

~~~powershell
pnpm --dir apps/web exec playwright install chromium
pnpm --dir apps/web build
pnpm --dir apps/web test:e2e --grep "sample-first|invalid handoff|viewport"
~~~

Expected: FAIL ก่อน config/selectors/UI contract ครบ

- [ ] **Step 3: กำหนด deterministic Playwright config**

Config ใช้ Chromium, retries `0` local/`1` CI, trace on first retry, screenshot on failure, base URL `http://127.0.0.1:3000` และ web server:

~~~typescript
webServer: {
  command: 'pnpm start --hostname 127.0.0.1 --port 3000',
  url: 'http://127.0.0.1:3000/demo',
  reuseExistingServer: !process.env.CI,
  timeout: 120_000,
}
~~~

เพิ่ม script `"test:judge": "playwright test e2e/judge-demo.spec.ts"`

- [ ] **Step 4: สร้าง CI workflow โดย checkout full history**

ทุก job ใช้ `actions/checkout@v4` พร้อม `fetch-depth: 0`

- Windows job รัน `scripts/demo/tests/run-tests.ps1`
- API job รัน demo security/upload/schema tests
- Evidence job รัน judge runner ลง temp แล้ว `judge_demo_manifest.py check --candidate-dir`
- Web job รัน unit/type/lint/build, install Chromium และ `pnpm test:judge`

ห้ามใช้ `|| true` หรือ advisory exit masking ใน demo workflow

- [ ] **Step 5: รัน full local CI-equivalent gates**

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo/tests/run-tests.ps1
& 'services/api/.venv/Scripts/python.exe' -m pytest services/api/tests -q
& 'services/ml/.venv/Scripts/python.exe' -m pytest services/ml/tests/test_pipeline_orchestrator.py services/ml/tests/test_judge_demo.py scripts/tests/test_judge_demo_manifest.py -q --no-cov
pnpm --dir apps/web exec vitest run
pnpm --dir apps/web lint
pnpm --dir apps/web type-check
pnpm --dir apps/web build
pnpm --dir apps/web test:judge
~~~

Expected: ทุก command PASS

- [ ] **Step 6: Commit Task 10**

~~~powershell
git add apps/web/playwright.config.ts apps/web/e2e apps/web/package.json .github/workflows/ci-demo.yml .github/workflows/ci-web.yml .github/workflows/ci-api.yml .github/workflows/ci-ml.yml
git commit -m "ci: gate the complete judge demo journey"
~~~

---

### Task 11: P2 release tooling, runbook and truthful repository status

**Files:**
- Create: `scripts/demo/release_contract.py`
- Create: `scripts/demo/verify_backup_video.py`
- Create: `scripts/demo/freeze-treeq-demo.ps1`
- Create: `scripts/tests/test_demo_release.py`
- Create: `docs/demo/JUDGE_DEMO_RUNBOOK.md`
- Create: `docs/demo/JUDGE_SCRIPT_TH.md`
- Create: `docs/demo/FAILURE_RESPONSE_TH.md`
- Modify: `.gitignore`
- Modify: `AGENTS.md`
- Modify: `docs/PROJECT_SPEC.md`
- Modify: `README.md`
- Modify: `docs/SESSION_HANDOFF.md`

**Interfaces:**
- Consumes: final build, public manifest, backup MP4, launcher and Git state
- Produces: ignored `release/TreeQ-Judge-Demo-NSC-2026/` and `release-lock.json`
- Task 12 supplies actual video/rehearsal inputs and seals evidence

- [ ] **Step 1: เขียน failing release-contract tests**

~~~python
def test_video_gate_requires_1080p_and_three_to_five_minutes():
    validate_video_metadata(width=1920, height=1080, duration_seconds=220)
    with pytest.raises(ValueError):
        validate_video_metadata(width=1280, height=720, duration_seconds=220)
    with pytest.raises(ValueError):
        validate_video_metadata(width=1920, height=1080, duration_seconds=301)

def test_freeze_deadline_is_at_least_24_hours():
    validate_freeze_time(
        frozen_at="2026-08-03T23:59:59+07:00",
        competition_start="2026-08-05T00:00:00+07:00",
    )
    with pytest.raises(ValueError):
        validate_freeze_time(
            frozen_at="2026-08-04T12:00:00+07:00",
            competition_start="2026-08-05T00:00:00+07:00",
        )
~~~

- [ ] **Step 2: รัน release tests เพื่อยืนยัน RED**

~~~powershell
& 'services/ml/.venv/Scripts/python.exe' -m pytest scripts/tests/test_demo_release.py -q --no-cov
~~~

Expected: FAIL เพราะ release modules ยังไม่มี

- [ ] **Step 3: Implement video/release validators**

`verify_backup_video.py` ใช้ OpenCV อ่าน width, height, fps/frame count และคืน JSON ASCII-safe; fail เมื่อไม่ใช่ 1920×1080 หรือ duration นอก 180–300 วินาที

`release_contract.py` สร้าง canonical JSON lock:

~~~python
{
    "schema_version": "1",
    "source_commit": source_commit,
    "production_commit": production_commit,
    "web_build_id": web_build_id,
    "judge_manifest_sha256": judge_manifest_sha256,
    "backup_video_sha256": backup_video_sha256,
    "rehearsal_sha256": rehearsal_sha256,
    "frozen_at": frozen_at,
    "competition_start": competition_start,
}
~~~

และ validate deadline/hashes/clean commit

- [ ] **Step 4: Implement fail-closed freeze script**

`freeze-treeq-demo.ps1` รับ:

~~~powershell
param(
  [Parameter(Mandatory)][string]$BackupVideo,
  [Parameter(Mandatory)][string]$Rehearsal,
  [Parameter(Mandatory)][string]$ProductionCommit,
  [datetimeoffset]$CompetitionStart = '2026-08-05T00:00:00+07:00',
  [string]$OutputDirectory = 'release/TreeQ-Judge-Demo-NSC-2026'
)
~~~

ลำดับ:

1. fail เมื่อ Git dirty
2. run manifest check, launcher harness, API/ML focused tests, web unit/type/lint/build/E2E
3. verify video metadata/hash และ rehearsal JSON schema/hash
4. copy standalone server + `.next/static` + `public`
5. copy launcher scripts, manifest, presenter/failure scripts และ video
6. write release lock หลัง build โดย source commit คือ current HEAD และ production commit ต้องมี Git tree ตรงกัน
7. verify copied hashesอีกรอบ
8. ห้ามสร้าง package หากเลย deadline

เพิ่ม `release/` และ `release-input/` ใน `.gitignore`

- [ ] **Step 5: เขียน operator and presenter documents**

`JUDGE_SCRIPT_TH.md` ต้องเป็น timeline:

- 00:00–00:35 problem/why
- 00:35–00:55 input + frozen provenance
- 00:55–02:15 pipeline
- 02:15–03:25 result + excluded explanation
- 03:25–04:00 trust/limitations
- Live Upload appendix ไม่เกิน 1 นาทีเพิ่ม

`FAILURE_RESPONSE_TH.md` มีประโยคพูดจริงสำหรับ tunnel fail, API fail, upload invalid และ frozen mode โดยไม่สวมรอย live

`JUDGE_DEMO_RUNBOOK.md` ระบุ preflight, one-click start, three mode badges, stop, known-good file, backup video และห้าม deploy/change branch วันแข่ง

- [ ] **Step 6: Update repository truth after code exists**

แก้เฉพาะสถานะจริงใน AGENTS/PROJECT_SPEC/README/SESSION_HANDOFF:

- launcher canonical อยู่ใน repo และไม่ redeploy Vercel
- production API ยังไม่ continuously deployed
- frozen evidence มี scope deterministic fixture
- diagnostics implemented หลัง tests ผ่าน
- PointNet++/species/certification status ไม่เปลี่ยน

ห้ามเปลี่ยน metric หลัก `0.418`, `0.808`, `0.613`, `0.831`, `1.1673846154 cm` หรือ claims ของ Demol

- [ ] **Step 7: รัน docs/release tests และ truth check**

~~~powershell
& 'services/ml/.venv/Scripts/python.exe' -m pytest scripts/tests/test_demo_release.py scripts/tests/test_sync_truth.py -q --no-cov
& 'services/ml/.venv/Scripts/python.exe' scripts/sync_truth.py --check
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo/tests/run-tests.ps1
git diff --check
~~~

Expected: PASS

- [ ] **Step 8: Commit Task 11**

~~~powershell
git add scripts/demo scripts/tests/test_demo_release.py docs/demo .gitignore AGENTS.md docs/PROJECT_SPEC.md README.md docs/SESSION_HANDOFF.md
git commit -m "docs(demo): add the competition freeze runbook"
~~~

---

### Task 12: P2 final evidence seal, rehearsal, freeze and publication

**Files:**
- Regenerate: `docs/evidence/judge_demo_manifest.json`
- Regenerate: `apps/web/public/demo/*`
- Regenerate: `apps/web/src/generated/judge-demo-evidence.ts`
- Local ignored input: `release-input/TreeQ-Judge-Demo-Backup-1080p.mp4`
- Local ignored input: `release-input/judge_demo_rehearsal.json`
- Local ignored output: `release/TreeQ-Judge-Demo-NSC-2026/*`

**Interfaces:**
- Consumes: all Tasks 1–11
- Produces: clean evidence-seal commit, green/merged PR, production verification, verified release package และ annotated freeze tag

- [ ] **Step 1: Run all automated gates at final implementation commit**

ใช้ `superpowers:verification-before-completion` แล้วรันใหม่ทั้งหมด:

~~~powershell
git status --short
& 'services/api/.venv/Scripts/python.exe' -m pytest services/api/tests -q
& 'services/ml/.venv/Scripts/python.exe' -m pytest services/ml/tests scripts/tests -q --no-cov
& 'services/ml/.venv/Scripts/python.exe' scripts/sync_truth.py --check
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo/tests/run-tests.ps1
pnpm --dir apps/web exec vitest run
pnpm --dir apps/web lint
pnpm --dir apps/web type-check
pnpm --dir apps/web build
pnpm --dir apps/web test:judge
git diff --check
~~~

Expected: clean before generation and every command PASS

- [ ] **Step 2: Regenerate judge artifacts from the clean implementation commit**

~~~powershell
Remove-Item -Recurse -Force -LiteralPath 'temp/final-judge-demo' -ErrorAction SilentlyContinue
& 'services/ml/.venv/Scripts/python.exe' services/ml/scripts/run_judge_demo.py --output-dir temp/final-judge-demo --repo-root .
& 'services/ml/.venv/Scripts/python.exe' scripts/judge_demo_manifest.py seal --repo-root . --artifact-dir temp/final-judge-demo --status candidate
& 'services/ml/.venv/Scripts/python.exe' scripts/judge_demo_manifest.py check --repo-root . --candidate-dir temp/final-judge-demo
~~~

Expected: reproducible true, all hashes match, analyzed commit equals pre-seal implementation commit, layout fixture values absent

- [ ] **Step 3: Commit candidate evidence seal**

~~~powershell
git add docs/evidence/judge_demo_manifest.json apps/web/public/demo apps/web/src/generated/judge-demo-evidence.ts
git commit -m "chore(demo): seal deterministic judge evidence"
~~~

- [ ] **Step 4: Record and validate the actual backup video from the sealed local build**

บันทึก Chrome 1920×1080 ตาม `JUDGE_SCRIPT_TH.md` ความยาว 180–300 วินาที เก็บเป็น `release-input/TreeQ-Judge-Demo-Backup-1080p.mp4` ตรวจว่าไม่มี token/address fragment, notification, account popup, private path หรือข้อมูลบุคคลในเฟรม

~~~powershell
& 'services/ml/.venv/Scripts/python.exe' scripts/demo/verify_backup_video.py release-input/TreeQ-Judge-Demo-Backup-1080p.mp4
Get-FileHash -Algorithm SHA256 -LiteralPath 'release-input/TreeQ-Judge-Demo-Backup-1080p.mp4'
~~~

Expected: 1920×1080, duration 180–300 seconds, SHA-256 64 hex

- [ ] **Step 5: Finalize video hash without changing analyzed commit**

รัน:

~~~powershell
& 'services/ml/.venv/Scripts/python.exe' scripts/judge_demo_manifest.py finalize --repo-root . --backup-video 'release-input/TreeQ-Judge-Demo-Backup-1080p.mp4'
& 'services/ml/.venv/Scripts/python.exe' scripts/judge_demo_manifest.py check --repo-root .
git add docs/evidence/judge_demo_manifest.json apps/web/public/demo/manifest.json apps/web/src/generated/judge-demo-evidence.ts
git commit -m "chore(demo): freeze backup evidence"
~~~

Manifest analyzed commit ยังคงชี้ code ที่สร้าง artifact; final seal commit เป็น commit ที่บรรจุ evidence จึงไม่ regenerate วน

- [ ] **Step 6: Push branch, create PR and wait for every required check**

~~~powershell
git push -u origin codex/judge-demo-sprint-impl
gh pr create --fill --head codex/judge-demo-sprint-impl
gh pr checks --watch
~~~

Expected: required checks green; ห้าม merge เมื่อมี pending/failure

- [ ] **Step 7: Merge only after owner approval and verify the Vercel production deployment**

หลังผู้ใช้/owner อนุมัติ merge ให้ merge PR ผ่าน GitHub แล้ว:

~~~powershell
git fetch origin main
$SealCommit = git rev-parse HEAD
$ProductionCommit = git rev-parse origin/main
git merge-base --is-ancestor $SealCommit $ProductionCommit
git diff --quiet $SealCommit $ProductionCommit --
~~~

Expected: seal commit เป็น ancestor และ Git tree ไม่มีความต่าง รอ Vercel Git integration deploy `origin/main` ไป `https://treeqcarbon.vercel.app` แล้วตรวจ `/` และ `/demo` ด้วย Chrome; production page ต้องเป็น revision ใหม่และ default Frozen sample ต้องเปิดได้

- [ ] **Step 8: Run production cold starts and failure rehearsals**

วัดจากไม่มี owned process เดิม:

1. Production Auto success ×3
2. tunnel unavailable -> Local Live
3. API unavailable -> Frozen Evidence
4. known-good `apps/web/public/demo/input.ply` Live Upload
5. normal narration ไม่เกิน 4 นาที
6. upload path ไม่เกิน 5 นาที
7. forced-failure narration ไม่เกิน 4:30

เขียน observed ISO timestamps, durations, seal commit, production commit, mode และ pass/fail ลง `release-input/judge_demo_rehearsal.json` ห้ามใส่ค่าคาดการณ์ ชื่อบัญชี หรือข้อมูลบุคคล

- [ ] **Step 9: Build/package after production verification and before deadline**

~~~powershell
pnpm --dir apps/web build
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo/freeze-treeq-demo.ps1 -BackupVideo 'release-input/TreeQ-Judge-Demo-Backup-1080p.mp4' -Rehearsal 'release-input/judge_demo_rehearsal.json' -ProductionCommit $ProductionCommit -CompetitionStart '2026-08-05T00:00:00+07:00'
~~~

Expected: release package verify ผ่าน; lock ชี้ seal commit, production commit, build ID, manifest, video และ rehearsal hashes; timestamp ไม่เกิน deadline

- [ ] **Step 10: Offline package smoke test**

ตัด internet แล้วเปิด launcher จาก release package ยืนยัน Frozen Evidence และ backup video เปิดได้ จากนั้น:

~~~powershell
git status --short
git diff --check
& 'services/ml/.venv/Scripts/python.exe' scripts/sync_truth.py --check
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo/tests/run-tests.ps1
~~~

Expected: source worktree clean; gates PASS

- [ ] **Step 11: Tag the exact production commit**

~~~powershell
git tag -a judge-demo-nsc-2026-freeze $ProductionCommit -m "TreeQ NSC 2026 judge demo freeze"
git push origin judge-demo-nsc-2026-freeze
~~~

Expected: tag points to the same commit deployed by Vercel; do not move or recreate the tag

---

## Spec coverage matrix

| Design section | Implemented by |
|---|---|
| `1–`4 context, goals, approved decisions and honest modes | Tasks 1–5 |
| `5 Judge Journey | Tasks 4, 8, 9, 10 and 11 |
| `6 Visual System | Tasks 8–10 |
| `7 Runtime Components | Tasks 1–5 |
| `8 Launcher Design | Task 5 and Task 10 Windows gate |
| `9 Runtime Handoff and Security | Tasks 1, 2, 5 and 10 |
| `10 Live Upload Behavior | Tasks 1, 2, 7 and 8 |
| `11 Pipeline Diagnostics Contract | Tasks 6–8 |
| `12 Frozen Evidence Bundle | Tasks 3, 4 and 12 |
| `13 Error Handling and Mode Transitions | Tasks 1, 2, 5, 8 and 10 |
| `14 Testing and Release Gates | Tasks 10–12 |
| `15 Freeze Policy | Tasks 11 and 12 |
| `16 Implementation Boundaries | File map and all task interfaces |
| `17 Risks and Controls | Tasks 1–5, 10 and 11 |
| `18 Acceptance Criteria | Definition of Done below |

---

## Definition of Done

1. One-click launcher ไม่ deploy และปิดเฉพาะ owned processes
2. Production Live, Local Live และ Frozen Evidence ผ่าน cold-start/failure tests
3. Frozen artifacts, manifest, result และ backup video ตรวจ hashes ผ่าน
4. Live Upload PLY จริงรายงาน phase จริง, raw hash และ normalized input hash
5. Detected/measured/excluded invariants ผ่าน ML, API และ web tests
6. UI ใช้คำว่า `ต้นไม้ที่คำนวณสำเร็จ` และอธิบาย excluded reason codes
7. Landing/Results Workspace ผ่านสอง viewport และไม่มี auth redirect
8. `tlsep`/PointNet++/species/certification claims ตรง evidence
9. Judge script ปกติไม่เกิน 4 นาที, upload ไม่เกิน 5 นาที และ failure rehearsal ไม่เกิน 4:30
10. Freeze package สร้างก่อน deadline, เปิดแบบ offline ได้ และ branch/PR checks green
