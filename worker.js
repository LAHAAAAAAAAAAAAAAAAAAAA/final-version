/**
 * Fashion Radar — public refresh relay.
 *
 * This is the ONLY piece that's allowed to know the GitHub token. It runs
 * on Cloudflare, not in anyone's browser, so the token never reaches a
 * page's source code — anyone who views your site's source sees nothing
 * secret, just a call to this worker's public URL.
 *
 * It exposes one endpoint (POST /) that:
 *  1. Checks a cooldown stored in KV — if someone refreshed recently,
 *     it refuses instead of hitting GitHub again. This is what makes it
 *     safe to let *everyone* click the button: no amount of clicking can
 *     trigger more than one real run per cooldown window.
 *  2. If the cooldown has passed, tells GitHub to run the daily-refresh
 *     workflow right now.
 *
 * Setup: see README.md in this folder.
 */

const COOLDOWN_KEY = "last_triggered";

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", ...corsHeaders() },
  });
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders() });
    }
    if (request.method !== "POST") {
      return json({ ok: false, message: "Use POST." }, 405);
    }

    const cooldownMinutes = parseInt(env.COOLDOWN_MINUTES || "60", 10);
    const now = Date.now();

    const last = await env.COOLDOWN_KV.get(COOLDOWN_KEY);
    if (last) {
      const elapsedMs = now - parseInt(last, 10);
      const remainingMs = cooldownMinutes * 60 * 1000 - elapsedMs;
      if (remainingMs > 0) {
        const remainingMin = Math.max(1, Math.ceil(remainingMs / 60000));
        return json(
          {
            ok: false,
            cooldown: true,
            message: `Someone already refreshed this recently \u2014 try again in about ${remainingMin} min.`,
          },
          429
        );
      }
    }

    const url = `https://api.github.com/repos/${env.OWNER}/${env.REPO}/actions/workflows/${env.WORKFLOW_FILE}/dispatches`;

    let ghRes;
    try {
      ghRes = await fetch(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GITHUB_TOKEN}`,
          Accept: "application/vnd.github+json",
          "User-Agent": "fashion-radar-worker",
        },
        body: JSON.stringify({ ref: env.BRANCH || "main" }),
      });
    } catch (e) {
      return json({ ok: false, message: "Could not reach GitHub." }, 502);
    }

    if (!ghRes.ok) {
      return json(
        { ok: false, message: `GitHub rejected the request (${ghRes.status}).` },
        502
      );
    }

    await env.COOLDOWN_KV.put(COOLDOWN_KEY, String(now));
    return json({ ok: true, message: "Refresh triggered." }, 200);
  },
};
