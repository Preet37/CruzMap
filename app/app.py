"""CruzGuard — Autonomous Civic Infrastructure Agent for Santa Cruz.

Streamlit dashboard: a map of Santa Cruz fills with hazard pins as Gemma 4
(running 100% locally via Ollama) inspects each photo and autonomously fires
native tool calls (log_hazard, dispatch_public_works). The right-hand panel
streams the model's real reasoning trace and tool-call JSON live.
"""

import base64
import json
import os
import sys
import time

import folium
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_THIS_DIR))
sys.path.insert(0, _THIS_DIR)
from agent.cruzguard_agent import analyze_hazard  # noqa: E402
from severity import color_for, icon_for  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(ROOT, "data", "images")
LOCATIONS_PATH = os.path.join(ROOT, "data", "locations.json")
RESULTS_PATH = os.path.join(ROOT, "data", "results.json")
SC_CENTER = [36.9741, -122.0297]

st.set_page_config(page_title="CruzGuard", page_icon="\U0001F6A6", layout="wide")


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

@st.cache_data
def load_locations():
    with open(LOCATIONS_PATH) as f:
        return {loc["id"]: loc for loc in json.load(f)}


def load_results():
    if not os.path.exists(RESULTS_PATH):
        return []
    with open(RESULTS_PATH) as f:
        return json.load(f)


@st.cache_data
def thumb_b64(image_name: str, max_w: int = 480) -> str:
    path = os.path.join(IMAGES_DIR, image_name)
    img = Image.open(path).convert("RGB")
    ratio = max_w / img.width
    img = img.resize((max_w, int(img.height * ratio)))
    buf_path = "/tmp/_cruzguard_thumb.jpg"
    img.save(buf_path, "JPEG", quality=80)
    with open(buf_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def popup_html(rec: dict) -> str:
    b64 = thumb_b64(rec["image"])
    color = color_for(rec.get("severity", "low"))
    return f"""
    <div style="width:280px;font-family:sans-serif;">
      <img src="data:image/jpeg;base64,{b64}" style="width:100%;border-radius:6px;margin-bottom:6px;" />
      <b>{icon_for(rec.get('category',''))} {rec.get('category','').replace('_',' ').title()}</b>
      <span style="float:right;color:{color};font-weight:bold;">{rec.get('severity','').upper()}</span>
      <p style="margin:6px 0;font-size:0.85em;">{rec.get('description','')}</p>
      {f"<p style='margin:0;font-size:0.8em;color:#d29922;'>🎫 Ticket {rec['ticket_id']} — {rec.get('priority','').upper()}</p>" if rec.get('dispatched') else "<p style='margin:0;font-size:0.8em;color:#3fb950;'>No dispatch needed</p>"}
    </div>
    """


def render_map(records: list) -> str:
    m = folium.Map(location=SC_CENTER, zoom_start=13, tiles="CartoDB dark_matter")
    for rec in records:
        folium.CircleMarker(
            location=[rec["lat"], rec["lon"]],
            radius=14,
            color=color_for(rec.get("severity", "low")),
            weight=2,
            fill=True,
            fill_color=color_for(rec.get("severity", "low")),
            fill_opacity=0.85,
            popup=folium.Popup(popup_html(rec), max_width=300),
            tooltip=f"{rec['location_label']} — {rec.get('severity','?').upper()}",
        ).add_to(m)
    return m.get_root().render()


def stream_text(placeholder, text: str, prefix: str = "", delay: float = 0.018, chunk: int = 2):
    words = (text or "").split()
    shown = ""
    for i in range(0, len(words), chunk):
        shown += " " + " ".join(words[i : i + chunk])
        placeholder.markdown(f"{prefix}\n\n```\n{shown.strip()}\n```")
        time.sleep(delay)
    return shown.strip()


def render_tool_call(entry: dict) -> str:
    name = entry["tool_call"]
    args = entry["arguments"]
    result = entry["result"]
    icon = "\U0001F4CB" if name == "log_hazard" else "\U0001F6A8"
    return (
        f"**{icon} tool call → `{name}()`**\n\n"
        f"```json\n{json.dumps(args, indent=2)}\n```\n"
        f"→ `{json.dumps(result)}`"
    )


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div style="display:flex;align-items:center;gap:14px;">
      <div style="font-size:2.4em;">\U0001F6A6</div>
      <div>
        <h1 style="margin:0;">CruzGuard</h1>
        <p style="margin:0;color:#8b949e;">Autonomous civic infrastructure agent for Santa Cruz — powered entirely by local <b>Gemma 4</b> (vision + native function calling)</p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.divider()

locations = load_locations()
all_results = load_results()

# ---------------------------------------------------------------------------
# Metrics row
# ---------------------------------------------------------------------------

if all_results:
    recs = [r["record"] for r in all_results]
    dispatched = sum(1 for r in recs if r.get("dispatched"))
    avg_time = sum(r.get("duration_sec", 0) for r in recs) / len(recs)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations inspected", len(recs))
    c2.metric("Tickets dispatched", dispatched)
    c3.metric("Avg. inference time", f"{avg_time:.1f}s")
    c4.metric("Model", "gemma4:latest (8B, local)")

st.divider()

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------

st.sidebar.header("Controls")
run_demo = st.sidebar.button("▶️  Run Cinematic Demo", use_container_width=True, type="primary")

st.sidebar.divider()
st.sidebar.subheader("⚡ Live Analysis (proof it's real)")
loc_choice = st.sidebar.selectbox(
    "Pick a location to analyze right now",
    options=list(locations.keys()),
    format_func=lambda k: locations[k]["label"],
)
run_live = st.sidebar.button("Run Gemma 4 live on this photo", use_container_width=True)

st.sidebar.divider()
st.sidebar.caption(
    "Track: Autonomous Agent  \nModel: gemma4:latest (8B, Q4_K_M) via Ollama, 100% local/offline  \n"
    "Tools: log_hazard, dispatch_public_works"
)

# ---------------------------------------------------------------------------
# Main layout
# ---------------------------------------------------------------------------

col_map, col_trace = st.columns([3, 2])

with col_map:
    st.subheader("\U0001F5FA️ Live Hazard Map")
    map_placeholder = st.empty()

with col_trace:
    st.subheader("\U0001F9E0 Agent Trace")
    trace_placeholder = st.empty()

if "revealed" not in st.session_state:
    st.session_state.revealed = [r["record"] for r in all_results] if all_results else []

with map_placeholder.container():
    components.html(render_map(st.session_state.revealed), height=520)

if not st.session_state.revealed:
    trace_placeholder.info(
        "Press **▶️ Run Cinematic Demo** in the sidebar to watch CruzGuard inspect each location live, "
        "or run a genuine live Gemma 4 call from the sidebar."
    )
else:
    trace_placeholder.success(f"{len(st.session_state.revealed)} locations inspected. Press Run Cinematic Demo to replay.")

# ---------------------------------------------------------------------------
# Cinematic demo replay
# ---------------------------------------------------------------------------

if run_demo and all_results:
    st.session_state.revealed = []
    with map_placeholder.container():
        components.html(render_map([]), height=520)

    for result in all_results:
        rec = result["record"]
        trace = result["trace"]

        trace_placeholder.markdown(f"### \U0001F4CD Inspecting: **{rec['location_label']}**")
        time.sleep(0.4)

        for entry in trace:
            if entry.get("thinking"):
                stream_text(trace_placeholder, f"### \U0001F4CD {rec['location_label']}\n\U0001F4AD *thinking...*", entry["thinking"])
            if entry.get("tool_call"):
                trace_placeholder.markdown(
                    f"### \U0001F4CD {rec['location_label']}\n\n" + render_tool_call(entry)
                )
                time.sleep(0.9)
            if entry.get("content") and not entry.get("tool_call"):
                trace_placeholder.markdown(f"### \U0001F4CD {rec['location_label']}\n\n✅ {entry['content']}")
                time.sleep(0.6)

        st.session_state.revealed.append(rec)
        with map_placeholder.container():
            components.html(render_map(st.session_state.revealed), height=520)
        time.sleep(0.8)

    trace_placeholder.success("Demo complete — all locations inspected by Gemma 4.")
    st.rerun()

# ---------------------------------------------------------------------------
# Live (non-cached) analysis
# ---------------------------------------------------------------------------

if run_live:
    loc = locations[loc_choice]
    image_path = os.path.join(IMAGES_DIR, loc["image"])
    with trace_placeholder:
        with st.spinner(f"Gemma 4 is analyzing {loc['label']} live (no cache)..."):
            out = analyze_hazard(image_path, loc["label"], loc["lat"], loc["lon"])
    rec = out["record"]
    rec["id"] = loc["id"]
    rec["image"] = loc["image"]

    lines = [f"### ⚡ LIVE inspection: **{loc['label']}**"]
    for entry in out["trace"]:
        if entry.get("thinking"):
            lines.append(f"**\U0001F4AD thinking:**\n```\n{entry['thinking']}\n```")
        if entry.get("tool_call"):
            lines.append(render_tool_call(entry))
        if entry.get("content") and not entry.get("tool_call"):
            lines.append(f"✅ {entry['content']}")
    trace_placeholder.markdown("\n\n---\n\n".join(lines))

    st.session_state.revealed = [r for r in st.session_state.revealed if r.get("id") != loc["id"]]
    st.session_state.revealed.append(rec)
    with map_placeholder.container():
        components.html(render_map(st.session_state.revealed), height=520)

# ---------------------------------------------------------------------------
# Hazard log table
# ---------------------------------------------------------------------------

st.divider()
st.subheader("\U0001F4CB Hazard Log")
if st.session_state.revealed:
    for rec in st.session_state.revealed:
        with st.expander(
            f"{icon_for(rec.get('category',''))} {rec['location_label']} — "
            f"{rec.get('category','').replace('_',' ').title()} ({rec.get('severity','?').upper()})"
        ):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.image(os.path.join(IMAGES_DIR, rec["image"]))
            with c2:
                st.write(rec.get("description", ""))
                if rec.get("dispatched"):
                    st.warning(f"\U0001F3AB Ticket `{rec.get('ticket_id')}` — priority **{rec.get('priority','').upper()}**: {rec.get('recommended_action','')}")
                else:
                    st.success("No dispatch needed (low severity).")
                st.caption(f"Source: {rec.get('source','')} — inference time {rec.get('duration_sec','?')}s")
else:
    st.caption("No hazards logged yet.")
