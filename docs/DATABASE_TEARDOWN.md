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

## Open security item: `spatial_ref_sys`

Supabase's advisor reported three tables with Row Level Security disabled. The
teardown removed two (`alembic_version`, `species_db`). One is left, and it
**cannot be fixed from any interface this project has**.

### What is actually exposed

Measured, not assumed:

```
table owner                supabase_admin
anon    SELECT ✓  INSERT ✓  UPDATE ✓  DELETE ✓
authenticated  same
```

PostGIS is installed in `public`, which is the schema PostgREST exposes, so
`spatial_ref_sys` is reachable over the REST API with the anon key. Reading it
matters to nobody — it is the EPSG registry, ~8,500 rows of public reference
data. **Writing to it does matter:** an anon caller can corrupt or empty the
table, and every `ST_Transform` in the project then fails or returns wrong
coordinates, silently. Nothing uses PostGIS today, so nothing breaks today —
but this is the table the georeferencing work would depend on.

### Why it cannot be fixed here

Every route is blocked by ownership. The connection available to this project —
and to the dashboard's SQL editor — is `postgres`, not the owner.

| attempt | result |
|---|---|
| `alter table public.spatial_ref_sys enable row level security` | `ERROR 42501: must be owner of table spatial_ref_sys` |
| `revoke insert, update, delete on public.spatial_ref_sys from anon, authenticated` | **reports success and changes nothing** |
| `alter extension postgis set schema extensions` | needs extension ownership, and PostGIS does not support `SET SCHEMA` |
| `drop extension postgis` | needs extension ownership |

The revoke is the one to watch. Postgres only revokes grants the calling role
issued, and `pg_class.relacl` shows every grant here was issued by
`supabase_admin`:

```
anon=arwdDxtm/supabase_admin
authenticated=arwdDxtm/supabase_admin
```

So the statement is legal, affects nothing, and returns success. A migration
named `revoke_write_on_spatial_ref_sys` is recorded in this project's Supabase
migration history and **did nothing** — it is left in place rather than deleted,
because rewriting migration history to hide a mistake is worse than the mistake,
but do not read it as a fix.

### What can be done

1. **Leave it.** Nothing reads or writes PostGIS in this project. Revisit before
   any georeferencing work goes live, because that work makes the table load-
   bearing.
2. **Drop PostGIS.** `drop extension postgis cascade` removes the table and the
   advisory together — no table uses a geometry column any more. It also needs
   ownership, so it would have to go through Supabase support, and it gives up
   the extension that georeferencing would need back.
3. **Ask Supabase support** to move PostGIS into the `extensions` schema, which
   already exists on this project. Out of `public`, PostgREST stops exposing it
   and the advisory resolves properly. This is the real fix.

`public.users` has RLS enabled already.

## If a database is wanted again

Persisting an analysis so a user can return to it is a real gap — today a
refresh loses the result. It does not need any of the schema above: the result
is a JSON document, and the thing to decide first is ownership, because
`POST /upload/analyze` is deliberately unauthenticated.

Georeferencing is the separate prerequisite for anything spatial: read the CRS
from LAS/LAZ headers, transform to WGS84, and ask for a plot origin when a PLY
carries none.
