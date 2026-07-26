"""Batch-runs the CruzGuard agent over every location in data/locations.json
and caches the full result (record + reasoning trace) to data/results.json.
This is what the Streamlit demo replays for speed/reliability; app.py also
supports re-running any single location live on demand."""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.cruzguard_agent import analyze_hazard

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCATIONS_PATH = os.path.join(ROOT, "data", "locations.json")
RESULTS_PATH = os.path.join(ROOT, "data", "results.json")


def main():
    with open(LOCATIONS_PATH) as f:
        locations = json.load(f)

    results = []
    for loc in locations:
        image_path = os.path.join(ROOT, "data", "images", loc["image"])
        print(f"Processing {loc['id']} ({image_path})...", flush=True)
        out = analyze_hazard(image_path, loc["label"], loc["lat"], loc["lon"])
        out["record"]["id"] = loc["id"]
        out["record"]["image"] = loc["image"]
        out["record"]["source"] = loc.get("source", "")
        results.append(out)
        print(f"  -> {out['record'].get('category')} / {out['record'].get('severity')} "
              f"(dispatched={out['record'].get('dispatched')})", flush=True)

    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nSaved {len(results)} results to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
