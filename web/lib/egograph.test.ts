import { describe, it, expect } from "vitest";
import {
  RELATION_SEMANTICS,
  buildEgoModel,
  formatTerms,
  relationKindMeta,
} from "./egograph";
import type { CapitalWeb } from "./data";

// ---------------------------------------------------------------------------
// Fixtures mirroring the shape of the real capital_web in public/data/site.json
// (verified against the four worked cases in the spec, section 4).
// ---------------------------------------------------------------------------

const nodes = [
  { id: "NVDA", name: "NVDA", type: "public", ticker: "NASDAQ:NVDA", layer: "L1-chips" },
  { id: "TSM", name: "TSM", type: "public", ticker: "NYSE:TSM", layer: "L1-chips" },
  { id: "MSFT", name: "MSFT", type: "public", ticker: "NASDAQ:MSFT", layer: "L2-infra" },
  { id: "GOOGL", name: "GOOGL", type: "public", ticker: "NASDAQ:GOOGL", layer: "L2-infra" },
  { id: "openai", name: "OpenAI", type: "private", layer: "private-lab" },
  { id: "anthropic", name: "Anthropic", type: "private", layer: "private-lab" },
];

// NVDA --customer--> TSM  (NVDA buys from TSM; TSM is NVDA's supplier)
const customerEdge = {
  src: "NVDA",
  dst: "TSM",
  type: "customer",
  attrs: { note: "leading-edge foundry" },
  certainty: "reported",
  source_url: "brief Part C (late May 2026)",
  as_of: "2026-05",
};

// MSFT --infra_partner--> openai  (MSFT supplies openai; MSFT is openai's supplier)
const infraEdge = {
  src: "MSFT",
  dst: "openai",
  type: "infra_partner",
  attrs: { note: "Azure compute" },
  certainty: "reported",
  source_url: "brief Part C (late May 2026)",
  as_of: "2026-05",
};

// GOOGL --equity_stake--> anthropic  (GOOGL invests in anthropic; GOOGL is a backer)
const equityEdge = {
  src: "GOOGL",
  dst: "anthropic",
  type: "equity_stake",
  attrs: { pct: 14, cap_pct: 15 },
  certainty: "reported",
  source_url: "brief Part C (late May 2026)",
  as_of: "2026-05",
};

function web(edges: CapitalWeb["edges"]): CapitalWeb {
  return { nodes, edges };
}

describe("RELATION_SEMANTICS", () => {
  it("is the single source of truth for the known edge types", () => {
    expect(RELATION_SEMANTICS.customer.flow).toBe("src_buys_from_dst");
    expect(RELATION_SEMANTICS.compute_commitment.flow).toBe("src_buys_from_dst");
    expect(RELATION_SEMANTICS.infra_partner.flow).toBe("src_supplies_dst");
    expect(RELATION_SEMANTICS.equity_stake.flow).toBe("capital");
    expect(RELATION_SEMANTICS.subsidiary.flow).toBe("capital");
    expect(RELATION_SEMANTICS.voting_power.flow).toBe("capital");
  });

  it("classifies the new quantum edge types", () => {
    // capital flow: acquired / subsidiary / spinout (same as equity_stake).
    expect(RELATION_SEMANTICS.acquired.flow).toBe("capital");
    expect(RELATION_SEMANTICS.spinout.flow).toBe("capital");
    // cloud_on — like compute_commitment (src buys compute from dst).
    expect(RELATION_SEMANTICS.cloud_on.flow).toBe("src_buys_from_dst");
    // supplier — like infra_partner (src supplies dst).
    expect(RELATION_SEMANTICS.supplier.flow).toBe("src_supplies_dst");
  });
});

// ---------------------------------------------------------------------------
// New quantum edge types (acquired/subsidiary/spinout/cloud_on/supplier).
// ---------------------------------------------------------------------------

describe("buildEgoModel — acquired (capital, like equity_stake)", () => {
  // NVDA --acquired--> openai  (NVDA acquired openai => openai is a holding)
  const acquiredEdge = {
    src: "NVDA",
    dst: "openai",
    type: "acquired",
    attrs: { usd: 1075000000 },
    certainty: "filed",
  };
  const w = web([acquiredEdge]);

  it("for the acquirer (src), the target is an output/capital-out (a holding)", () => {
    const m = buildEgoModel(w, "NVDA");
    expect(m.inputs).toHaveLength(0);
    expect(m.outputs).toHaveLength(1);
    const oa = m.outputs[0];
    expect(oa.id).toBe("openai");
    expect(oa.side).toBe("output");
    expect(oa.kind).toBe("capital");
  });

  it("for the target (dst), the acquirer is an input/capital-in (a parent)", () => {
    const m = buildEgoModel(w, "openai");
    expect(m.outputs).toHaveLength(0);
    expect(m.inputs).toHaveLength(1);
    const nvda = m.inputs[0];
    expect(nvda.id).toBe("NVDA");
    expect(nvda.side).toBe("input");
    expect(nvda.kind).toBe("capital");
  });
});

describe("buildEgoModel — subsidiary (capital)", () => {
  // MSFT --subsidiary--> anthropic  (MSFT parent => anthropic the holding)
  const subEdge = {
    src: "MSFT",
    dst: "anthropic",
    type: "subsidiary",
    attrs: { note: "majority" },
    certainty: "reported",
  };
  const w = web([subEdge]);

  it("for the parent (src), the subsidiary is an output/capital-out", () => {
    const m = buildEgoModel(w, "MSFT");
    expect(m.inputs).toHaveLength(0);
    expect(m.outputs).toHaveLength(1);
    expect(m.outputs[0].id).toBe("anthropic");
    expect(m.outputs[0].side).toBe("output");
    expect(m.outputs[0].kind).toBe("capital");
  });

  it("for the subsidiary (dst), the parent is an input/capital-in", () => {
    const m = buildEgoModel(w, "anthropic");
    expect(m.outputs).toHaveLength(0);
    expect(m.inputs).toHaveLength(1);
    expect(m.inputs[0].id).toBe("MSFT");
    expect(m.inputs[0].side).toBe("input");
    expect(m.inputs[0].kind).toBe("capital");
  });
});

describe("buildEgoModel — spinout (capital)", () => {
  // GOOGL --spinout--> anthropic  (anthropic spun out of GOOGL => a holding/output)
  const spinEdge = {
    src: "GOOGL",
    dst: "anthropic",
    type: "spinout",
    attrs: { note: "SandboxAQ-style" },
    certainty: "reported",
  };
  const w = web([spinEdge]);

  it("for the parent (src), the spinout is an output/capital-out", () => {
    const m = buildEgoModel(w, "GOOGL");
    expect(m.inputs).toHaveLength(0);
    expect(m.outputs).toHaveLength(1);
    expect(m.outputs[0].id).toBe("anthropic");
    expect(m.outputs[0].side).toBe("output");
    expect(m.outputs[0].kind).toBe("capital");
  });

  it("for the spinout (dst), the parent is an input/capital-in (a backer)", () => {
    const m = buildEgoModel(w, "anthropic");
    expect(m.outputs).toHaveLength(0);
    expect(m.inputs).toHaveLength(1);
    expect(m.inputs[0].id).toBe("GOOGL");
    expect(m.inputs[0].side).toBe("input");
    expect(m.inputs[0].kind).toBe("capital");
  });
});

describe("buildEgoModel — cloud_on (src buys compute from dst)", () => {
  // openai --cloud_on--> MSFT  (openai runs on MSFT's cloud => MSFT is supplier)
  const cloudEdge = {
    src: "openai",
    dst: "MSFT",
    type: "cloud_on",
    attrs: { note: "Azure" },
    certainty: "reported",
  };
  const w = web([cloudEdge]);

  it("for the customer (src), the cloud provider is an input/compute (the supplier)", () => {
    const m = buildEgoModel(w, "openai");
    expect(m.outputs).toHaveLength(0);
    expect(m.inputs).toHaveLength(1);
    const msft = m.inputs[0];
    expect(msft.id).toBe("MSFT");
    expect(msft.side).toBe("input");
    expect(msft.kind).toBe("compute");
  });

  it("for the cloud provider (dst), the customer is an output/compute", () => {
    const m = buildEgoModel(w, "MSFT");
    expect(m.inputs).toHaveLength(0);
    expect(m.outputs).toHaveLength(1);
    const oa = m.outputs[0];
    expect(oa.id).toBe("openai");
    expect(oa.side).toBe("output");
    expect(oa.kind).toBe("compute");
  });
});

describe("buildEgoModel — supplier (src supplies dst)", () => {
  // TSM --supplier--> NVDA  (TSM supplies NVDA => NVDA is the customer)
  const supplierEdge = {
    src: "TSM",
    dst: "NVDA",
    type: "supplier",
    attrs: { product: "lasers" },
    certainty: "reported",
  };
  const w = web([supplierEdge]);

  it("for the supplier (src), the buyer is an output/supply (the customer)", () => {
    const m = buildEgoModel(w, "TSM");
    expect(m.inputs).toHaveLength(0);
    expect(m.outputs).toHaveLength(1);
    const nvda = m.outputs[0];
    expect(nvda.id).toBe("NVDA");
    expect(nvda.side).toBe("output");
    expect(nvda.kind).toBe("supply");
  });

  it("for the buyer (dst), the supplier is an input/supply", () => {
    const m = buildEgoModel(w, "NVDA");
    expect(m.outputs).toHaveLength(0);
    expect(m.inputs).toHaveLength(1);
    const tsm = m.inputs[0];
    expect(tsm.id).toBe("TSM");
    expect(tsm.side).toBe("input");
    expect(tsm.kind).toBe("supply");
  });
});

describe("buildEgoModel — customer (NVDA -> TSM)", () => {
  const w = web([customerEdge]);

  it("for NVDA, TSM is an input/supply (the supplier)", () => {
    const m = buildEgoModel(w, "NVDA");
    expect(m.focal.id).toBe("NVDA");
    expect(m.outputs).toHaveLength(0);
    expect(m.inputs).toHaveLength(1);
    const tsm = m.inputs[0];
    expect(tsm.id).toBe("TSM");
    expect(tsm.name).toBe("TSM");
    expect(tsm.side).toBe("input");
    expect(tsm.kind).toBe("supply");
    expect(tsm.relations[0].type).toBe("customer");
    expect(tsm.relations[0].certainty).toBe("reported");
    expect(m.counts.inputs).toBe(1);
    expect(m.counts.outputs).toBe(0);
  });

  it("for TSM, NVDA is an output (the customer)", () => {
    const m = buildEgoModel(w, "TSM");
    expect(m.inputs).toHaveLength(0);
    expect(m.outputs).toHaveLength(1);
    const nvda = m.outputs[0];
    expect(nvda.id).toBe("NVDA");
    expect(nvda.side).toBe("output");
  });
});

describe("buildEgoModel — infra_partner (MSFT -> openai)", () => {
  const w = web([infraEdge]);

  it("for openai, MSFT is an input/supply (the supplier)", () => {
    const m = buildEgoModel(w, "openai");
    expect(m.inputs).toHaveLength(1);
    expect(m.outputs).toHaveLength(0);
    const msft = m.inputs[0];
    expect(msft.id).toBe("MSFT");
    expect(msft.side).toBe("input");
    expect(msft.kind).toBe("supply");
  });

  it("for MSFT, openai is an output", () => {
    const m = buildEgoModel(w, "MSFT");
    expect(m.outputs).toHaveLength(1);
    expect(m.inputs).toHaveLength(0);
    const oa = m.outputs[0];
    expect(oa.id).toBe("openai");
    expect(oa.name).toBe("OpenAI");
    expect(oa.side).toBe("output");
  });
});

describe("buildEgoModel — equity_stake (GOOGL -> anthropic)", () => {
  const w = web([equityEdge]);

  it("for anthropic, GOOGL is an input/capital-in (the backer)", () => {
    const m = buildEgoModel(w, "anthropic");
    expect(m.inputs).toHaveLength(1);
    expect(m.outputs).toHaveLength(0);
    const g = m.inputs[0];
    expect(g.id).toBe("GOOGL");
    expect(g.side).toBe("input");
    expect(g.kind).toBe("capital");
  });

  it("for GOOGL, anthropic is an output/capital-out (the holding)", () => {
    const m = buildEgoModel(w, "GOOGL");
    expect(m.outputs).toHaveLength(1);
    expect(m.inputs).toHaveLength(0);
    const a = m.outputs[0];
    expect(a.id).toBe("anthropic");
    expect(a.side).toBe("output");
    expect(a.kind).toBe("capital");
  });
});

describe("buildEgoModel — pair aggregation", () => {
  it("aggregates multiple edges between the same pair into one Counterparty", () => {
    // Two distinct edges, same (NVDA, TSM) pair, both classify TSM as an input.
    const second = {
      src: "NVDA",
      dst: "TSM",
      type: "infra_partner", // MSFT-> for NVDA->TSM infra_partner: dst is customer => output
    };
    // Instead use two edges that land on the SAME side: customer + compute_commitment
    const compute = {
      src: "NVDA",
      dst: "TSM",
      type: "compute_commitment",
      attrs: { usd: 1000000000 },
      certainty: "reported",
    };
    const m = buildEgoModel(web([customerEdge, compute]), "NVDA");
    expect(m.inputs).toHaveLength(1);
    const tsm = m.inputs[0];
    expect(tsm.id).toBe("TSM");
    expect(tsm.relations).toHaveLength(2);
    const types = tsm.relations.map((r) => r.type).sort();
    expect(types).toEqual(["compute_commitment", "customer"]);
    void second;
  });

  it("places a pair that is both input and output on both sides", () => {
    // MSFT -> openai infra_partner (openai input) AND openai -> MSFT
    // compute_commitment (openai buys from MSFT => for openai, MSFT is input too).
    // Use a genuine both-sides case from MSFT's perspective:
    //   MSFT -> openai infra_partner  => openai is MSFT's output
    //   openai -> MSFT customer        => openai buys from MSFT => MSFT is supplier =>
    //                                     for MSFT (= dst), openai (= src) is the customer => output
    // To get both sides, combine infra_partner (output) with equity_stake where MSFT is dst.
    const backer = {
      src: "openai",
      dst: "MSFT",
      type: "equity_stake", // openai invests in MSFT => for MSFT, openai is backer (input)
      attrs: { note: "x" },
    };
    const m = buildEgoModel(web([infraEdge, backer]), "MSFT");
    expect(m.outputs.some((c) => c.id === "openai")).toBe(true);
    expect(m.inputs.some((c) => c.id === "openai")).toBe(true);
  });
});

describe("buildEgoModel — sorting by salience", () => {
  it("sorts by usd salience desc, then count, then name", () => {
    const big = {
      src: "NVDA",
      dst: "TSM",
      type: "customer",
      attrs: { usd: 9000000000 },
    };
    const small = {
      src: "NVDA",
      dst: "openai",
      type: "customer",
      attrs: { usd: 1000000 },
    };
    const m = buildEgoModel(web([small, big]), "NVDA");
    expect(m.inputs.map((c) => c.id)).toEqual(["TSM", "openai"]);
  });
});

describe("buildEgoModel — unknown type", () => {
  it("falls back to kind 'related' and still places the counterparty", () => {
    const weird = { src: "NVDA", dst: "TSM", type: "mystery_link" };
    const m = buildEgoModel(web([weird]), "NVDA");
    // focal = src, unknown flow => output (best-effort)
    expect(m.outputs).toHaveLength(1);
    expect(m.outputs[0].kind).toBe("related");
    expect(m.outputs[0].relations[0].kind).toBe("related");
  });
});

describe("formatTerms", () => {
  it("renders usd / power / gpus / tpus compactly", () => {
    const s = formatTerms({
      usd: 200000000000,
      power_gw: 1,
      tpus: 1000000,
    });
    expect(s).toContain("$200.0B");
    expect(s).toContain("1 GW");
    expect(s).toContain("1M TPUs");
  });

  it("renders a *_usd key and a product, omits low-signal keys", () => {
    const s = formatTerms({
      contract_usd: 40000000000,
      product: "H100 GPUs",
      retrieved_at: "2026-05-30T00:00:00Z",
      origin: "curated",
    });
    expect(s).toContain("$40.0B");
    expect(s).toContain("H100 GPUs");
    expect(s).not.toContain("curated");
    expect(s).not.toContain("retrieved_at");
  });

  it("renders pct/stake_pct and gpus", () => {
    expect(formatTerms({ pct: 14 })).toContain("14%");
    expect(formatTerms({ stake_pct: 15 })).toContain("15%");
    expect(formatTerms({ gpus: 100000 })).toContain("100K GPUs");
    expect(formatTerms({ power_mw: 500 })).toContain("500 MW");
  });

  it("returns an empty string when no recognized term is present", () => {
    expect(formatTerms({ transactions: [] })).toBe("");
    expect(formatTerms(undefined)).toBe("");
  });
});

describe("relationKindMeta", () => {
  it("returns a label + color class for each kind", () => {
    for (const k of ["supply", "compute", "capital", "related"] as const) {
      const meta = relationKindMeta(k);
      expect(typeof meta.label).toBe("string");
      expect(meta.label.length).toBeGreaterThan(0);
      expect(typeof meta.colorCls).toBe("string");
      expect(meta.colorCls.length).toBeGreaterThan(0);
    }
  });
});
