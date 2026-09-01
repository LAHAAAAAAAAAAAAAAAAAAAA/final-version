# Public refresh relay (Cloudflare Worker)

This is what makes the "Refresh now" button safe to expose to everyone,
including your friend. It's a small piece of code that runs on Cloudflare's
free tier (no credit card), sits between the button and GitHub, and:

- holds your GitHub token privately — it never appears in `index.html` or
  anywhere a visitor's browser can see it
- enforces a cooldown, so no matter how many people click the button, the
  actual GitHub workflow (and your Gemini API usage) only fires at most
  once per cooldown window — default one hour

## Setup (about 10 minutes, dashboard only — no CLI needed)

1. **Create a free Cloudflare account** at https://dash.cloudflare.com/sign-up
   (email + password, no credit card).

2. **Create the Worker**: in the dashboard, go to *Workers & Pages* →
   *Create* → *Create Worker*. Give it any name (e.g.
   `fashion-radar-refresh`) and deploy the default template — you'll
   replace the code next.

3. **Paste the code**: open the Worker, click *Edit code* (the Quick Edit /
   code editor view), delete the placeholder content, and paste in the
   contents of `worker.js` from this folder. Click *Deploy*.

4. **Add a KV namespace** (this is what tracks the cooldown):
   - *Workers & Pages* → *KV* → *Create a namespace* → name it anything,
     e.g. `fashion-radar-cooldown`
   - Back in your Worker → *Settings* → *Variables* → *KV Namespace
     Bindings* → *Add binding*
   - Variable name: `COOLDOWN_KV` (must match exactly — the code refers to
     this name) → select the namespace you just created → *Save*

5. **Add your GitHub token as a secret**:
   - First create the token itself: https://github.com/settings/tokens →
     *Fine-grained tokens* → *Generate new token* → *Repository access:
     Only select repositories* → pick this repo → *Permissions* → *Actions:
     Read and write* → *Generate*, then copy it
   - In your Worker → *Settings* → *Variables* → *Environment Variables* →
     *Add variable* → name it `GITHUB_TOKEN`, paste the token as the value,
     and toggle **Encrypt** (this is what keeps it a proper secret, not
     just a plain variable) → *Save*

6. **Add the plain config variables** the same way (no encryption needed
   for these — they're not sensitive):
   - `OWNER` → your GitHub username
   - `REPO` → your repo name
   - `WORKFLOW_FILE` → `daily-refresh.yml`
   - `COOLDOWN_MINUTES` → `60` (or whatever you'd prefer — this is how
     often the button can actually trigger a real run)

7. **Copy your Worker's URL**: shown at the top of the Worker's page,
   something like `https://fashion-radar-refresh.yourname.workers.dev`.

8. **Paste that URL into the site**: open `index.html`, find the line
   `const REFRESH_WORKER_URL = "..."` near the bottom, and replace the
   placeholder with your real Worker URL. Re-upload/commit `index.html` to
   your GitHub repo.

That's it — the button on your live site now calls your Worker, which
calls GitHub, with the cooldown protecting you regardless of who clicks it
or how often.

## Adjusting the cooldown

Change the `COOLDOWN_MINUTES` variable in the Worker's settings any time,
no redeploy needed. Shorter means fresher data on demand but more frequent
Gemini API usage; longer means less cost but a longer wait if someone just
triggered it.

## If something looks off

- **Button always says "couldn't reach the refresh service"**: double-check
  the URL in `index.html` exactly matches your Worker's URL, and that you
  deployed after pasting the code in.
- **"GitHub rejected the request"**: usually the token, owner, or repo
  variable is wrong, or the token's Actions permission isn't set to
  Read and write.
- **Cooldown message never seems to clear**: that's expected behavior, not
  a bug — it means someone (possibly you, on another device) refreshed
  recently.
