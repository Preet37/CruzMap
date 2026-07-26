# CruzSurge 🌊

**A natural-language coastal erosion simulator for West Cliff Drive, Santa Cruz, driven entirely by Gemma 4's native tool calling.**

Type a storm scenario in plain English, like *"a category 5 hurricane hits at king tide with no seawall,"*
and watch a live cliff/ocean simulation react: waves grow, the seawall status updates, and the cliff
visibly erodes until the road is at risk or gone. Every parameter change on screen is a real,
autonomous function call made by `gemma4:latest` running 100% locally via Ollama. No cloud API, no
internet dependency.

Built for the **CruzHacks "Build with Gemma" hackathon (Autonomous Agent Track)**.

## What this is, and what it isn't

This is not a replacement for engineering-grade coastal modeling, and it doesn't try to be. The
erosion math is a small, transparent, illustrative heuristic, not a validated physical model. City
engineers and firms already have far more rigorous tools for that work, and they should keep using
them.

What CruzSurge actually is: a communication tool. Real coastal engineering reports are static,
expensive to produce, and written for other engineers. A resident, a city council member, or a
student cannot easily ask "what if" and see an answer. CruzSurge lets anyone type a plain-English
scenario and immediately see the qualitative shape of the tradeoff between tide, storm intensity, and
coastal defenses, grounded in real, verified facts about their own street.

## Why this matters beyond one road

West Cliff Drive is the concrete example, chosen because it is real, well-documented, and
high-stakes for Santa Cruz right now. But the reusable part of this project isn't the cliff. It's the
pattern: a person describes intent in plain English, a local Gemma 4 agent autonomously decides which
functions to call to configure a live system, and the system responds. That pattern is not specific to
coastal erosion. The same architecture (natural language in, autonomous tool calls out, a live system
that reacts) could sit in front of a transit planning tool, a wildfire risk model, a water usage
dashboard, or any other public-facing system a city or campus wants ordinary people to actually be
able to use. West Cliff Drive is the demo. The agent pattern is the point.

## The record, verified

- **~30 months (nearly 2 years)**: how long a block of West Cliff Drive stayed closed after the
  January 2023 atmospheric river storms damaged the seawall and roadway.
  ([Lookout Santa Cruz](https://lookout.co/city-to-reopen-part-of-west-cliff-to-two-way-traffic-after-a-near-two-year-closure), [ABC7](https://abc7news.com/post/west-cliff-drive-reopens-santa-cruz-2-year-closure-winter-storm-damage/17519748/))
- **944/960 West Cliff Drive**: sites of an emergency-declared sinkhole and seawall failure, repaired
  with an underdrain system and 450 cubic yards of slurry-cement backfill.
  ([City of Santa Cruz CEQA filing](https://ceqanet.lci.ca.gov/2024100649))
- **~$1.8M, construction targeting 2027**: the city's plan to relocate roughly 400-600 ft of road and
  the pedestrian path 50-60 ft inland into Lighthouse Field State Beach, because the current
  alignment can't be defended long-term.
  ([Lookout Santa Cruz](https://lookout.co/city-of-santa-cruz-eyes-2027-construction-for-partial-west-cliff-drive-roadway-path-relocation/story), [Santa Cruz Local](https://santacruzlocal.org/2024/11/20/5-year-west-cliff-plan/))

## How it works

```
"a category 5 hurricane hits at king tide, no seawall"
                    │
                    ▼
   Gemma 4 (gemma4:latest, 8B, Q4_K_M) via Ollama, native tool calling, text-only
                    │
   ├─ set_tide_level(level)
   ├─ update_wave_kinematics(amplitude, frequency)
   ├─ toggle_infrastructure(defense_type, active)      [only if defenses are mentioned]
   └─ calculate_erosion_rate(simulated_hours)
                    │
                    ▼
   simulation state (tide, waves, defenses, cumulative erosion %)
                    │
                    ▼
   self-contained HTML5 canvas: animated ocean, receding cliff, road, seawall
```

This is a genuine agentic loop (see `agent/cruzsurge_agent.py`). Gemma decides, per scenario, which
of the four tools to call and with what arguments, including whether to touch coastal defenses at
all, and how many hours to simulate. The erosion calculation itself (`_erosion_model`) is deliberately
kept outside the model's control, so the simulation stays physically sane no matter what Gemma is
asked to do to it.

The page also has a second, faster interaction path that needs no AI call at all: draggable sliders
and toggles that mutate the live canvas instantly, plus a continuously running client-side clock so
erosion accrues in real time based on whatever the current settings are. Gemma's job is turning
English into a scenario; the moment-to-moment sandbox play doesn't need to wait on it.

Responses run with `think=False` by default (about 7 to 10 seconds) for a snappy, interactive feel. A
"Fast mode" toggle lets you re-enable Gemma's full chain-of-thought reasoning trace when you want to
see it, tucked behind an opt-in disclosure so it never gets in a regular user's way.

## Project layout

```
agent/cruzsurge_agent.py   # Gemma 4 tool-calling agent for the coastal simulator (the core)
server.py                   # thin Flask API (/api/run, /api/state, /api/reset) around the agent
web/index.html               # the entire user-facing app: custom UI, canvas renderer, JS client
agent/cruzguard_agent.py    # earlier prototype: same agent pattern, applied to photo hazard-triage
app/                          # CruzGuard's Streamlit dashboard (kept as a secondary, working prototype)
data/                        # CruzGuard's demo photos/locations (unused by CruzSurge)
```

The user-facing app is a single self-contained HTML page. No build step, no framework, no external
libraries beyond two Google Fonts, just `fetch()` calls to the Flask backend. Nothing about the
agent's internals (code, terminal, raw model output) is ever shown by default. The "Show Gemma 4's
agent reasoning and tool calls" disclosure is opt-in, for anyone who wants to verify the tool calls
are real.

## Running it

Requires [Ollama](https://ollama.com) with `gemma4:latest` pulled locally (`ollama pull gemma4`).

```bash
pip install -r requirements.txt
python3 server.py
# open http://localhost:8600
```

Try the four presets, the "real-world calibration" card (recreates the Jan 2023 storm conditions), or
drag the sliders directly and watch the cliff respond in real time. Type your own scenario, for
example *"a mild winter storm at low tide with the seawall up"* versus *"a catastrophic category 5
hurricane at king tide with no coastal defenses, run 72 hours,"* and compare how differently the
cliff, road, and warning states behave.

## Why Gemma 4

- **Native tool calling** is the entire mechanism, not a demo feature bolted on. Gemma reads an
  unstructured English sentence and decides which structured simulation functions to call, with what
  arguments, including judgment calls like whether defenses were mentioned at all.
- **Runs fully offline** via Ollama on Apple Silicon. No API key, no per-request cost, no
  connectivity requirement.
- **`agent/cruzguard_agent.py`** demonstrates the same pattern works with **vision** too (photo to
  hazard classification to dispatch ticket), showing the agent architecture generalizes across input
  modalities, not just this one demo.

## Track

Primary: **Autonomous Agent Track** (native function calling drives the entire simulation state).
