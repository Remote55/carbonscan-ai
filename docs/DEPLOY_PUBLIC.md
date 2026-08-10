# Deploying a permanent backend

Written for the state the repository is in after Phase B. It replaces nothing in
`DEPLOYMENT.md`; that file still describes the tunnel-and-launcher setup used
for the competition, which continues to work.

**What is not verified here.** The image in `services/api/Dockerfile` has been
reviewed and its dependency set is checked by
`services/ml/tests/test_runtime_import_surface.py`, but it has **not been
built** — no Docker daemon was available on the machine that wrote it. Treat the
first `docker build` as part of the work, not a formality.

## What changed in Phase B

| | before | now |
|---|---|---|
| ML pipeline in the image | absent — every analysis failed | copied in, one interpreter |
| torch in the image | would have been ~2 GB | not installed; tlsep needs no GPU |
| provenance | shelled to `git` *after* computing, so a container failed at the end of every run | baked at build time, resolved before the first stage |
| upload rate limit | only with demo mode **on** | always |
| upload size cap | 500 MB with demo mode off | the smaller of the two caps, always |
| PLY vertex cap | only with demo mode on | always |
| job uploads | never deleted | deleted after each job, plus a 24 h sweep |

## Build

Context is the repository root, not `services/api`.

```bash
docker build -f services/api/Dockerfile --build-arg GIT_COMMIT=$(git rev-parse HEAD) --build-arg GIT_DIRTY=$(test -z "$(git status --porcelain)" && echo false || echo true) -t treeq-api .
```

`GIT_COMMIT` is not optional. A container has no `.git`, and `process_points`
refuses to start a run it cannot attribute — deliberately, because
`metadata.git_commit` is displayed as provenance. Omit it and the first request
fails immediately with a message naming the variable, which is the intended
behaviour and not a bug to work around.

`GIT_DIRTY` defaults to `true`. "Nobody recorded whether the checkout was clean"
and "the checkout was clean" are different claims, and only the build knows
which one is true.

## Run

```bash
docker run -p 8000:8000 -e TREEQ_DEMO_MODE=false treeq-api
```

Then check both:

```bash
curl -fsS http://localhost:8000/health
```

```bash
curl -fsS http://localhost:8000/api/v1/health/pipeline
```

The second one is the one that matters. `/health` only says uvicorn is up; the
old image passed it while every analysis failed. `/api/v1/health/pipeline`
imports the ML orchestrator in its runtime and returns the pipeline version, or
503s. It was added in Phase B — before it, the only probe that checked this was
gated behind demo mode, which a public deployment turns off.

## Settings for a public deployment

| variable | value | why |
|---|---|---|
| `TREEQ_DEMO_MODE` | `false` | no token gate; the caps and the rate limit apply regardless |
| `TREEQ_DEMO_TOKEN` | unset | only read when demo mode is on |
| `RATE_LIMIT_UPLOAD` | `5` (default) | per client per minute, on a route that runs a subprocess |
| `TRUST_PROXY_HEADERS` | **`true`** | **set this.** Railway, Fly, HF Spaces and Cloudflare all terminate the connection, so the socket peer is the proxy — leave it off and every caller in the world shares one rate-limit bucket. Leave it **off** when nothing sits in front, because the header is caller-controlled and would otherwise be a free reset |
| `MAX_CONCURRENT_ANALYSES` | `2` (default) | analyses in flight at once, across all callers. The rate limit bounds how often ONE caller may ask; this bounds how much work exists. Raise only with the host's RAM in hand — each slot holds an upload in memory plus a pipeline subprocess |
| `TREEQ_DEMO_MAX_UPLOAD_SIZE_MB` | `100` (default) | the effective cap in every mode; ingestion buffers about twice this |
| `TREEQ_DEMO_MAX_POINTS` | `2_000_000` (default) | checked from the PLY header before any work starts |

On the web side, set `NEXT_PUBLIC_API_URL` to the backend origin and leave
`NEXT_PUBLIC_DEMO_TOKEN` **unset**. With demo mode off the API asks for no
token, so publishing one buys nothing and, unlike the tunnel token, it never
rotates.

## Where to host it

Hugging Face Spaces (Docker SDK) is the strongest genuinely free option: 16 GB
RAM, no card required, and it sleeps after about 48 hours idle rather than 15
minutes. The trade is a `*.hf.space` hostname and a cold start after sleep.

Railway or Fly.io are roughly $5/month and give a stable hostname and no sleep.
Worth it only once somebody outside the team is relying on the URL.

Neither needs a GPU. The production wood/leaf backend is tlsep — PCA over
KD-tree neighbourhoods, pure numpy.

## Still open

- The image is unbuilt (see the note at the top).
- `/upload/analyze` remains unauthenticated by design, so the caps above are the
  only thing standing between a public URL and the instance. They are now
  enforced in every mode, and `services/api/tests/test_public_deployment_limits.py`
  fails if any of them is ever put back behind a mode flag.
- The async job queue that used to be listed here has been removed rather than
  finished. Nothing called it, no deployment started its worker, and
  `/jobs/analyze` answered 202 "queued" for work that could not run.
  `/upload/analyze` is synchronous and is the path this service offers.
