# Async Job Worker — Runbook

CarbonScan processes point clouds asynchronously so the API never blocks on
heavy ML. This doc covers running and deploying the worker.

## Flow
1. Client `POST /api/v1/jobs/analyze` (multipart file, Bearer token).
2. API validates, saves the upload to `JOB_UPLOAD_DIR`, inserts a `queued`
   job, returns **202** `{id, status, created_at}`.
3. The worker claims the job (`FOR UPDATE SKIP LOCKED`), runs the pipeline,
   marks it `completed` (result in `jobs.result_json`) or `failed`.
4. Client polls `GET /api/v1/jobs/{id}` until `status` is terminal.

## Run locally
```bash
cd services/api
# 1. apply migrations (needs Postgres + PostGIS for the full 0001 schema)
alembic upgrade head
# 2. API
uvicorn app.main:app --reload
# 3. worker (separate terminal) — shares JOB_UPLOAD_DIR + DATABASE_URL with API
python -m app.worker
```

## Config
- `JOB_UPLOAD_DIR` — dir shared by API + worker (default `<temp>/carbonscan-jobs`).
- `DATABASE_URL` — same Postgres for API + worker.
- `ML_DIR` / `ML_PYTHON` — override ML venv auto-detection if needed.

## Deploy (Phase 2 → 3)
- **Phase 2 (single host):** API + worker on the same box/volume; the local
  `JOB_UPLOAD_DIR` handoff works. Run 1+ workers (`python -m app.worker`).
- **Phase 3 (scale-out):** replace `job_input.save_job_input` with Supabase
  Storage upload and have the worker download by object key. Then the worker
  can run anywhere (e.g. RunPod GPU). Swap `DbJobStore` for a `PgmqJobStore`
  only if DB-as-queue contention becomes a bottleneck — same `JobStore` API.

## Known limits (MVP)
- No progress streaming (`progress` stays 0→100); add stage updates later.
- No cancel endpoint yet (`cancelled` status exists in the schema).
- Rate limiting not wired — add before public exposure.
