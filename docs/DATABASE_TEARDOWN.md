# The database this service no longer has

> [!IMPORTANT]
> **Done, apart from one table.** On 2026-08-10 the six unused tables were
> dropped from the `Carbon_project` Supabase project. `public.users` was left
> standing on purpose — see [What is still there](#what-is-still-there).

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

## What was dropped

Applied 2026-08-10 to `Carbon_project` as the Supabase migration
`drop_unused_application_tables`, in dependency order:

```sql
drop table if exists public.transactions;   -- 0 rows
drop table if exists public.trees;          -- 0 rows
drop table if exists public.jobs;           -- 0 rows
drop table if exists public.plots;          -- 0 rows
drop table if exists public.species_db;     -- 5 rows, duplicated in git
drop table if exists public.alembic_version;-- 1 row, read '0001'
```

`species_db` held the five seed species, which are the same five in
`services/ml/data/species_db.csv` — the copy the code actually reads. Nothing
was lost that is not version-controlled.

`alembic_version` read `0001`, so the initial schema **was** applied through
`alembic upgrade head`; `0002` never ran, and neither did `0003` or `0004`.

> An earlier revision of this file said `alembic_version` was empty and
> concluded the schema had been applied through the SQL editor. That was wrong.
> The row counts it quoted were wrong too — they came from `list_tables`, which
> reports the query planner's `reltuples` estimate rather than a count. `users`
> was given as 2 and is 5; `species_db` as 0 and was 5. Anything deciding
> whether to delete data has to come from `count(*)`.

<a id="what-is-still-there"></a>
## What is still there

| table | rows | why it stayed |
|---|---|---|
| `public.users` | **5** | real content, and not all of it the project owner's |
| `public.spatial_ref_sys` | ~8,500 | PostGIS's own reference table |

**`public.users` was not dropped.** It holds five rows, including addresses
belonging to other people, and its `role` column (`auditor` / `community`)
exists nowhere else — those assignments cannot be reconstructed from anything
in the repository.

Dropping it would not lock anyone out: Supabase Auth keeps the identities in
`auth.users`, a different schema, which also holds five rows and is untouched.
Only the roles would go. To drop it anyway:

```sql
select id, email, role, created_at from public.users order by created_at;  -- look first
drop table public.users;
```

`spatial_ref_sys` belongs to the PostGIS extension. No table in this project
uses a geometry column any more — the only geometry types left are PostGIS's
own internal `geometry_dump` and `valid_detail` composites — so the extension
can go with `drop extension postgis cascade`. It was left in place because
georeferencing (below) is the one plausible reason to want a database here
again, and that work would need it back.

## Open security item

Supabase's advisor reported, at **critical** level, three tables with Row Level
Security disabled — anyone holding the anon key could read or modify every row.
The teardown removed two of them (`alembic_version`, `species_db`). One is left:

```
public.spatial_ref_sys    RLS disabled
```

It is PostGIS's static table of coordinate-system definitions. Nothing secret
is in it, and nothing in this project reads it, so the practical exposure today
is that someone with the anon key could corrupt reference data no code uses.
The advisory will keep appearing until it is dealt with, in one of two ways:

```sql
-- Remove it at the root, since no table uses a geometry column any more:
drop extension postgis cascade;
```

```sql
-- Or keep PostGIS and turn RLS on. Note that this table is owned by the
-- extension, and enabling RLS with no policy blocks all access rather than
-- restricting it — add a read policy if anything is ever going to read it.
alter table public.spatial_ref_sys enable row level security;
```

`public.users` has RLS enabled already.

## If a database is wanted again

Persisting an analysis so a user can return to it is a real gap — today a
refresh loses the result. It does not need any of the schema above: the result
is a JSON document, and the thing to decide first is ownership, because
`POST /upload/analyze` is deliberately unauthenticated.

Georeferencing is the separate prerequisite for anything spatial: read the CRS
from LAS/LAZ headers, transform to WGS84, and ask for a plot origin when a PLY
carries none.
