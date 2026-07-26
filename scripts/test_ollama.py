import ollama
import json

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "log_hazard",
            "description": "Log a detected civic infrastructure hazard for public works dispatch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["pothole", "coastal_erosion", "storm_drain_debris", "cracked_sidewalk", "fallen_tree", "other"],
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                    },
                    "description": {"type": "string", "description": "One sentence describing what is visible in the image."},
                },
                "required": ["category", "severity", "description"],
            },
        },
    }
]

resp = ollama.chat(
    model="gemma4:latest",
    messages=[
        {
            "role": "system",
            "content": "You are CruzGuard, a civic infrastructure inspection agent for the city of Santa Cruz. "
                       "Look at the image and call the log_hazard tool with your assessment.",
        },
        {
            "role": "user",
            "content": "Inspect this location and log any hazard you see.",
            "images": ["data/images/pothole.jpg"],
        },
    ],
    tools=TOOLS,
)

print("=== RAW RESPONSE ===")
print(resp)
print("\n=== message.content ===")
print(resp.get("message", {}).get("content"))
print("\n=== tool_calls ===")
print(json.dumps(resp.get("message", {}).get("tool_calls"), indent=2, default=str))
