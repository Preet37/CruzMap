# CruzGuard: An Autonomous Civic Infrastructure Agent for Santa Cruz
### Subtitle: Turning a street photo into a public-works ticket, entirely on-device with Gemma 4's native vision and tool calling

*Track: Autonomous Agent*

## The Problem

Santa Cruz is in a constant, expensive fight against infrastructure decay: coastal bluff collapse
along West Cliff Drive has forced repeated emergency road closures, and the city — like most
mid-size municipalities — has no scalable way to triage everyday hazards like potholes, clogged
storm drains, cracked sidewalks, and storm-downed trees. Today that requires a human crew to
physically drive out and inspect every report. CruzGuard demonstrates that a single, locally-run
open model can do the first pass: look at a photo, decide what's wrong, judge how serious it is,
and autonomously file the paperwork — with no cloud dependency, no per-request API cost, and no
internet connectivity requirement.

## Architecture

CruzGuard is a thin, honest wrapper around one core loop (`agent/cruzguard_agent.py`): a photo and
a GPS location go in, `gemma4:latest` (8B, Q4_K_M, served locally via Ollama) is given a system
prompt establishing it as a Santa Cruz civic inspector and two tool schemas — `log_hazard(category,
severity, description)` and `dispatch_public_works(priority, recommended_action)`. The model looks
at the image using its native vision capability, reasons about it (Gemma 4 runs with thinking
enabled, so we get a genuine chain-of-thought for every decision), and calls `log_hazard`. If it
judged the severity to be medium or higher, it independently decides to make a second tool call,
`dispatch_public_works`, in the same turn-taking loop — nothing forces that second call; the model
chooses to make it based on its own severity assessment. A final turn produces a plain-language
summary. This is a real multi-turn agentic loop, not a single canned prompt-and-parse.

The Streamlit dashboard (`app/app.py`) is a live console: a map of Santa Cruz starts empty and
fills with color-coded severity pins as each location is inspected, while a side panel streams
Gemma's actual reasoning trace and the raw tool-call JSON as it happens. A sidebar control also
lets a judge trigger a genuine, non-cached inference call against Ollama on demand — proof this is
live model output, not a scripted replay.

## Why Gemma 4, specifically

Gemma 4 is not a bolt-on chatbot here — it is the entire decision-making mechanism. Its **native
vision** capability reads the photo directly with no separate object-detection model in the loop.
Its **native tool/function calling** is what turns "look at this picture" into a structured,
machine-actionable record — the model itself decides which function to call, with what arguments,
and whether a second call is warranted. And because it runs **entirely offline** via Ollama on
Apple Silicon, the same pipeline could run on a city vehicle's onboard compute with no cellular
connection, which matters for a real municipal deployment surveying remote areas like the Santa
Cruz Mountains after a storm.

## Challenges in a one-day sprint

The single biggest early decision was walking away from an initially more ambitious plan: fusing
this agent with `lingbot-map`, an open-source streaming 3D reconstruction model, to turn dashcam
video into a live 3D flythrough with hazard annotations. That pipeline requires CUDA, FlashInfer,
and a from-source Kaolin build — none of which run on the Apple Silicon hardware available for this
sprint. Rather than lose hours fighting an infeasible dependency, we cut it entirely and rebuilt the
project around what Gemma 4 itself could do end-to-end, offline, on the hardware in hand. That
turned out to be the right call: it kept 100% of the remaining time on deepening the actual Gemma
integration (a real multi-turn tool-calling loop, not a single call) instead of fighting a build.

A second challenge was authenticity under real time constraints: with only a few hours and no
opportunity to travel to every hazard site in Santa Cruz in person, the demo uses one real,
public-domain USGS photo of an actual West Cliff Drive collapse, plus four freely-licensed
illustrative photos (Wikimedia Commons) standing in for common Santa Cruz hazard types, mapped to
real Santa Cruz street coordinates. `data/locations.json` documents the true source of every image
so this is fully transparent rather than passed off as literal footage of those exact streets.

## Why this is a strong foundation, not just a demo

The agent core is fully decoupled from the data source: it accepts any photo + location, whether
that photo comes from a city dashcam, a resident's phone report, or a drone survey. Extending it to
a real pipeline is a data-plumbing problem, not an architecture change — the same `log_hazard`
and `dispatch_public_works` tools could write to an actual 311/public-works ticketing system instead
of the simulated in-memory store used for the demo.
