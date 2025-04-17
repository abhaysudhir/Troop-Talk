# Propagate User's Organization to ask_gpt

A minimal plan to send the authenticated user's organization (Troop Number) in every `/api/ask_gpt` request.

## 📋 To-Dos

### 1. Clerk Dashboard
- [x] Enable **Organizations** in the Clerk Dashboard.
- [x] Create or invite test users into a "Troop" organization. - done for abhaysudhir@Icloud.com

### 2. Environment Setup
- [ ] Add to `.env.local`:
  - `CLERK_ORG_ENABLED=true`
  - `NEXT_PUBLIC_CLERK_FRONTEND_API=<your-front-end-api>`
  - `CLERK_SECRET_KEY=<your-backend-secret>`
- [ ] Restart the dev server.

### 3. Frontend (React/Vite)
- [ ] Ensure `<ClerkProvider>` wraps `<App />` (already in `main.tsx`).
- [ ] Import Clerk hooks:
  ```ts
  import { useAuth, useOrganization } from "@clerk/clerk-react";
  ```
- [ ] In `Chat.tsx` `handleSend`:
  ```ts
  const { getToken } = useAuth();
  const { organization } = useOrganization();
  const token = await getToken();
  const orgId = organization?.id;
  const response = await fetch(`${import.meta.env.VITE_DO_BACKEND_URL}/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
    body: JSON.stringify({ question: input, organizationId: orgId }),
  });
  ```

### 4. Backend (Python ask_gpt.py)
- [ ] Extract and parse `Authorization` header:
  ```py
  token = request.headers.get("Authorization", "").split("Bearer ")[-1]
  ```
- [ ] Verify token and extract org with Clerk:
  ```py
  from clerk import Clerk
  clerk = Clerk(secret_key=os.environ["CLERK_SECRET_KEY"])
  session = clerk.sessions.verify_token(token)
  org_id = session.organization_id
  ```
- [ ] Add `org_id` to your OpenAI call or audit logs.

## 🚀 Next Steps
1. Add unit tests mocking Clerk session in backend.
2. Expand prompt conditioning by organization in front-end or backend.
3. Document edge cases (no org, stale token).
4. Roll out in staging and verify per-org logging.

---

_Keep it simple for now; we can expand each section with code snippets and detailed tests later._ 