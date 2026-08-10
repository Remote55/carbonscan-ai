# The database this service no longer has

> [!IMPORTANT]
> The API code that talked to Postgres is gone. **The tables in Supabase are
> not.** Nothing in this repository can drop them any more — alembic was removed
> with the rest — so the SQL below is the record of what is there and how to
> clean it up. Run it yourself when you are ready; it is not run by anything.

## What happened

The service had a Postgres layer: a SQLAlchemy async engine, alembic, and six
tables. Not one of them had a reader or a writer.

| table | why it went |
|---|---|
| `jobs` | backed the async analysis queue. Nothing called that queue and no deployment started its worker; removed, with the queue, in commit `536773f`. |
| `trees` | `location` was `GEOMETRY(POINT, 4326) NOT NULL` — WGS84 latitude and longitude. Nothing in this system produces a geographic coordinate: `load_point_cloud` reads `las.x, las.y, las.z` and discards the CRS, so a tree's position is a mean in the point cloud's own frame. `POST /trees` could not have been written. Removed in `9658f6a`. |
| `transactions` | `tree_id` referenced `trees`. A record of a carbon sale that cannot say which tree was sold is not worth keeping. |
| `users` | written only by `DbJobStore.create`, which went with the queue. Authentication is Supabase's and lives in `auth.users`, a different schema. |
| `plots` | no ORM model, no code, ever. |
| `species_db` | no ORM model, no code. The species data actually used is read from `services/ml/data/species_db.csv` by `app/services/species_catalogue.py`. |

An analysis is now computed and returned in one response. The service stores
nothing between requests, apart from the segmented point cloud, which
`app/services/segmented_cloud_store.py` keeps on local disk for 30 minutes so
the viewer can fetch it.

## What is still in Supabase

Checked on 2026-08-10 against project `Carbon_project`:

| table | rows |
|---|---|
| `public.users` | **2** |
| `public.jobs` | 0 |
| `public.trees` | 0 |
| `public.transactions` | 0 |
| `public.plots` | 0 |
| `public.species_db` | 0 |
| `public.alembic_version` | 0 |
| `public.spatial_ref_sys` | PostGIS's own; leave it alone |

`alembic_version` being empty means the schema was applied through the SQL
editor rather than by `alembic upgrade head` — the guide in
`docs/SUPABASE_SETUP.md` offers both paths and this project took the first.
That is also why migrations `0003` and `0004`, which dropped `jobs` and
`trees`, never ran anywhere.

**`public.users` holds 2 rows.** Read them before dropping the table. Note that
this is the application mirror, not the identities themselves: Supabase Auth
keeps those in `auth.users`, which the SQL below does not touch, so dropping
`public.users` does not delete anyone's login.

## Teardown SQL

Run in the Supabase SQL editor. Reverse dependency order, so the foreign keys
go before the tables they point at.

```sql
-- Check first. This should print zeros for everything except users.
select 'users' as t, count(*) from public.users
union all select 'jobs',         count(*) from public.jobs
union all select 'trees',        count(*) from public.trees
union all select 'transactions', count(*) from public.transactions
union all select 'plots',        count(*) from public.plots
union all select 'species_db',   count(*) from public.species_db;
```

```sql
begin;

drop table if exists public.transactions;
drop table if exists public.trees;
drop table if exists public.jobs;
drop table if exists public.plots;
drop table if exists public.species_db;
drop table if exists public.users;
drop table if exists public.alembic_version;

commit;
```

`spatial_ref_sys` belongs to the PostGIS extension, not to this application.
Leave it, or drop the extension itself with `drop extension postgis cascade` if
nothing else in the project uses it.

## Open security item, unrelated to the teardown

Supabase's advisor reports, at **critical** level, that three tables have Row
Level Security disabled: `spatial_ref_sys`, `alembic_version` and `species_db`.
Anyone holding the anon key can read or modify every row in them. Dropping
`alembic_version` and `species_db` as above removes two of the three.

Do not enable RLS without adding policies — that blocks all access rather than
restricting it. The advisor's suggested statements are:

```sql
alter table public.spatial_ref_sys  enable row level security;
alter table public.alembic_version  enable row level security;
alter table public.species_db       enable row level security;
```

## If a database is wanted again

Persisting an analysis so a user can return to it is a real gap — today a
refresh loses the result. It does not need any of the schema above: the result
is a JSON document, and the thing to decide first is ownership, because
`POST /upload/analyze` is deliberately unauthenticated.

Georeferencing is the separate prerequisite for anything spatial: read the CRS
from LAS/LAZ headers, transform to WGS84, and ask for a plot origin when a PLY
carries none.
