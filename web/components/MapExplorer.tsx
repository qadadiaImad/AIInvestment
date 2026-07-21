"use client";

import { useMemo, useState } from "react";
import type { CapitalWeb, ResiliencyNode, ChokepointsData } from "@/lib/data";
import { LAYER_LABELS, LAYER_ORDER } from "@/lib/format";
import { chokepointsForNode, type Chokepoint } from "@/lib/chokepoints";

const EMPTY_CHOKEPOINTS: Chokepoint[] = [];
import CapitalGraph, { type ColorMode } from "@/components/CapitalGraph";
import CompanyValueChain from "@/components/CompanyValueChain";
import NodeDetailPanel from "@/components/NodeDetailPanel";
import ChokepointSideList from "@/components/ChokepointSideList";
import ChokepointClaimsPanel from "@/components/ChokepointClaimsPanel";
import StressControls, { STRESS_ZERO, type StressState } from "@/components/StressControls";

type ViewMode = "global" | "company";

// Sector filter: "all" plus any concrete sector found on the nodes (AI/Quantum).
// A node belongs to a sector if its `sectors` array includes it; bridge nodes
// carry both and thus appear under either filter. The control is hidden when no
// node carries a `sectors` field (AI-only datasets remain unchanged).
type SectorFilter = string; // "all" | "AI" | "Quantum" | …

// `sectors` is an OPTIONAL field on the merged CapitalWeb node (see merge
// contract); read it defensively so AI-only data (no `sectors`) still works.
function nodeSectors(n: CapitalWeb["nodes"][number]): string[] | undefined {
  const s = (n as { sectors?: unknown }).sectors;
  return Array.isArray(s) ? (s.filter((x) => typeof x === "string") as string[]) : undefined;
}

function layerSortKey(layer?: string): number {
  if (!layer) return LAYER_ORDER.length + 1;
  const i = LAYER_ORDER.indexOf(layer);
  return i === -1 ? LAYER_ORDER.length : i;
}

export default function MapExplorer({
  web,
  resiliency,
  dffBase,
  chokepointsData,
}: {
  web: CapitalWeb;
  resiliency?: ResiliencyNode[];
  dffBase: number;
  // Supply-chain chokepoint layer (Round 6) — GENERATED/gitignored, may
  // legitimately be null (getChokepointsData() guard). The overlay toggle
  // hides entirely when null rather than rendering disabled-with-no-data.
  chokepointsData?: ChokepointsData | null;
}) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("global");
  const [colorMode, setColorMode] = useState<ColorMode>("layer");
  const [shock, setShock] = useState<StressState>(STRESS_ZERO);
  const [sector, setSector] = useState<SectorFilter>("all");
  const [chokepointMode, setChokepointMode] = useState(false);
  const [activeChokepointId, setActiveChokepointId] = useState<string | null>(null);
  const stressActive = shock.dRateBps !== 0 || shock.dElecPct !== 0;
  const companyMode = viewMode === "company";
  const hasChokepoints = !!chokepointsData && chokepointsData.chokepoints.length > 0;
  // Stable reference when the bundle is absent: a fresh [] every render would
  // retrigger CapitalGraph's full network-rebuild effect on every slider tick.
  const chokepoints = chokepointsData?.chokepoints ?? EMPTY_CHOKEPOINTS;
  const chokepointOverlayOn = chokepointMode && hasChokepoints && !companyMode;

  const activeChokepoint = activeChokepointId
    ? (chokepoints.find((cp) => cp.id === activeChokepointId) ?? null)
    : null;

  const linkedChokepoints = useMemo(() => {
    if (!chokepointsData || !selectedId) return [];
    return chokepointsForNode(chokepointsData, selectedId);
  }, [chokepointsData, selectedId]);

  function handleSelectChokepoint(id: string | null) {
    setActiveChokepointId(id);
  }

  // Distinct sectors present across nodes (e.g. ["AI", "Quantum"]). When empty,
  // the dataset is AI-only / unsectored and the sector control stays hidden.
  const sectorOptions = useMemo(() => {
    const seen = new Set<string>();
    for (const n of web.nodes) {
      const ss = nodeSectors(n);
      if (ss) for (const s of ss) seen.add(s);
    }
    return [...seen].sort();
  }, [web.nodes]);
  const hasSectors = sectorOptions.length > 0;

  // Filter the graph to the chosen sector: a node is kept if its `sectors`
  // includes the selection (bridges carry both, so they survive either filter);
  // an edge is kept only if BOTH endpoints survive. "all" (or unsectored data)
  // passes the original web through untouched.
  const filteredWeb = useMemo<CapitalWeb>(() => {
    if (!hasSectors || sector === "all") return web;
    const keptNodes = web.nodes.filter((n) => {
      const ss = nodeSectors(n);
      return ss ? ss.includes(sector) : false;
    });
    const keptIds = new Set(keptNodes.map((n) => n.id));
    const keptEdges = web.edges.filter(
      (e) => keptIds.has(e.src) && keptIds.has(e.dst),
    );
    return { nodes: keptNodes, edges: keptEdges };
  }, [web, sector, hasSectors]);

  // Selecting a node in the global graph drills into its company value chain.
  function handleGraphSelect(id: string | null) {
    setSelectedId(id);
    if (id) setViewMode("company");
  }

  // Build <optgroup>s grouped & ordered by layer (from the filtered nodes).
  const groups = useMemo(() => {
    const byLayer = new Map<string, CapitalWeb["nodes"]>();
    for (const n of filteredWeb.nodes) {
      const key = n.layer ?? "other";
      const arr = byLayer.get(key) ?? [];
      arr.push(n);
      byLayer.set(key, arr);
    }
    return [...byLayer.entries()]
      .sort((a, b) => layerSortKey(a[0]) - layerSortKey(b[0]))
      .map(([layer, nodes]) => ({
        layer,
        label: LAYER_LABELS[layer] ?? layer.toUpperCase(),
        nodes: [...nodes].sort((a, b) =>
          (a.name || a.id).localeCompare(b.name || b.id),
        ),
      }));
  }, [filteredWeb.nodes]);

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* selector bar */}
      <div className="flex flex-wrap items-center gap-2 px-3 py-2 border-b border-term-border">
        {/* view-mode toggle: Global graph | By company */}
        <div className="inline-flex rounded-sm border border-term-border overflow-hidden">
          {(
            [
              ["global", "Global graph"],
              ["company", "By company"],
            ] as [ViewMode, string][]
          ).map(([m, label]) => (
            <button
              key={m}
              type="button"
              onClick={() => setViewMode(m)}
              className={`px-2 py-1 text-[10.5px] uppercase tracking-wider transition-colors ${
                viewMode === m
                  ? "bg-emerald-500/20 text-emerald-300"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {companyMode && selectedId && (
          <button
            type="button"
            onClick={() => setViewMode("global")}
            className="text-[10.5px] text-zinc-400 hover:text-emerald-300"
          >
            ← Global graph
          </button>
        )}

        {/* Sector filter (All / AI / Quantum) — only when nodes carry sectors. */}
        {hasSectors && (
          <div className="inline-flex items-center gap-1.5">
            <span className="text-[10.5px] uppercase tracking-wider text-term-muted">
              Sector
            </span>
            <div className="inline-flex rounded-sm border border-term-border overflow-hidden">
              {(["all", ...sectorOptions] as SectorFilter[]).map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setSector(s)}
                  className={`px-2 py-1 text-[10.5px] uppercase tracking-wider transition-colors ${
                    sector === s
                      ? "bg-emerald-500/20 text-emerald-300"
                      : "text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  {s === "all" ? "All" : s}
                </button>
              ))}
            </div>
          </div>
        )}

        <label
          htmlFor="node-select"
          className="text-[10.5px] uppercase tracking-wider text-term-muted"
        >
          {companyMode ? "Company" : "Drill into node"}
        </label>
        <select
          id="node-select"
          value={selectedId ?? ""}
          onChange={(e) => setSelectedId(e.target.value || null)}
          className="bg-[#0b0f17] border border-term-border rounded-sm px-2 py-1 text-[11px] text-zinc-200 font-mono max-w-[280px] focus:outline-none focus:border-zinc-500"
        >
          <option value="">— select a node —</option>
          {groups.map((g) => (
            <optgroup key={g.layer} label={g.label}>
              {g.nodes.map((n) => (
                <option key={n.id} value={n.id}>
                  {(n.name || n.id) + (n.layer ? ` — ${n.layer}` : "")}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
        {selectedId && (
          <button
            type="button"
            onClick={() => setSelectedId(null)}
            className="text-[10.5px] text-zinc-500 hover:text-zinc-300 underline"
          >
            clear
          </button>
        )}

        {/* Color-by toggle: Layer | Health (applies to the global graph). */}
        <div
          className={`ml-auto flex items-center gap-2 ${
            companyMode ? "opacity-40 pointer-events-none" : ""
          }`}
          title={
            companyMode
              ? "Node coloring applies to the global graph."
              : undefined
          }
        >
          <span className="text-[10.5px] uppercase tracking-wider text-term-muted">
            Color nodes by
          </span>
          <div className="inline-flex rounded-sm border border-term-border overflow-hidden">
            {(["layer", "health"] as ColorMode[]).map((m) => (
              <button
                key={m}
                type="button"
                disabled={companyMode}
                onClick={() => setColorMode(m)}
                className={`px-2 py-1 text-[10.5px] uppercase tracking-wider transition-colors ${
                  colorMode === m
                    ? "bg-emerald-500/20 text-emerald-300"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {m}
              </button>
            ))}
          </div>
        </div>

        {/* Chokepoint overlay toggle — hidden entirely when chokepoints.json
            hasn't been generated (hasChokepoints false); disabled/grayed in
            company-view mode, matching the "Color nodes by" pattern above. */}
        {hasChokepoints && (
          <div
            className={companyMode ? "opacity-40 pointer-events-none" : ""}
            title={
              companyMode
                ? "Chokepoint overlay applies to the global graph."
                : undefined
            }
          >
            <button
              type="button"
              disabled={companyMode}
              onClick={() => {
                setChokepointMode((v) => !v);
                if (chokepointMode) setActiveChokepointId(null);
              }}
              className={`px-2 py-1 rounded-sm border text-[10.5px] uppercase tracking-wider transition-colors ${
                chokepointMode
                  ? "border-fuchsia-500/60 bg-fuchsia-500/15 text-fuchsia-300"
                  : "border-term-border text-zinc-400 hover:text-zinc-200"
              }`}
            >
              ⛓ Chokepoints
            </button>
          </div>
        )}
      </div>

      {/* macro-stress slider bar (compact) — applies to the global graph. */}
      <div
        className={`flex flex-wrap items-center gap-x-4 gap-y-1.5 px-3 py-2 border-b border-term-border bg-[#0a0d14] ${
          companyMode ? "opacity-40 pointer-events-none" : ""
        }`}
        aria-hidden={companyMode}
      >
        <span className="text-[9.5px] uppercase tracking-wider text-emerald-300/80">
          Macro stress
        </span>
        <StressControls value={shock} onChange={setShock} compact />
        <span className="text-[9px] text-term-muted ml-auto basis-full sm:basis-auto">
          {stressActive
            ? "Edges colored by live stress — green resilient → red stressed."
            : "Sliders at 0 / 0 — edges use default styling."}{" "}
          Illustrative client-side recompute (mirrors the Python model);
          indicative, not a dollar-loss. Not financial advice.
        </span>
      </div>

      {/* graph (or company value chain) + detail panel */}
      <div className="flex flex-col lg:flex-row flex-1 min-h-0">
        <div className="relative flex-1 min-h-[55vh] lg:min-h-0 bg-[#0b0f17]">
          {companyMode ? (
            <CompanyValueChain
              web={web}
              focalId={selectedId}
              onFocus={setSelectedId}
              resiliency={resiliency}
            />
          ) : (
            <CapitalGraph
              web={filteredWeb}
              resiliency={resiliency}
              colorMode={colorMode}
              selectedId={selectedId}
              onSelect={handleGraphSelect}
              stress={{
                dRateBps: shock.dRateBps,
                dElecPct: shock.dElecPct,
                dffBase,
              }}
              chokepoints={chokepoints}
              chokepointMode={chokepointOverlayOn}
              activeChokepointId={activeChokepointId}
              onSelectChokepoint={handleSelectChokepoint}
            />
          )}
        </div>
        <aside className="lg:w-[360px] shrink-0 border-t lg:border-t-0 lg:border-l border-term-border bg-[#0a0d14] min-h-[40vh] lg:min-h-0 lg:h-auto flex flex-col">
          {chokepointOverlayOn && (
            <>
              <ChokepointSideList
                chokepoints={chokepoints}
                activeId={activeChokepointId}
                onSelect={handleSelectChokepoint}
              />
              <ChokepointClaimsPanel cp={activeChokepoint} />
            </>
          )}
          <div className="flex-1 min-h-0 flex flex-col">
            <NodeDetailPanel
              web={web}
              selectedId={selectedId}
              resiliency={resiliency}
              linkedChokepoints={linkedChokepoints}
              onSelectChokepoint={(id) => {
                setChokepointMode(true);
                setActiveChokepointId(id);
              }}
            />
          </div>
        </aside>
      </div>
    </div>
  );
}
