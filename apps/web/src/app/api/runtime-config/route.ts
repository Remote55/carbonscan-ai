/**
 * What backend this deployment was built against.
 *
 * NEXT_PUBLIC_* values are inlined when the site is built, so changing one on
 * Vercel does nothing until a redeploy finishes. The launcher publishes a fresh
 * tunnel URL that way on every Auto run, and the previous script simply ran the
 * commands and announced success - which is how the site spent a day serving a
 * hostname that had stopped resolving, with nothing on screen to say so.
 *
 * This route is how that step proves itself: the launcher polls it until the
 * deployed site reports the endpoint it just published, and only then calls the
 * demo ready. It is also the fastest way to answer "which backend does the
 * live site think it has" when something looks wrong.
 *
 * The token is never returned. Whether one was configured is enough to tell a
 * half-finished publish from a complete one.
 */
export const dynamic = 'force-dynamic';

export function GET(): Response {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? null;
  const hasToken = (process.env.NEXT_PUBLIC_DEMO_TOKEN ?? '').length > 0;

  return Response.json(
    { apiUrl, hasToken },
    { headers: { 'cache-control': 'no-store' } },
  );
}
