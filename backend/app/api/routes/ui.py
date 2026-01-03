from fastapi import APIRouter, Response

from app.core.config import get_settings

router = APIRouter(prefix="/ui", tags=["ui"])


@router.get("/timeline", response_class=Response)
async def timeline_preview() -> Response:
    settings = get_settings()
    tenant_id = settings.default_tenant_id

    html = f"""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>FlightPlan Timeline Preview</title>
    <style>
      @import url("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600&display=swap");
      :root {{
        --bg: #f7f2ec;
        --ink: #1d1a16;
        --muted: #6b5f54;
        --accent: #2f6f6f;
        --accent-2: #b25c3a;
        --accent-3: #3c4f6b;
        --card: #fff7f0;
        --line: #d8ccc1;
      }}
      * {{
        box-sizing: border-box;
      }}
      body {{
        margin: 0;
        font-family: "Space Grotesk", "Segoe UI", sans-serif;
        color: var(--ink);
        background: radial-gradient(circle at 10% 10%, #fff6ed, var(--bg));
      }}
      header {{
        padding: 28px 24px 16px;
      }}
      h1 {{
        font-size: 28px;
        margin: 0 0 8px 0;
      }}
      p {{
        margin: 0;
        color: var(--muted);
      }}
      .container {{
        padding: 16px 24px 48px;
        display: grid;
        gap: 20px;
      }}
      .card {{
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 16px;
        box-shadow: 0 8px 20px rgba(34, 24, 16, 0.08);
        animation: fadeIn 0.4s ease-out both;
      }}
      .card h2 {{
        font-size: 18px;
        margin: 0 0 6px 0;
      }}
      .card small {{
        color: var(--muted);
      }}
      .legend {{
        display: flex;
        gap: 14px;
        flex-wrap: wrap;
        margin-top: 10px;
        color: var(--muted);
        font-size: 12px;
      }}
      .legend span {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }}
      .dot {{
        width: 10px;
        height: 10px;
        border-radius: 999px;
        display: inline-block;
      }}
      .dot.locations {{
        background: var(--accent);
      }}
      .dot.events {{
        background: var(--accent-2);
      }}
      .dot.attachments {{
        background: var(--accent-3);
      }}
      svg {{
        width: 100%;
        height: auto;
      }}
      .axis-label {{
        font-size: 12px;
        fill: var(--muted);
      }}
      .lane-label {{
        font-size: 13px;
        fill: var(--ink);
        font-weight: 600;
      }}
      .empty {{
        padding: 12px;
        color: var(--muted);
      }}
      @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to {{ opacity: 1; transform: translateY(0); }}
      }}
    </style>
  </head>
  <body>
    <header>
      <h1>Timeline Preview</h1>
      <p>Quick visual check of synthetic data for a couple of patients.</p>
    </header>
    <section class="container" id="timeline-root">
      <div class="card empty">Loading timeline…</div>
    </section>
    <script>
      const TENANT_ID = "{tenant_id}";

      const fmtDate = (value) => {{
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return "Unknown time";
        return date.toLocaleString();
      }};

      const toMillis = (value) => {{
        const date = new Date(value);
        return Number.isNaN(date.getTime()) ? null : date.getTime();
      }};

          async function fetchJson(url) {{
            const resp = await fetch(url, {{
              headers: {{
                "X-Tenant-ID": TENANT_ID,
              }},
            }});
            if (!resp.ok) {{
              throw new Error(`Request failed: ${{resp.status}}`);
            }}
            return resp.json();
          }}

      function makeSvgTimeline(data) {{
        const width = 1000;
        const height = 220;
        const paddingLeft = 120;
        const paddingRight = 40;
        const laneY = {{
          locations: 60,
          events: 120,
          attachments: 180,
        }};

        const allTimes = data.points
          .map((item) => item.time)
          .filter((value) => value !== null);
        let min = Math.min(...allTimes);
        let max = Math.max(...allTimes);
        if (!Number.isFinite(min) || !Number.isFinite(max)) {{
          min = Date.now();
          max = min + 3600000;
        }}
        if (min === max) {{
          max = min + 3600000;
        }}

        const scaleX = (value) => {{
          if (value === null) return paddingLeft;
          const ratio = (value - min) / (max - min);
          return paddingLeft + ratio * (width - paddingLeft - paddingRight);
        }};

        const axis = `
          <line x1="${{paddingLeft}}" y1="30" x2="${{width - paddingRight}}" y2="30" stroke="#bfb2a6" stroke-width="2" />
          <text x="${{paddingLeft}}" y="20" class="axis-label">${{fmtDate(min)}}</text>
          <text x="${{width - paddingRight}}" y="20" class="axis-label" text-anchor="end">${{fmtDate(max)}}</text>
        `;

        const laneLabels = `
          <text x="16" y="${{laneY.locations + 4}}" class="lane-label">Locations</text>
          <text x="16" y="${{laneY.events + 4}}" class="lane-label">Clinical Events</text>
          <text x="16" y="${{laneY.attachments + 4}}" class="lane-label">Attachments</text>
        `;

        const points = data.points
          .map((item) => {{
            const cx = scaleX(item.time);
            const cy = laneY[item.lane];
            const color =
              item.lane === "locations"
                ? "var(--accent)"
                : item.lane === "events"
                ? "var(--accent-2)"
                : "var(--accent-3)";
            return `
              <circle cx="${{cx}}" cy="${{cy}}" r="6" fill="${{color}}" />
              <text x="${{cx + 8}}" y="${{cy - 10}}" font-size="11" fill="#4a3f36">${{item.label}}</text>
            `;
          }})
          .join("");

        return `
          <svg viewBox="0 0 ${{width}} ${{height}}" role="img" aria-label="Timeline">
            ${{axis}}
            ${{laneLabels}}
            <line x1="${{paddingLeft}}" y1="${{laneY.locations}}" x2="${{width - paddingRight}}" y2="${{laneY.locations}}" stroke="#e1d5c9" />
            <line x1="${{paddingLeft}}" y1="${{laneY.events}}" x2="${{width - paddingRight}}" y2="${{laneY.events}}" stroke="#e1d5c9" />
            <line x1="${{paddingLeft}}" y1="${{laneY.attachments}}" x2="${{width - paddingRight}}" y2="${{laneY.attachments}}" stroke="#e1d5c9" />
            ${{points}}
          </svg>
        `;
      }}

      function buildPoints(timeline, trajectory, attachments) {{
        const points = [];
        for (const item of trajectory) {{
          points.push({{
            lane: "locations",
            time: toMillis(item.effective_at || item.effectiveAt),
            label: item.to_location || item.location || "Location",
          }});
        }}
        for (const item of timeline) {{
          const details = item.details || item;
          points.push({{
            lane: "events",
            time: toMillis(item.occurred_at || item.occurredAt),
            label: item.event_type || details?.label || "Event",
          }});
        }}
        for (const item of attachments) {{
          points.push({{
            lane: "attachments",
            time: toMillis(item.occurred_at || item.occurredAt),
            label: item.filename || "Attachment",
          }});
        }}
        return points;
      }}

      async function loadTimelines() {{
        const root = document.getElementById("timeline-root");
        root.innerHTML = "";
        try {{
          const patients = await fetchJson("/api/v1/patients?limit=2");
          const patientItems = patients.items || [];
          if (patientItems.length === 0) {{
            root.innerHTML = '<div class="card empty">No patients found.</div>';
            return;
          }}
          let index = 0;
          for (const patient of patientItems) {{
            index += 1;
            const patientId = patient.patient_id;
            const admissions = await fetchJson(`/api/v1/admissions?patient_id=${{patientId}}`);
            const admissionItems = admissions.items || [];
            if (admissionItems.length === 0) {{
              const card = document.createElement("div");
              card.className = "card";
              card.innerHTML = `<h2>Patient ${{index}}</h2><small>No admissions found.</small>`;
              root.appendChild(card);
              continue;
            }}
            const admission = admissionItems[0];
            const admissionId = admission.admission_id;

            const [timeline, trajectory, attachments] = await Promise.all([
              fetchJson(`/api/v1/admissions/${{admissionId}}/timeline`),
              fetchJson(`/api/v1/admissions/${{admissionId}}/trajectory`),
              fetchJson(`/api/v1/admissions/${{admissionId}}/attachments`),
            ]);

            const points = buildPoints(
              timeline.items || [],
              trajectory.items || [],
              attachments.items || [],
            );

            const card = document.createElement("div");
            card.className = "card";
            card.innerHTML = `
              <h2>Patient ${{index}}</h2>
              <small>Admission: ${{admissionId}}</small>
              <div class="legend">
                <span><i class="dot locations"></i>Locations</span>
                <span><i class="dot events"></i>Clinical events</span>
                <span><i class="dot attachments"></i>Attachments</span>
              </div>
              ${{points.length ? makeSvgTimeline({{points}}) : '<div class="empty">No timeline data for this admission.</div>'}}
            `;
            root.appendChild(card);
          }}
        }} catch (error) {{
          root.innerHTML = `<div class="card empty">Error loading timeline: ${{error.message}}</div>`;
        }}
      }}

      loadTimelines();
    </script>
  </body>
</html>
"""
    return Response(content=html, media_type="text/html")
