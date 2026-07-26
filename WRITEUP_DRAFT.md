# CruzSurge: A Natural-Language Coastal Erosion Simulator for Santa Cruz
### Subtitle: Type a storm scenario, watch Gemma 4 autonomously drive a live cliff-erosion simulation

*Track: Autonomous Agent*

## The Problem

Santa Cruz's West Cliff Drive is in an active, well-documented fight against coastal erosion. After
the January 2023 atmospheric river storms, a block of the road stayed closed for **nearly two years**
while the city repaired a sinkhole and seawall failure at 944/960 West Cliff Drive — an emergency
project involving an underdrain system and 450 cubic yards of slurry-cement backfill. The city is now
planning a **~$1.8M project, targeting 2027 construction**, to relocate roughly 400-600 feet of the
road and pedestrian path 50-60 feet inland into Lighthouse Field State Beach, because the current
alignment cannot be defended indefinitely. (Sources: Lookout Santa Cruz, ABC7, Santa Cruz Local, and
the City of Santa Cruz's CEQA filing for the 944/960 West Cliff Drive emergency storm damage project.)

Today, the reasoning behind these decisions — how tide level, storm intensity, and coastal defenses
trade off against cliff stability — lives in static engineering reports and expensive modeling
software, inaccessible to the public and slow for planners to explore interactively. CruzSurge makes
that reasoning immediate: describe a scenario in plain English, and watch a live simulation respond.

## Architecture

CruzSurge has one core loop (`agent/cruzsurge_agent.py`): a natural-language scenario and the current
simulation state go in, `gemma4:latest` (8B, Q4_K_M, served locally via Ollama) is given a system
prompt establishing it as the simulator's operator and four tool schemas — `set_tide_level`,
`update_wave_kinematics`, `toggle_infrastructure`, and `calculate_erosion_rate`. Gemma reads the
scenario and decides, autonomously, which of these to call and with what arguments: it always sets
tide and wave parameters, only touches coastal defenses if the scenario mentions them, and always
finishes by advancing the simulation a scenario-appropriate number of hours. This is a genuine
multi-call agentic turn, not a single classification — the model is making several dependent decisions
in sequence, in a single turn, based on its own read of the scenario.

The erosion calculation itself is a small, transparent heuristic (wave energy proportional to
amplitude² × frequency, boosted by tide level, dampened 45-70% by active defenses, integrated over the
simulated hours) — deliberately not something Gemma computes directly, so the simulation stays
physically sane regardless of what's asked of it. Gemma's role is translation (English → structured
intent), not arithmetic.

The frontend is a self-contained HTML5 canvas (`app/canvas.py`, no external libraries) showing an
animated cross-section: layered sine-wave ocean, a cliff face that visibly recedes as cumulative
erosion increases, cracks that appear and multiply, a seawall block and rip-rap that appear/disappear
with the agent's tool calls, and a shrinking "West Cliff Drive" road strip that displays "ROAD AT
RISK" past 70% erosion and "ROADWAY COLLAPSE" past 95%. Everything is driven by state that Gemma's
tool calls mutated — there is no hard-coded animation independent of the agent's decisions.

By default, responses run with Ollama's `think=False`, giving ~7-10 second turnaround for a snappy,
interactive feel; a toggle re-enables Gemma's full chain-of-thought so the reasoning behind each
scenario can be inspected on demand.

## Why Gemma 4, specifically

Gemma 4's **native tool/function calling** is not a demo feature here — it is the entire mechanism
that turns an unstructured English sentence into a structured, physically-grounded simulation state
change. The model has to make several linked judgment calls per scenario (what tide, what wave
intensity, whether defenses are mentioned at all, how long to run it) and gets all of them right
consistently across very different phrasings, from "a mild winter storm" to "a catastrophic category 5
hurricane... run it for 72 hours." And because it runs **entirely offline** via Ollama on Apple
Silicon, the same architecture could run on a planning department's own hardware with no cloud
dependency or per-query cost — relevant for a tool meant to be explored interactively and often.

## Challenges in a one-day sprint

The project went through two pivots before landing here, and being honest about that is part of the
engineering story. The first concept fused this agent with `lingbot-map`, an open-source streaming 3D
reconstruction model, to turn dashcam video into a navigable 3D flythrough of hazard sites. That
pipeline requires CUDA, FlashInfer, and a from-source Kaolin build — none of which run on the Apple
Silicon hardware available for this sprint — and it fundamentally needs continuous moving-camera
video, which we didn't have a fast, honestly-licensed source for. Rather than burn the sprint's
remaining hours on an infeasible dependency, we cut it and built a photo-based civic hazard-triage
agent instead (`agent/cruzguard_agent.py`, kept in this repo as a working secondary prototype: same
Gemma 4 vision + tool-calling pattern, applied to street-hazard photos). That version worked, but
static photo pins undersold what an *interactive*, reactive agent could demonstrate.

CruzSurge is the result of taking that feedback seriously: instead of Gemma reacting to a fixed photo,
it reacts live to open-ended natural language, with a visual payoff (a cliff eroding in real time) that
is immediately legible without needing any technical explanation.

## Why this is a strong foundation, not just a demo

The agent core is fully decoupled from the visual layer: any frontend that can render the four state
variables (tide, wave amplitude/frequency, defenses, erosion %) could consume the same tool-calling
loop. Because the erosion model, tool schemas, and thresholds are explicit and inspectable, the same
architecture is a plausible starting point for a real planning tool — swap the illustrative heuristic
for the city's actual coastal engineering model, and the Gemma-driven natural-language interface layer
does not need to change at all.
