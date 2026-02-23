"use client";

import { useMemo, useState } from "react";
import { WorkspaceShell } from "@/components/workspace-shell";

type NodeItem = {
  id: string;
  label: string;
  lane: string;
  x: number;
  y: number;
  w: number;
  h: number;
  details: string;
};

type EdgeItem = {
  id: string;
  from: string;
  to: string;
};

const lanes = [
  { id: "ui", label: "UI Layer", x: 60 },
  { id: "api", label: "API Layer", x: 350 },
  { id: "agent", label: "Agent Layer", x: 640 },
  { id: "mcp", label: "MCP Tools", x: 930 },
  { id: "provider", label: "Provider Layer", x: 1220 },
  { id: "data", label: "Data + Obs", x: 1510 },
];

const nodes: NodeItem[] = [
  { id: "n1", label: "User", lane: "ui", x: 60, y: 90, w: 220, h: 54, details: "End user interacts via login, compose, and feedback flows." },
  { id: "n2", label: "Compose UI", lane: "ui", x: 60, y: 175, w: 220, h: 54, details: "Text + voice input with intent/tone/language controls." },
  { id: "n3", label: "Preview UI", lane: "ui", x: 60, y: 260, w: 220, h: 54, details: "Draft rendering, copy, playback, and score visibility." },

  { id: "n4", label: "JWT Auth", lane: "api", x: 350, y: 90, w: 220, h: 54, details: "Registration/login/token verification and role access checks." },
  { id: "n5", label: "Draft API", lane: "api", x: 350, y: 175, w: 220, h: 54, details: "Handles draft generation with replay protection and limits." },
  { id: "n6", label: "Observability API", lane: "api", x: 350, y: 260, w: 220, h: 54, details: "Serves live/global metrics, alerts, and integration status." },

  { id: "n7", label: "Input + Intent Guard", lane: "agent", x: 640, y: 90, w: 220, h: 54, details: "Blocks non-email requests and insufficient context prompts." },
  { id: "n8", label: "Refiner + Personalization", lane: "agent", x: 640, y: 175, w: 220, h: 54, details: "Context enrichment, prompt refinement, and profile memory use." },
  { id: "n9", label: "Writer + Validator + Router", lane: "agent", x: 640, y: 260, w: 220, h: 54, details: "Draft generation, quality review, retries, and fallback routing." },

  { id: "n10", label: "search_web", lane: "mcp", x: 930, y: 90, w: 220, h: 54, details: "MCP tool to fetch contextual web signals and citations." },
  { id: "n11", label: "voice.transcribe/speak", lane: "mcp", x: 930, y: 175, w: 220, h: 54, details: "Speech transcription and text-to-speech capabilities." },
  { id: "n12", label: "memory.upsert_profile", lane: "mcp", x: 930, y: 260, w: 220, h: 54, details: "Updates profile memory and thread-level context." },

  { id: "n13", label: "OpenAI / Deepgram / Tavily", lane: "provider", x: 1220, y: 132, w: 220, h: 54, details: "External model and search providers powering generation/tools." },
  { id: "n14", label: "LangSmith Tracing", lane: "provider", x: 1220, y: 238, w: 220, h: 54, details: "Agent execution traces and quality/latency observability." },

  { id: "n15", label: "PostgreSQL", lane: "data", x: 1510, y: 110, w: 220, h: 54, details: "Source of truth for auth, drafts, scores, evaluations, logs." },
  { id: "n16", label: "Chroma Vector Memory", lane: "data", x: 1510, y: 195, w: 220, h: 54, details: "Vectorized memory for retrieval and personalization context." },
  { id: "n17", label: "Global Metrics + Alerts", lane: "data", x: 1510, y: 280, w: 220, h: 54, details: "Derived operational metrics and threshold-based alert evaluation." },
];

const edges: EdgeItem[] = [
  { id: "e1", from: "n1", to: "n4" },
  { id: "e2", from: "n2", to: "n5" },
  { id: "e3", from: "n3", to: "n6" },
  { id: "e4", from: "n5", to: "n7" },
  { id: "e5", from: "n5", to: "n8" },
  { id: "e6", from: "n5", to: "n9" },
  { id: "e7", from: "n8", to: "n10" },
  { id: "e8", from: "n8", to: "n12" },
  { id: "e9", from: "n9", to: "n11" },
  { id: "e10", from: "n10", to: "n13" },
  { id: "e11", from: "n11", to: "n13" },
  { id: "e12", from: "n12", to: "n16" },
  { id: "e13", from: "n9", to: "n15" },
  { id: "e14", from: "n6", to: "n17" },
  { id: "e15", from: "n9", to: "n14" },
];

function edgePath(from: NodeItem, to: NodeItem): string {
  const x1 = from.x + from.w;
  const y1 = from.y + from.h / 2;
  const x2 = to.x;
  const y2 = to.y + to.h / 2;
  const dx = Math.max(40, (x2 - x1) * 0.45);
  return `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;
}

export default function ArchitectureMapPage() {
  const [zoom, setZoom] = useState(100);
  const [selected, setSelected] = useState<NodeItem>(nodes[0]);
  const scale = useMemo(() => Math.max(0.6, Math.min(1.6, zoom / 100)), [zoom]);

  const nodeById = useMemo(() => {
    const map = new Map<string, NodeItem>();
    for (const node of nodes) map.set(node.id, node);
    return map;
  }, []);

  return (
    <WorkspaceShell
      title="Interactive Architecture Map"
      subtitle="Zoomable SVG system map with connected flows and node-level details."
      allowGuest
    >
      {() => (
        <div className="grid ops-grid">
          <section className="card">
            <h2>Map Controls</h2>
            <p className="meta">Use zoom and node selection for deep-dive architecture walkthroughs.</p>
            <div className="timeline-row">
              <span className="meta">60%</span>
              <input type="range" min={60} max={160} value={zoom} onChange={(e) => setZoom(Number(e.target.value))} />
              <span className="meta">160%</span>
            </div>
            <p className="meta">Current zoom: {zoom}%</p>
          </section>

          <section className="card">
            <h2>Selected Node</h2>
            <div className="info-item">
              <h3>{selected.label}</h3>
              <p className="meta">{selected.details}</p>
            </div>
          </section>

          <section className="card">
            <h2>System Map</h2>
            <p className="meta">Click any block to inspect the component role and system behavior.</p>
            <div className="svg-map-shell">
              <svg className="svg-map-canvas" viewBox="0 0 1800 390" style={{ transform: `scale(${scale})` }} role="img" aria-label="Architecture map">
                <defs>
                  <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
                    <polygon points="0 0, 8 3, 0 6" fill="#8ecfff" />
                  </marker>
                </defs>

                {lanes.map((lane) => (
                  <g key={lane.id}>
                    <text x={lane.x} y={46} className="svg-lane-title">{lane.label}</text>
                    <line x1={lane.x - 10} y1={56} x2={lane.x + 240} y2={56} className="svg-lane-line" />
                  </g>
                ))}

                {edges.map((edge) => {
                  const from = nodeById.get(edge.from);
                  const to = nodeById.get(edge.to);
                  if (!from || !to) return null;
                  return (
                    <path key={edge.id} d={edgePath(from, to)} className="svg-edge" markerEnd="url(#arrowhead)" />
                  );
                })}

                {nodes.map((node) => {
                  const isActive = selected.id === node.id;
                  return (
                    <g key={node.id} onClick={() => setSelected(node)} className="svg-node-group" tabIndex={0}>
                      <title>{node.label}</title>
                      <rect x={node.x} y={node.y} rx={10} ry={10} width={node.w} height={node.h} className={isActive ? "svg-node active" : "svg-node"} />
                      <text x={node.x + node.w / 2} y={node.y + node.h / 2 + 4} textAnchor="middle" className="svg-node-text">
                        {node.label}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
          </section>
        </div>
      )}
    </WorkspaceShell>
  );
}
