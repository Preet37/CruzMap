"""Self-contained HTML5 canvas: an animated cross-section of West Cliff Drive
(ocean, cliff, seawall, road) driven by the CruzSurge simulation state. No
external libraries — pure canvas 2D, embedded via st.components.v1.html."""

import json


def render_canvas(state: dict, height: int = 420) -> str:
    tide_offset = {"low": -22, "neutral": 0, "high": 22, "king_tide": 42}.get(state["tide_level"], 0)
    payload = json.dumps(
        {
            "tideOffset": tide_offset,
            "amp": state["wave_amplitude"],
            "freq": state["wave_frequency"],
            "erosionPct": state["erosion_pct"],
            "seawall": state["seawall_active"],
            "ripRap": state["rip_rap_active"],
        }
    )

    return f"""
    <div style="background:#0d1117;border-radius:8px;padding:8px;">
    <canvas id="surge" width="1000" height="{height}" style="width:100%;display:block;border-radius:6px;"></canvas>
    </div>
    <script>
    (function() {{
        const S = {payload};
        const canvas = document.getElementById('surge');
        const ctx = canvas.getContext('2d');
        const W = canvas.width, H = canvas.height;

        const baseWaterY = H * 0.55;
        const baseCliffEdgeX = W * 0.42;
        const maxRecedePx = W * 0.34;
        const cliffEdgeX = baseCliffEdgeX + (S.erosionPct / 100) * maxRecedePx;
        const waterY = baseWaterY - S.tideOffset;

        let t = 0;

        function drawSky() {{
            const g = ctx.createLinearGradient(0, 0, 0, waterY);
            g.addColorStop(0, '#1b2735');
            g.addColorStop(1, '#3a4a5c');
            ctx.fillStyle = g;
            ctx.fillRect(0, 0, W, waterY + 10);
        }}

        function drawCliff() {{
            const crackCount = Math.floor(S.erosionPct / 15);
            ctx.fillStyle = S.erosionPct > 60 ? '#6b4a3a' : '#5a4632';
            ctx.beginPath();
            ctx.moveTo(cliffEdgeX, waterY + 6);
            // jagged rock face
            let x = cliffEdgeX;
            const steps = 6;
            for (let i = 0; i <= steps; i++) {{
                const jag = (i % 2 === 0 ? -8 : 8) * (1 + S.erosionPct / 100);
                ctx.lineTo(x + jag, waterY + 6 + (H - waterY - 6) * (i / steps));
            }}
            ctx.lineTo(W, H);
            ctx.lineTo(W, waterY - 60);
            ctx.lineTo(cliffEdgeX, waterY - 60);
            ctx.closePath();
            ctx.fill();

            // cracks
            ctx.strokeStyle = 'rgba(0,0,0,0.35)';
            ctx.lineWidth = 2;
            for (let i = 0; i < crackCount; i++) {{
                const cx = cliffEdgeX + 20 + i * 22;
                if (cx > W - 10) continue;
                ctx.beginPath();
                ctx.moveTo(cx, waterY - 60);
                ctx.lineTo(cx + 6, waterY - 20);
                ctx.lineTo(cx - 4, waterY + 10);
                ctx.stroke();
            }}
        }}

        function drawRoad() {{
            const roadY = waterY - 60;
            const roadW = W - cliffEdgeX;
            ctx.fillStyle = '#39404a';
            ctx.fillRect(cliffEdgeX, roadY - 14, roadW, 14);
            ctx.strokeStyle = '#e8c547';
            ctx.setLineDash([10, 8]);
            ctx.beginPath();
            ctx.moveTo(cliffEdgeX, roadY - 7);
            ctx.lineTo(W, roadY - 7);
            ctx.stroke();
            ctx.setLineDash([]);

            ctx.fillStyle = '#c9d1d9';
            ctx.font = '13px sans-serif';
            ctx.fillText('West Cliff Drive', Math.min(cliffEdgeX + 14, W - 120), roadY - 20);

            if (S.erosionPct > 70) {{
                ctx.fillStyle = '#f85149';
                ctx.font = 'bold 14px sans-serif';
                ctx.fillText('\\u26A0 ROAD AT RISK', cliffEdgeX + 14, roadY - 40);
            }}
            if (S.erosionPct >= 95) {{
                ctx.fillStyle = '#f85149';
                ctx.font = 'bold 16px sans-serif';
                ctx.fillText('\\u26A0\\uFE0F ROADWAY COLLAPSE', W * 0.55, roadY - 60);
            }}
        }}

        function drawSeawall() {{
            if (S.seawall) {{
                ctx.fillStyle = '#8b949e';
                ctx.fillRect(cliffEdgeX - 10, waterY - 30, 12, 90);
            }}
            if (S.ripRap) {{
                ctx.fillStyle = '#6e7681';
                for (let i = 0; i < 5; i++) {{
                    const rx = cliffEdgeX - 26 - i * 10;
                    const ry = waterY + 10 + (i % 2) * 8;
                    ctx.beginPath();
                    ctx.arc(rx, ry, 9, 0, Math.PI * 2);
                    ctx.fill();
                }}
            }}
        }}

        function drawWaves() {{
            const layers = [
                {{ color: 'rgba(56,139,253,0.35)', speed: 1.0, yOff: -6 }},
                {{ color: 'rgba(31,111,235,0.55)', speed: 1.4, yOff: 6 }},
                {{ color: 'rgba(9,72,160,0.85)', speed: 1.8, yOff: 18 }},
            ];
            const amp = 6 + S.amp * 34;
            const wavelength = 260 - S.freq * 160;
            layers.forEach((layer) => {{
                ctx.beginPath();
                ctx.moveTo(0, H);
                for (let x = 0; x <= cliffEdgeX + 20; x += 6) {{
                    const y = waterY + layer.yOff + Math.sin((x / wavelength) + t * layer.speed) * amp;
                    ctx.lineTo(x, y);
                }}
                ctx.lineTo(cliffEdgeX + 20, H);
                ctx.closePath();
                ctx.fillStyle = layer.color;
                ctx.fill();
            }});
        }}

        function drawHUD() {{
            ctx.fillStyle = 'rgba(13,17,23,0.75)';
            ctx.fillRect(10, 10, 230, 78);
            ctx.fillStyle = '#c9d1d9';
            ctx.font = '12px monospace';
            ctx.fillText('Erosion: ' + S.erosionPct.toFixed(1) + '%', 20, 30);
            ctx.fillText('Wave amplitude: ' + S.amp.toFixed(2), 20, 48);
            ctx.fillText('Wave frequency: ' + S.freq.toFixed(2), 20, 66);
            ctx.fillText('Defenses: ' + (S.seawall ? 'seawall ' : '') + (S.ripRap ? 'rip-rap' : '') + (!S.seawall && !S.ripRap ? 'none' : ''), 20, 82);
        }}

        function draw() {{
            ctx.clearRect(0, 0, W, H);
            drawSky();
            drawWaves();
            drawCliff();
            drawSeawall();
            drawRoad();
            drawHUD();
            t += 0.015 + S.freq * 0.03;
            requestAnimationFrame(draw);
        }}
        draw();
    }})();
    </script>
    """
