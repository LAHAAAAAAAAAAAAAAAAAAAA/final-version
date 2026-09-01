# Fashion Radar — daily auto-refresh setup (free)

This turns the static prototype into a site that refreshes itself once a
day, using Google's Gemini API — which has a genuine ongoing free tier, not
just a trial credit. It's also installable as an app on phones and
desktops. The files:

- `index.html` — the site (reads `data.json`, shown here as fallback data
  until the first refresh runs)
- `fetch_data.py` — calls the Gemini API with Google Search grounding,
  writes `data.json`
- `.github/workflows/daily-refresh.yml` — runs the script every day for free
- `requirements.txt` — the one Python dependency
- `manifest.json`, `sw.js`, `icons/` — make the site installable as an app
  (see "Sharing it as an installable app" below)

## Why Gemini instead of Claude for this part

Anthropic's API only gives a one-time ~$5 trial credit, then bills per use.
Google's Gemini API (via Google AI Studio) has an actual free tier: no
credit card, and a daily request limit generous enough that one run a day
never comes close to it. That makes it the right fit for a background job
like this one. You're still using Claude for everything else in this
chat — this is just the one small, always-on piece that benefits from being
on a free key.

## What this actually does (read this first)

- `fetch_data.py` runs once a day, gets a snapshot from a search, and stops.
  It is not a live, always-on crawler.
- "Search the whole internet and social media" isn't something any API
  does literally. Google Search grounding covers publicly indexed pages —
  including some public social posts, but not a live feed of
  Instagram/Threads/TikTok, which don't offer open search access to outside
  apps. Expect the Events tab to be reliably good, and the Collaborators tab
  to be a smaller, patchier signal.
- Free-tier model names and limits shift over time. If `fetch_data.py`
  errors with a "model not found" message, open
  https://ai.google.dev/gemini-api/docs/models, find the current free
  Flash model name, and swap it into the `MODEL` line near the top of the
  script.

## Setup (about 10 minutes, no local coding required)

1. **Create a free GitHub account** if you don't have one, and create a new
   repository (public or private — either works with GitHub Pages).

2. **Upload everything** to the repo, keeping the folder structure:
   `index.html`, `fetch_data.py`, `requirements.txt`, `manifest.json`,
   `sw.js`, the `icons/` folder, and the `.github/workflows/daily-refresh.yml`
   file (GitHub's web uploader keeps folder paths if you drag the whole
   project folder in).

3. **Get a free API key**: go to https://aistudio.google.com, sign in with
   any Google account, click *Get API key* in the left sidebar, then
   *Create API key*. No credit card, no billing setup required for the free
   tier.

4. **Add the key to GitHub** so the workflow can use it without it being
   public: in your repo, go to *Settings → Secrets and variables → Actions →
   New repository secret*. Name it `GEMINI_API_KEY` and paste the key as
   the value.

5. **Turn on GitHub Pages**: *Settings → Pages → Deploy from branch → main →
   / (root)*. GitHub will give you a URL like
   `https://yourusername.github.io/fashion-radar/` — that's your live app.

6. **Run it once by hand**: go to the *Actions* tab, click *Daily refresh* in
   the sidebar, then *Run workflow*. After it finishes (about 30-60 seconds),
   `data.json` will appear in your repo and the site will show real results.

From here it runs itself: the workflow fires automatically every day at
06:00 UTC (edit the `cron` line in the workflow file to change the time),
searches, and commits a fresh `data.json`. The site always reads whatever
the latest file says, so it updates without you touching anything, and it
costs nothing to keep running.

## The "Refresh now" button

The site has a manual refresh button that anyone who opens the app can
use — including your friend. It doesn't talk to GitHub directly; it calls
a small, free Cloudflare Worker that holds your GitHub token privately and
enforces a cooldown, so no matter how many people click it, the actual
refresh only fires at most once per cooldown window (an hour, by default).

**This needs a one-time setup of its own** — see
`cloudflare-worker/README.md` in this project for the full walkthrough
(about 10 minutes, dashboard only, no coding). Until you complete that
setup, the button will just show a "couldn't reach the refresh service"
message — the daily automatic refresh keeps working regardless.

## Sharing it as an installable app

The site is a Progressive Web App, so anyone you send the link to can
"install" it without any app store:

- **iPhone (Safari)**: open the link → Share button → *Add to Home Screen*
- **Android (Chrome)**: open the link → the browser will usually offer an
  *Install app* / *Add to Home screen* prompt on its own; otherwise it's in
  the ⋮ menu
- **Desktop (Chrome/Edge)**: an install icon appears in the address bar

Once installed, it opens full-screen with its own icon, like a regular app —
while still just being your GitHub Pages site under the hood, so it keeps
updating daily the same as always, and the refresh button works the same
for your friend as it does for you. This isn't the same as a real App
Store/Play Store app (no listing, no push notifications, no offline data
beyond the last thing it loaded) — but it costs nothing, needs no developer
account, and is genuinely how you'd share this with a friend.

## Adjusting what it searches for

Open `fetch_data.py` and edit the `prompt` string — e.g. narrow it to
specific cities, add "sustainable fashion" as a filter, or ask it to also
look for casting calls. The JSON schema below the prompt tells the model
exactly what shape to return, so keep that part intact when you edit.

## If something looks off

- **Empty or missing data.json**: check the Actions tab for a failed run —
  usually an invalid API key, or the model name in `fetch_data.py` needing
  an update (see above).
- **JSON parsing errors in the logs**: the model occasionally wraps its
  answer in explanation text despite instructions not to; re-running usually
  fixes it, and you can make the prompt stricter if it keeps happening.
- **Nothing shows in Collaborators**: expected fairly often, given the
  search-access limits described above — it's not a bug.
