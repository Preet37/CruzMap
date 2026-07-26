"""CruzGuard agent core: Gemma 4 (via Ollama) analyzes a hazard photo and
autonomously calls tools to log the hazard and, if serious enough, dispatch
a public works ticket. This is the only place Gemma 4 is invoked."""

import json
import time
import ollama

MODEL = "gemma4:latest"

SYSTEM_PROMPT = """You are CruzGuard, an autonomous civic infrastructure inspection agent for the \
City of Santa Cruz, California. You are shown a photo taken at a specific street location. \
Your job:

1. Look carefully at the image and identify the single most important infrastructure hazard \
visible (e.g. pothole, coastal erosion, storm drain blockage, cracked sidewalk, fallen tree/storm \
debris, or other).
2. Call the `log_hazard` tool exactly once with your assessment.
3. If the severity you logged is "medium", "high", or "critical", you must then also call the \
`dispatch_public_works` tool to create a ticket for the city crew. If severity is "low", do not \
dispatch a ticket.
4. Keep descriptions to one concise sentence, written for a public works dispatcher, not a \
general audience.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "log_hazard",
            "description": "Log a detected civic infrastructure hazard for the Santa Cruz public works record.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": [
                            "pothole",
                            "coastal_erosion",
                            "storm_drain_debris",
                            "cracked_sidewalk",
                            "fallen_tree",
                            "other",
                        ],
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                    },
                    "description": {
                        "type": "string",
                        "description": "One concise sentence describing the hazard for a dispatcher.",
                    },
                },
                "required": ["category", "severity", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "dispatch_public_works",
            "description": "Create a Santa Cruz public works dispatch ticket for a logged hazard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "priority": {
                        "type": "string",
                        "enum": ["standard", "urgent", "emergency"],
                    },
                    "recommended_action": {
                        "type": "string",
                        "description": "What the crew should do, in one short sentence.",
                    },
                },
                "required": ["priority", "recommended_action"],
            },
        },
    },
]


def _exec_tool(name: str, args: dict) -> dict:
    """Simulated tool execution (writes to the local incident record).
    In a real deployment these would hit the city's actual work-order API."""
    if name == "log_hazard":
        return {"status": "logged", "hazard_id": f"hz-{int(time.time() * 1000) % 100000}"}
    if name == "dispatch_public_works":
        return {"status": "dispatched", "ticket_id": f"pw-{int(time.time() * 1000) % 100000}"}
    return {"status": "unknown_tool"}


def analyze_hazard(image_path: str, location_label: str, lat: float, lon: float, max_turns: int = 4) -> dict:
    """Runs the full agent loop for one photo. Returns a structured trace + final record."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Location: {location_label} (lat {lat}, lon {lon}). Inspect this photo and act.",
            "images": [image_path],
        },
    ]

    trace = []
    record = {"location_label": location_label, "lat": lat, "lon": lon, "image": image_path}
    start = time.time()

    for turn in range(max_turns):
        resp = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
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
            result = _exec_tool(name, args)
            trace.append({"turn": turn, "tool_call": name, "arguments": args, "result": result})

            if name == "log_hazard":
                record["category"] = args.get("category")
                record["severity"] = args.get("severity")
                record["description"] = args.get("description")
                record["hazard_id"] = result.get("hazard_id")
            elif name == "dispatch_public_works":
                record["priority"] = args.get("priority")
                record["recommended_action"] = args.get("recommended_action")
                record["ticket_id"] = result.get("ticket_id")

            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                }
            )

    record["duration_sec"] = round(time.time() - start, 1)
    record["dispatched"] = "ticket_id" in record
    return {"record": record, "trace": trace}


if __name__ == "__main__":
    out = analyze_hazard("data/images/pothole.jpg", "Pacific Avenue", 36.9741, -122.0297)
    print(json.dumps(out, indent=2, default=str))
