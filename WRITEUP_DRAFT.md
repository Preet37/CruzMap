# CruzSurge: A Natural-Language Coastal Erosion Simulator for Santa Cruz
### Subtitle: Drag a slider or describe a storm in English. Gemma 4 autonomously drives a live simulation of what happens to a real, disappearing Santa Cruz road.

*Track: Autonomous Agent*

## The Problem

West Cliff Drive in Santa Cruz is in an active, well-documented fight against coastal erosion. After
the January 2023 atmospheric river storms, a block of the road stayed closed for nearly two years
while the city repaired a sinkhole and seawall failure at 944/960 West Cliff Drive, an emergency
project involving an underdrain system and 450 cubic yards of slurry-cement backfill. The city is now
planning a roughly $1.8M project, targeting 2027 construction, to relocate about 400 to 600 feet of
road and pedestrian path 50 to 60 feet inland into Lighthouse Field State Beach, because the current
alignment cannot be defended indefinitely. (Sources: Lookout Santa Cruz, ABC7, Santa Cruz Local, and
the City of Santa Cruz's CEQA filing for the 944/960 West Cliff Drive emergency storm damage project.)

Today, the reasoning behind these decisions lives in static engineering reports and expensive
modeling software that only specialists can operate. A resident or a council member cannot easily ask
"what if a storm like that hit again with the seawall down" and get an answer. CruzSurge makes that
reasoning interactive.

## What this is, and isn't

CruzSurge is not a replacement for engineering-grade coastal modeling, and it does not claim to be.
The erosion math is a small, explainable heuristic, not a validated physical model, and the writeup
says so plainly. Its actual job is communication: giving a non-specialist an immediate, qualitative
feel for how tide, storm intensity, and coastal defenses trade off against a real cliff, grounded in
verified facts about their own street.

The reusable part of this project is not the cliff. It is the pattern underneath it: a person
describes intent in plain English, a local Gemma 4 agent decides which functions to call to configure
a live system, and the system responds immediately. That pattern generalizes to any public-facing
system a city or campus wants ordinary people, not just engineers, to be able to operate: transit
planning, wildfire risk, water usage, or anything else. West Cliff Drive is the demonstration. The
agent architecture is the point.

## Architecture

The core loop (`agent/cruzsurge_agent.py`) takes a natural-language scenario and the current
simulation state, and gives `gemma4:latest` (8B, Q4_K_M, served locally via Ollama) a system prompt
establishing it as the simulator's operator, plus four tool schemas: `set_tide_level`,
`update_wave_kinematics`, `toggle_infrastructure`, and `calculate_erosion_rate`. Gemma decides
autonomously which of these to call and with what arguments. It always sets tide and wave parameters,
only touches coastal defenses if the scenario mentions them, and always finishes by advancing the
simulation a scenario-appropriate number of hours. This is a genuine multi-call agentic turn: several
dependent decisions made in one pass, based on the model's own read of an unstructured sentence.

The erosion calculation itself is a small, transparent heuristic (wave energy proportional to
amplitude squared times frequency, boosted by tide level, dampened 45 to 70 percent by active
defenses, integrated over simulated hours), deliberately kept outside Gemma's direct control so the
simulation stays physically sane regardless of what is asked of it. Gemma's role is translation from
English to structured intent, not arithmetic.

The frontend is a single self-contained HTML page (`web/index.html`, no build step, no framework)
served by a thin Flask API (`server.py`) that does nothing but expose the agent loop over `fetch()`.
Two interaction paths sit side by side. The first needs no AI call at all: draggable sliders, a
segmented tide control, and defense toggles mutate the live canvas instantly, and a continuously
running client-side clock accrues erosion in real time based on whatever the current settings are, so
the cliff visibly degrades while you watch, not just on discrete clicks. The second path is the AI
agent showcase: type a scenario in English, and Gemma's tool calls visibly move those same sliders
into position and jump the erosion state forward, merging with whatever the live clock had already
accrued. Raw tool-call JSON and model reasoning are tucked behind an opt-in disclosure, closed by
default, so an ordinary user only ever sees the simulation and a plain-English result.

## Why Gemma 4, specifically

Gemma 4's native tool calling is not a demo feature bolted on top of a chatbot. It is the entire
mechanism that turns an unstructured sentence into a structured, physically grounded state change.
The model makes several linked judgment calls per scenario (what tide, what wave intensity, whether
defenses are mentioned at all, how long to run it) correctly across very different phrasings, from "a
mild winter storm" to "a catastrophic category 5 hurricane, run it for 72 hours." Because it runs
entirely offline via Ollama on Apple Silicon, the same architecture could run on a planning
department's own hardware with no cloud dependency or per-query cost, which matters for a tool meant
to be explored often and interactively rather than queried once.

## Challenges in a one-day sprint

The project went through two pivots before landing here, and being honest about that is part of the
engineering story. The first concept fused this agent with `lingbot-map`, an open-source streaming 3D
reconstruction model, to turn dashcam video into a navigable 3D flythrough of hazard sites. That
pipeline requires CUDA, FlashInfer, and a from-source Kaolin build, none of which run on the Apple
Silicon hardware available for this sprint, and it fundamentally needs continuous moving-camera
video that we did not have a fast, honestly licensed source for. Rather than burn the sprint's
remaining hours on an infeasible dependency, we cut it and built a photo-based civic hazard-triage
agent instead (`agent/cruzguard_agent.py`, kept in this repo as a working secondary prototype using
the same Gemma 4 vision and tool-calling pattern, applied to street-hazard photos).

That version worked but was not interactive: static photo pins under a chat log undersold what an
agent-driven system could demonstrate. The second pivot, CruzSurge, took that feedback seriously and
replaced fixed inputs with two live interaction paths (direct manipulation and natural language) so
the simulation always feels alive, whether or not Gemma is in the loop for a given moment.

## Why this is a strong foundation, not just a demo

The agent core is fully decoupled from both the visual layer and the specific domain. Any frontend
that can render the four state variables (tide, wave amplitude and frequency, defenses, erosion
percent) could consume the same tool-calling loop, and the tool schemas themselves are generic enough
that swapping the illustrative erosion heuristic for a city's actual coastal engineering model would
not require changing the Gemma-driven natural-language interface at all.
