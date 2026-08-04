import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const CANDIDATES_PATH = path.join(__dirname, "_candidates.json");
const CATALOG_PATH = path.join(__dirname, "catalog.json");

const BROWS = new Set(["flat", "raise", "furrow", "sad"]);
const EYES = new Set(["open", "blink", "wide", "dead", "sideL", "sideR"]);
const MOUTH = new Set(["flat", "open", "frown", "smile", "grimace", "o"]);
const PROP = new Set(["none", "fiddle", "paper", "phone", "pointer"]);

function isObj(v) {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function validateArm(arm, label) {
  if (arm === undefined) return null;
  if (!isObj(arm)) return `${label} must be an object`;
  for (const key of ["shoulder", "elbow", "wrist"]) {
    if (key in arm) {
      const v = arm[key];
      if (typeof v !== "number" || !Number.isFinite(v)) {
        return `${label}.${key} must be a finite number`;
      }
    }
  }
  if ("elbow" in arm && Math.abs(arm.elbow) > 150) {
    return `${label}.elbow must satisfy |elbow| <= 150 (got ${arm.elbow})`;
  }
  return null;
}

function validatePatch(patch) {
  if (!isObj(patch)) return "patch must be an object";

  if (patch.brows !== undefined) {
    if (!isObj(patch.brows)) return "brows must be an object";
    if (patch.brows.l !== undefined && !BROWS.has(patch.brows.l)) {
      return `brows.l invalid: ${patch.brows.l}`;
    }
    if (patch.brows.r !== undefined && !BROWS.has(patch.brows.r)) {
      return `brows.r invalid: ${patch.brows.r}`;
    }
  }

  if (patch.eyes !== undefined && !EYES.has(patch.eyes)) {
    return `eyes invalid: ${patch.eyes}`;
  }

  if (patch.mouth !== undefined && !MOUTH.has(patch.mouth)) {
    return `mouth invalid: ${patch.mouth}`;
  }

  if (patch.prop !== undefined && !PROP.has(patch.prop)) {
    return `prop invalid: ${patch.prop}`;
  }

  const armLErr = validateArm(patch.armL, "armL");
  if (armLErr) return armLErr;

  const armRErr = validateArm(patch.armR, "armR");
  if (armRErr) return armRErr;

  return null;
}

function main() {
  const raw = fs.readFileSync(CANDIDATES_PATH, "utf8");
  const candidates = JSON.parse(raw);

  if (!Array.isArray(candidates)) {
    throw new Error("_candidates.json must contain a JSON array");
  }

  const seenIds = new Set();
  const catalog = [];
  let dupCount = 0;
  let invalidCount = 0;

  for (const entry of candidates) {
    if (!isObj(entry) || typeof entry.id !== "string" || !entry.id) {
      invalidCount++;
      continue;
    }
    if (seenIds.has(entry.id)) {
      dupCount++;
      continue;
    }

    const err = validatePatch(entry.patch);
    if (err) {
      invalidCount++;
      console.warn(`skip "${entry.id}": ${err}`);
      continue;
    }

    seenIds.add(entry.id);

    const tags = Array.isArray(entry.tags) ? entry.tags : [];
    const baseDesc = entry.id.replace(/_/g, " ");
    const desc = tags.length > 0 ? `${baseDesc} (${tags.join(", ")})` : baseDesc;

    catalog.push({
      id: entry.id,
      params: entry.patch,
      desc,
      tags,
    });
  }

  fs.writeFileSync(CATALOG_PATH, JSON.stringify(catalog, null, 2) + "\n", "utf8");

  console.log(`catalog.json: ${catalog.length} valid entries (of ${candidates.length} candidates)`);
}

main();
