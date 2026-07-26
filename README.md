# CruzSurge 🌊

**A natural-language coastal erosion simulator for West Cliff Drive, Santa Cruz — driven entirely by Gemma 4's native tool calling.**

Type a storm scenario in plain English — *"a category 5 hurricane hits at king tide with no seawall"* —
and watch a live cliff/ocean simulation react: waves grow, the seawall status updates, and the cliff
visibly erodes until the road is at risk or gone. Every parameter change on screen is a real,
autonomous function call made by `gemma4:latest` running 100% locally via Ollama — no cloud API, no
internet dependency.

Built for the **CruzHacks "Build with Gemma" hackathon (Autonomous Agent Track)**.

## The problem, with real numbers

City planners currently manage coastal erosion along West Cliff Drive with static engineering reports
and expensive modeling software, reacting only after storms cause damage. The numbers are real and
verified:

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

CruzSurge makes the qualitative reasoning behind those decisions — how tide, wave energy, and coastal
defenses trade off against the cliff — interactive and immediate, for planners and the public alike.

## How it works

```
"a category 5 hurricane hits at king tide, no seawall"
                    │
                    ▼
   Gemma 4 (gemma4:latest, 8B, Q4_K_M) via Ollama — native tool calling, text-only
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

This is a genuine agentic loop (see `agent/cruzsurge_agent.py`): Gemma decides, per scenario, which
of the four tools to call and with what arguments — including whether to touch coastal defenses at
all, and how many hours to simulate. The erosion calculation itself (`_erosion_model`) is a small,
transparent, explainable heuristic — wave energy proportional to amplitude² × frequency, boosted by
tide level, dampened by active defenses — not something the model touches directly, which keeps the
simulation physically sane no matter what Gemma is asked to do to it.

Responses run with `think=False` by default (~7-10s) for a snappy, interactive feel; a "Fast mode"
toggle lets you re-enable Gemma's full chain-of-thought reasoning trace when you want to see it.

## Project layout

```
agent/cruzsurge_agent.py   # Gemma 4 tool-calling agent for the coastal simulator (the core)
app/canvas.py               # self-contained HTML5 canvas renderer (ocean/cliff/road/seawall)
app/surge_app.py             # Streamlit dashboard: chat input + live canvas + reasoning trace
agent/cruzguard_agent.py    # earlier prototype: same agent pattern, applied to photo hazard-triage
app/app.py, app/severity.py # CruzGuard's dashboard (kept as a secondary, working prototype)
data/                        # CruzGuard's demo photos/locations (unused by CruzSurge)
```

## Running it

Requires [Ollama](https://ollama.com) with `gemma4:latest` pulled locally (`ollama pull gemma4`).

```bash
pip install -r requirements.txt
streamlit run app/surge_app.py
```

Try the two presets in the sidebar, or type your own scenario — e.g. *"a mild winter storm at low
tide with the seawall up"* vs *"a catastrophic category 5 hurricane at king tide with no coastal
defenses, run 72 hours"* — and watch the cliff respond differently.

## Why Gemma 4

- **Native tool calling** is the entire mechanism, not a demo feature bolted on: Gemma reads an
  unstructured English sentence and decides which structured simulation functions to call, with what
  arguments, including judgment calls like whether defenses were mentioned at all.
- **Runs fully offline** via Ollama on Apple Silicon: no API key, no per-request cost, no
  connectivity requirement.
- **`agent/cruzguard_agent.py`** demonstrates the same pattern works with **vision** too (photo →
  hazard classification → dispatch ticket), showing the agent architecture generalizes across input
  modalities, not just this one demo.

## Track

Primary: **Autonomous Agent Track** (native function calling drives the entire simulation state).
