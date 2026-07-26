"""CruzSurge — Natural-language coastal erosion simulator for West Cliff
Drive, Santa Cruz. Gemma 4 (local, via Ollama, native tool calling) parses a
storm/tide scenario typed by the user into simulation control calls; a
self-contained HTML5 canvas renders the ocean/cliff/road cross-section
reacting live."""

import json
import os
import sys
import time

import streamlit as st
import streamlit.components.v1 as components

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_THIS_DIR))
sys.path.insert(0, _THIS_DIR)

from agent.cruzsurge_agent import run_command, DEFAULT_STATE  # noqa: E402
from canvas import render_canvas  # noqa: E402

st.set_page_config(page_title="CruzSurge", page_icon="\U0001F30A", layout="wide")

if "surge_state" not in st.session_state:
    st.session_state.surge_state = dict(DEFAULT_STATE)
if "surge_log" not in st.session_state:
    st.session_state.surge_log = []

st.markdown(
    """
    <div style="display:flex;align-items:center;gap:14px;">
      <div style="font-size:2.4em;">\U0001F30A</div>
      <div>
        <h1 style="margin:0;">CruzSurge</h1>
        <p style="margin:0;color:#8b949e;">Natural-language coastal erosion simulator for West Cliff Drive, Santa Cruz — driven live by local <b>Gemma 4</b> native tool calling</p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("\U0001F4CA Why West Cliff Drive — the real stakes (verified)"):
    st.markdown(
        """
- **~30 months / nearly 2 years**: how long a block of West Cliff Drive stayed closed after the Jan 2023
  atmospheric river storms damaged the seawall and roadway. *(Lookout Santa Cruz, ABC7)*
- **944/960 West Cliff Drive**: sites of an emergency-declared sinkhole and seawall failure requiring
  underdrain and slurry-cement backfill repair. *(City of Santa Cruz CEQA filing)*
- **~$1.8M, targeting 2027 construction**: the city's plan to relocate ~400-600 ft of road and the
  pedestrian path 50-60 ft inland into Lighthouse Field State Beach, because the current alignment
  can't be defended long-term. *(Lookout Santa Cruz, Santa Cruz Local)*

City planning for this today relies on static engineering reports and expensive modeling software.
CruzSurge lets anyone type a storm scenario in plain English and see, immediately, how tide, wave
energy, and coastal defenses trade off against the cliff — the same qualitative reasoning behind the
city's own retreat-and-defend decisions, made interactive.
        """
    )

st.divider()

col_canvas, col_chat = st.columns([3, 2])

with col_canvas:
    st.subheader("\U0001F30A Live Simulation")
    canvas_placeholder = st.empty()
    with canvas_placeholder.container():
        components.html(render_canvas(st.session_state.surge_state), height=440)

    reset_col, _ = st.columns([1, 3])
    if reset_col.button("\U0001F504 Reset to calm baseline"):
        st.session_state.surge_state = dict(DEFAULT_STATE)
        st.session_state.surge_log = []
        st.rerun()

with col_chat:
    st.subheader("\U0001F9E0 Talk to the simulator")
    st.caption("Describe a storm/tide scenario in plain English. Gemma 4 decides the tool calls.")

    presets = st.columns(2)
    preset_command = None
    if presets[0].button("Category 2 storm @ high tide", use_container_width=True):
        preset_command = "Simulate a category 2 storm hitting West Cliff Drive at high tide."
    if presets[1].button("King tide, seawall offline", use_container_width=True):
        preset_command = "A king tide is rolling in and the seawall is offline for repairs."

    command = st.text_input("Scenario", value=preset_command or "", placeholder="e.g. A category 4 hurricane swell hits at king tide with no seawall")
    fast_mode = st.checkbox("Fast mode (thinking off, ~10s)", value=True)
    run_clicked = st.button("⚡ Run scenario", type="primary", use_container_width=True)

    trace_placeholder = st.empty()

    if (run_clicked or preset_command) and command:
        with st.spinner(f"Gemma 4 is reasoning about: “{command}”..."):
            out = run_command(command, st.session_state.surge_state, think=not fast_mode)

        lines = [f"**\U0001F3D4️ Scenario:** {command}", f"*({out['duration_sec']}s)*"]
        for entry in out["trace"]:
            if entry.get("thinking"):
                lines.append(f"**\U0001F4AD thinking:**\n```\n{entry['thinking']}\n```")
            if entry.get("tool_call"):
                lines.append(f"**\U0001F527 `{entry['tool_call']}()`**\n```json\n{json.dumps(entry['arguments'], indent=2)}\n```")
            if entry.get("content") and not entry.get("tool_call"):
                lines.append(f"✅ {entry['content']}")
        trace_placeholder.markdown("\n\n---\n\n".join(lines))

        st.session_state.surge_log.insert(0, {"command": command, "duration": out["duration_sec"], "erosion": st.session_state.surge_state["erosion_pct"]})

        with canvas_placeholder.container():
            components.html(render_canvas(st.session_state.surge_state), height=440)
    elif st.session_state.surge_log:
        last = st.session_state.surge_log[0]
        trace_placeholder.info(f"Last scenario: “{last['command']}” → erosion now {last['erosion']}%")
    else:
        trace_placeholder.info("Try a preset above, or describe your own storm scenario.")

st.divider()
st.subheader("\U0001F4CB Scenario Log")
if st.session_state.surge_log:
    for entry in st.session_state.surge_log[:10]:
        st.caption(f"`{entry['duration']}s` — {entry['command']} → erosion {entry['erosion']}%")
else:
    st.caption("No scenarios run yet.")
