"""
Fashion Radar — daily data refresh.

Calls the Google Gemini API (free tier, Google AI Studio) with Google Search
grounding to find upcoming fashion events and creatives currently looking
for a magazine to collaborate with, then writes the results to data.json in
the schema the site reads.

This runs on Google's free tier: no credit card needed, and one request a
day is far below any free-tier limit. Get a key at https://aistudio.google.com
(API Keys in the left sidebar) — takes about a minute, Google account only.

Run manually:    python fetch_data.py
Run on schedule: see .github/workflows/daily-refresh.yml
"""

import json
import os
import re
from datetime import date

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# If this model name 404s, check the current free-tier Flash models at
# https://ai.google.dev/gemini-api/docs/models and swap it in here — Google
# renames/rotates these every few months.
MODEL = "gemini-2.5-flash"

SCHEMA_NOTE = """
Return ONLY valid JSON (no markdown fences, no commentary) matching this shape:

{
  "generated_on": "YYYY-MM-DD",
  "events": [
    {
      "name": "string",
      "place": "City, Country",
      "date": "human readable date or range",
      "tag": "runway" | "popup" | "meetup",
      "tagLabel": "Runway" | "Pop-up" | "Meetup",
      "note": "one sentence, under 25 words",
      "link": "https://... (the actual source page you found)",
      "initial": "two letters",
      "color": "#hex"
    }
  ],
  "collaborators": [
    {
      "name": "role + name or handle, e.g. 'Photographer \u2014 @handle'",
      "place": "City, Country if known, else 'Unknown'",
      "date": "how recent, e.g. 'Posted 2 days ago'",
      "tag": "collab",
      "tagLabel": "Seeking outlet",
      "note": "one sentence on what they're looking for, under 25 words",
      "link": "https://... (the actual post you found)",
      "initial": "two letters",
      "color": "#hex"
    }
  ]
}

Rules:
- Only include items you actually found via search, with a real URL you can point to.
  Never invent an entry, a name, or a link.
- If you find fewer than 5 events, or 0 collaborator posts, return fewer \u2014 do not pad the list.
- events: only things happening in the next 60 days from today.
- collaborators: only posts from roughly the last 14 days.
"""


def fetch():
    today = date.today().isoformat()

    prompt = f"""Today's date is {today}.

Search the web for two things:

1. Upcoming fashion events worldwide in the next 60 days: runway shows,
   pop-up shows, and designer meetups. Don't just default to the big four
   fashion weeks \u2014 include regional and independent events too if you find
   real, dated ones.

2. Photographers, designers, or other creatives who have recently posted
   publicly (e.g. on Threads, X, personal sites, forums, or anything indexed
   by search) saying they're looking for a magazine or publication to
   collaborate with or publish their work \u2014 for example, someone with
   fashion week accreditation who needs an outlet.

{SCHEMA_NOTE}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )

    text = response.text.strip()

    # Strip stray markdown fences in case the model adds them anyway
    text = re.sub(r"^```json\s*|\s*```$", "", text)

    data = json.loads(text)

    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)

    print(
        f"Saved {len(data.get('events', []))} events and "
        f"{len(data.get('collaborators', []))} collaborator posts."
    )


if __name__ == "__main__":
    fetch()
