"""CruzSurge agent core: Gemma 4 (via Ollama, text-only, native tool calling)
parses a natural-language storm command into structured simulation tool calls
that drive the West Cliff Drive wave/cliff canvas. Same proven agent-loop
pattern as agent/cruzguard_agent.py, retargeted from vision+hazard-triage to
text+coastal-physics-control."""

import json
import time
import ollama

MODEL = "gemma4:latest"

SYSTEM_PROMPT = """You are CruzSurge, an AI simulation operator for a coastal erosion model of \
West Cliff Drive in Santa Cruz, California. The user describes a storm or tide scenario in plain \
language. Your job is to translate that into the simulator's control functions.

Available state you control:
- tide level: low, neutral, high, king_tide
- wave amplitude (0.0-1.0, where 1.0 is an extreme storm swell)
- wave frequency (0.0-1.0, how rapidly waves arrive)
- seawall / rip-rap defense: on or off
- erosion progress: call calculate_erosion_rate to advance the simulation and get a new cumulative \
erosion percentage (0-100) given the current wave/tide/defense state

Rules:
1. Always call set_tide_level and update_wave_kinematics to reflect the scenario described.
2. If the user mentions a seawall, rip-rap, or coastal defenses, call toggle_infrastructure.
3. Always finish by calling calculate_erosion_rate for a reasonable simulated duration (in hours) \
implied by the scenario, so the cliff visibly responds.
4. Keep your own commentary minimal; let the tool calls do the work.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "set_tide_level",
            "description": "Set the baseline ocean water level against the cliff/seawall.",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "string", "enum": ["low", "neutral", "high", "king_tide"]},
                },
                "required": ["level"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_wave_kinematics",
            "description": "Set incoming wave amplitude and frequency to match a storm scenario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amplitude": {"type": "number", "description": "0.0 (calm) to 1.0 (extreme storm swell)"},
                    "frequency": {"type": "number", "description": "0.0 (slow swell) to 1.0 (rapid wave train)"},
                },
                "required": ["amplitude", "frequency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "toggle_infrastructure",
            "description": "Add or remove a coastal defense structure (seawall / rip-rap) at the cliff base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "defense_type": {"type": "string", "enum": ["seawall", "rip_rap", "none"]},
                    "active": {"type": "boolean"},
                },
                "required": ["defense_type", "active"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_erosion_rate",
            "description": "Advance the simulation and compute cumulative cliff erosion given the current wave/tide/defense state.",
            "parameters": {
                "type": "object",
                "properties": {
                    "simulated_hours": {"type": "integer", "description": "Duration to simulate, in hours"},
                },
                "required": ["simulated_hours"],
            },
        },
    },
]

DEFAULT_STATE = {
    "tide_level": "neutral",
    "wave_amplitude": 0.2,
    "wave_frequency": 0.3,
    "seawall_active": True,
    "rip_rap_active": False,
    "erosion_pct": 8,
    "simulated_hours_total": 0,
}

_TIDE_BUMP = {"low": -0.1, "neutral": 0.0, "high": 0.15, "king_tide": 0.3}


def _erosion_model(state: dict, hours: int) -> float:
    """Simple, explainable erosion heuristic: wave energy proxy (amplitude^2 * frequency),
    boosted by tide level, dampened by active defenses, integrated over simulated hours."""
    wave_energy = (state["wave_amplitude"] ** 2) * (0.4 + state["wave_frequency"])
    tide_boost = 1.0 + _TIDE_BUMP.get(state["tide_level"], 0.0)
    defense_factor = 1.0
    if state.get("seawall_active"):
        defense_factor *= 0.45
    if state.get("rip_rap_active"):
        defense_factor *= 0.7
    increment = wave_energy * tide_boost * defense_factor * (hours / 6.0) * 10
    return min(100.0, state["erosion_pct"] + increment)


def _exec_tool(name: str, args: dict, state: dict) -> dict:
    if name == "set_tide_level":
        state["tide_level"] = args["level"]
        return {"status": "ok", "tide_level": state["tide_level"]}
    if name == "update_wave_kinematics":
        state["wave_amplitude"] = max(0.0, min(1.0, float(args["amplitude"])))
        state["wave_frequency"] = max(0.0, min(1.0, float(args["frequency"])))
        return {"status": "ok", "wave_amplitude": state["wave_amplitude"], "wave_frequency": state["wave_frequency"]}
    if name == "toggle_infrastructure":
        if args["defense_type"] == "seawall":
            state["seawall_active"] = bool(args["active"])
        elif args["defense_type"] == "rip_rap":
            state["rip_rap_active"] = bool(args["active"])
        elif args["defense_type"] == "none":
            state["seawall_active"] = False
            state["rip_rap_active"] = False
        return {"status": "ok", "seawall_active": state["seawall_active"], "rip_rap_active": state["rip_rap_active"]}
    if name == "calculate_erosion_rate":
        hours = int(args.get("simulated_hours", 6))
        new_pct = _erosion_model(state, hours)
        state["erosion_pct"] = round(new_pct, 1)
        state["simulated_hours_total"] += hours
        return {"status": "ok", "erosion_pct": state["erosion_pct"], "simulated_hours": hours}
    return {"status": "unknown_tool"}


def run_command(command: str, state: dict, max_turns: int = 5, think: bool = True) -> dict:
    """Runs one agent turn: user's natural-language command -> Gemma tool calls -> mutated state.
    `state` is mutated in place and also returned for convenience."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Current state: {json.dumps(state)}\n\nScenario: {command}",
        },
    ]

    trace = []
    start = time.time()

    for turn in range(max_turns):
        resp = ollama.chat(model=MODEL, messages=messages, tools=TOOLS, think=think)
        msg = resp["message"]
        thinking = getattr(msg, "thinking", None) if not isinstance(msg, dict) else msg.get("thinking")
        content = msg["content"] if isinstance(msg, dict) else msg.content
        tool_calls = msg["tool_calls"] if isinstance(msg, dict) else msg.tool_calls

        trace.append({"turn": turn, "thinking": thinking, "content": content})

        if not tool_calls:
            break

        messages.append({"role": "assistant", "content": content or "", "tool_calls": tool_calls})

        for tc in tool_calls:
            fn = tc["function"] if isinstance(tc, dict) else tc.function
            name = fn["name"] if isinstance(fn, dict) else fn.name
            args = fn["arguments"] if isinstance(fn, dict) else fn.arguments
            result = _exec_tool(name, args, state)
            trace.append({"turn": turn, "tool_call": name, "arguments": args, "result": result})
            messages.append({"role": "tool", "content": json.dumps(result)})

    return {"state": state, "trace": trace, "duration_sec": round(time.time() - start, 1)}


if __name__ == "__main__":
    s = dict(DEFAULT_STATE)
    out = run_command("A category 2 storm is hitting at high tide. Take the seawall offline for repairs.", s)
    print(json.dumps(out, indent=2, default=str))
