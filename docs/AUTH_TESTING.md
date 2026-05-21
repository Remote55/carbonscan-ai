# 🧪 Testing the Auth Flow Live

> Step-by-step guide to verify Supabase Auth works end-to-end on your local machine.
>
> **Time:** ~10 minutes
> **Prerequisites:** Supabase project set up + `.env` files filled (see [SUPABASE_SETUP.md](SUPABASE_SETUP.md))

---

## Why This Matters

Auth is the **first feature that real users will touch**. If signup or login breaks, no one can use the app. This guide walks you through the full flow:

```
1. Start backend (FastAPI)
2. Start frontend (Next.js)
3. Sign up a test user via UI
4. Confirm email (or skip in dev)
5. Login
6. Visit /dashboard (protected)
7. Verify GET /api/v1/auth/me returns user data
8. Verify auto-sync trigger created public.users row
```

---

## Step 1: Disable email confirmation (dev only)

For local testing without email setup:

1. Go to https://supabase.com/dashboard/project/umuszxwwwxyvqxwhlpxf/auth/providers
2. Click **Email** provider
3. Under "Confirm email" — **turn OFF**
4. Click Save

> ⚠️ Re-enable before production. For now: signed-up users are immediately active.

---

## Step 2: Start Backend

```bash
cd D:\Project_Carbon\services\api

# Activate venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux

# Set encoding (for emoji in startup print)
set PYTHONIOENCODING=utf-8

# Start server
python -m uvicorn app.main:app --reload --port 8000
```

You should see:
```
🌲 Starting CarbonScan AI API v0.1.0 (development)
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Verify:**
- Open http://localhost:8000/docs — Swagger UI
- Open http://localhost:8000/api/v1/health/ready — `{"status":"ok","database":true}`

---

## Step 3: Start Frontend (separate terminal)

```bash
cd D:\Project_Carbon\apps\web

pnpm dev
```

Server runs at http://localhost:3000 — open in browser.

---

## Step 4: Sign Up

1. Navigate to http://localhost:3000/signup
2. Fill the form:
   - **ชื่อ:** Test User
   - **อีเมล:** `test@example.com` (use any real-looking email)
   - **รหัสผ่าน:** `TestPass123` (min 8 chars)
   - **ประเภทผู้ใช้:** เลือก "ชุมชน / เกษตรกร"
3. Click **"สมัครสมาชิกฟรี"**

**Expected:**
- Form submits without error
- If email confirmation OFF → you might be auto-redirected to `/dashboard`
- If email confirmation ON → you see "ตรวจอีเมลของคุณ ✉" message

---

## Step 5: Login (if not auto-logged in)

1. Navigate to http://localhost:3000/login
2. Enter the same email + password
3. Click **"เข้าสู่ระบบ"**

**Expected:**
- Redirect to `/dashboard`
- See "ยินดีต้อนรับ, Test User" with your role displayed

---

## Step 6: Verify Backend Sees You

The Web stores Supabase session in HttpOnly cookies. Backend needs the JWT in Authorization header.

### Option A: Use browser DevTools

1. On `/dashboard`, open DevTools → Console
2. Run:
   ```js
   const { data: { session } } = await window.supabase.auth.getSession();
   console.log(session.access_token);
   ```
   ⚠️ Doesn't work — `supabase` isn't globally exposed. Use Option B.

### Option B: Use the /auth/v1/token endpoint directly

```bash
# Get token via curl (paste your real credentials)
curl -X POST "https://umuszxwwwxyvqxwhlpxf.supabase.co/auth/v1/token?grant_type=password" \
  -H "apikey: sb_publishable_WXo8slEDXGA5He4YcjM4oQ_BsAn1F1j" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\",\"password\":\"TestPass123\"}"
```

Copy the `access_token` from the response (`eyJ...`).

### Then verify backend /me

```bash
# Replace <TOKEN> with access_token from above
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <TOKEN>"
```

**Expected response:**
```json
{
  "id": "abc-uuid-...",
  "email": "test@example.com",
  "name": "Test User",
  "role": "community",
  "created_at": "2026-05-22T...:..."
}
```

---

## Step 7: Verify Auto-Sync to public.users

The trigger `on_auth_user_created` should have inserted a row in `public.users` matching the auth user.

### Option A: Via Supabase Dashboard

1. Go to https://supabase.com/dashboard/project/umuszxwwwxyvqxwhlpxf/editor
2. Click `users` table
3. You should see a row with your test user's id, email, name, role

### Option B: Via psql (if installed)

```bash
psql "postgresql://postgres.umuszxwwwxyvqxwhlpxf:Remote21022549@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres" \
  -c "SELECT id, email, name, role FROM public.users;"
```

### Option C: Via Python (in services/api venv)

```bash
cd services/api
.venv/Scripts/python.exe -c "
import asyncio, asyncpg
async def main():
    conn = await asyncpg.connect(
        host='aws-1-ap-southeast-1.pooler.supabase.com', port=5432,
        user='postgres.umuszxwwwxyvqxwhlpxf', password='Remote21022549',
        database='postgres', statement_cache_size=0)
    rows = await conn.fetch('SELECT id, email, name, role, created_at FROM public.users')
    for r in rows: print(dict(r))
    await conn.close()
asyncio.run(main())
"
```

You should see your test user row.

---

## Step 8: Test Logout

1. On `/dashboard`, open DevTools → Application → Cookies
2. Note the Supabase auth cookies (`sb-<ref>-auth-token`)
3. (No logout button in UI yet — Phase 1 will add one)
4. To manually logout, clear cookies + reload `/dashboard` → redirects to `/login` ✓

---

## ✅ What Success Looks Like

- [ ] Signup form submits successfully
- [ ] Email confirmation (if ON): email arrives within 1 min
- [ ] Login redirects to /dashboard
- [ ] /dashboard shows your name + role
- [ ] /api/v1/auth/me returns user data with valid token
- [ ] /api/v1/auth/me returns 401 without token or with invalid token
- [ ] public.users has the auto-synced row
- [ ] Middleware redirects unauthenticated requests to /login
- [ ] After clearing cookies, /dashboard redirects to /login

---

## 🐛 Common Issues

### "Auth callback failed" after signup
- Email link clicked but session not established
- **Cause:** APP_URL mismatch (link points to wrong domain)
- **Fix:** In Supabase Dashboard → Auth → URL Configuration, add `http://localhost:3000` to "Site URL" and `/auth/callback` to "Redirect URLs"

### Signup succeeds but no row in public.users
- Trigger `on_auth_user_created` not active
- **Fix:** Re-run `services/api/scripts/rls_policies.sql` (it creates the trigger)
- Verify: `SELECT tgname FROM pg_trigger WHERE tgname='on_auth_user_created'`

### /api/v1/auth/me always returns 401
- Token invalid OR backend can't reach Supabase
- **Check:** `curl https://umuszxwwwxyvqxwhlpxf.supabase.co/auth/v1/user -H "Authorization: Bearer <token>" -H "apikey: <publishable-key>"`
- If this works but FastAPI doesn't → check `.env` has correct SUPABASE_URL + ANON_KEY

### Login form just spins, no error
- CORS issue between Web and Supabase
- **Check:** browser DevTools → Network tab → look at the failing request
- **Fix:** In Supabase Dashboard → Auth → URL Configuration, add `http://localhost:3000` to allowed origins

### "User from sub claim in JWT does not exist"
- public.users row missing for the auth user
- **Fix:** Re-run RLS script (creates the trigger to auto-sync) OR manually insert:
  ```sql
  INSERT INTO public.users (id, email, name, role)
  SELECT id, email, raw_user_meta_data->>'name', 'community'
  FROM auth.users WHERE email='test@example.com';
  ```

### CSRF / Cookie not set
- Production-only issue (CSRF) — local dev OK
- **Phase 1 TODO:** Configure cookies with `secure: true`, `sameSite: 'lax'`

---

## 🧹 Cleanup Test Data

After testing, remove test users:

### Via Dashboard
1. Supabase Dashboard → Authentication → Users
2. Find your test user → ⋮ menu → Delete user
3. Trigger ON DELETE CASCADE should remove public.users row too

### Via SQL
```sql
-- Delete from auth (cascades to public.users via FK)
DELETE FROM auth.users WHERE email='test@example.com';
```

---

## 📈 Next: Connect Web → Backend

Once auth works, the next milestone is making Web actually call FastAPI:

1. Web stores Supabase session (already works)
2. Update `apps/web/src/lib/api.ts` to attach `Authorization: Bearer <token>` header
3. Use `useSession()` hook in Client Components to grab the token
4. Test by calling `/api/v1/auth/me` from a Web page

(This will be done in PR #10+ as Phase 1 work.)

---

📖 **Related docs:**
- [docs/SUPABASE_SETUP.md](SUPABASE_SETUP.md) — Initial Supabase setup
- [docs/API.md](API.md) — Full API reference
- [services/api/scripts/rls_policies.sql](../services/api/scripts/rls_policies.sql) — RLS + trigger source
- [apps/web/src/lib/auth.ts](../apps/web/src/lib/auth.ts) — Web auth helpers
- [apps/web/src/middleware.ts](../apps/web/src/middleware.ts) — Route protection
