"""Generate Karim VO for halal kit entries via the locked cloned voice; update the manifest.

    python higgs/_gen_halal_voice.py                 # newest kit
    python higgs/_gen_halal_voice.py --date 2026-07-21
    python higgs/_gen_halal_voice.py --dry-run       # lint + print commands, no spend

Refuses on: missing halal.json, lint errors, or a null voice id (course/persona/higgsfield-ids.json).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

HIGGS = pathlib.Path(__file__).resolve().parent
ROOT = HIGGS.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
from aiinvest.kit_md import parse_cfg                       # noqa: E402
from aiinvest.halal_join import load_halal, screen_card_data  # noqa: E402
from aiinvest.halal_lint import lint_halal_script           # noqa: E402
import re                                                    # noqa: E402

IDS = ROOT / "course/persona/higgsfield-ids.json"
MANIFEST = HIGGS / "reels_manifest.json"


def collect_halal_entries(md):
    out, seen = [], set()
    for tk in re.findall(r'"([A-Z0-9.]{1,12})":\{', md):
        if tk in seen:
            continue
        seen.add(tk)
        c = parse_cfg(md, tk)
        if c and c.get("halal_script"):
            out.append((tk, c["halal_script"].strip()))
    return out


def compose_tts_cmd(script, voice):
    if not voice.get("id"):
        raise SystemExit("voice.id is null in course/persona/higgsfield-ids.json — "
                         "create the cloned voice in the Higgsfield web UI first (see VOICE.md).")
    return ["higgsfield", "generate", "create", "text2speech_v2",
            "--prompt", script,
            "--variant", voice.get("variant", "elevenlabs"),
            "--voice_id", voice["id"],
            "--voice_type", voice.get("type", "element"),
            "--wait", "--json"]


def merge_manifest(manifest, date, tk, voice_url):
    manifest = dict(manifest)
    manifest["date"] = date
    reels = list(manifest.get("reels", []))
    for e in reels:
        if e.get("tk") == tk:
            e["voice"] = voice_url
            e["voice_name"] = "Karim"
            break
    else:
        reels.append({"tk": tk, "hero": "", "voice": voice_url, "voice_name": "Karim"})
    manifest["reels"] = reels
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    from _build_v4 import pick_kit  # local import: same conventions
    kit = pick_kit(HIGGS, args.date, None)
    if not kit or not kit.exists():
        raise SystemExit(f"no kit found ({kit})")
    md = kit.read_text(encoding="utf-8")
    m = re.search(r"reels_(\d{4}-\d{2}-\d{2})_kit", kit.name)
    date = args.date or (m.group(1) if m else "")

    verdicts, warns = load_halal(ROOT / "web/public/data/halal.json")
    for w in warns:
        print("WARN", w)

    voice = json.loads(IDS.read_text(encoding="utf-8")).get("voice") or {}
    entries = collect_halal_entries(md)
    if not entries:
        print("no halal_script entries in kit — nothing to do")
        return 0

    failed = False
    for tk, script in entries:
        card = screen_card_data(verdicts, tk)
        if card is None:
            print(f"SKIP {tk}: not in halal.json")
            continue
        errs = lint_halal_script(script, card)
        if errs:
            failed = True
            for e in errs:
                print(f"LINT {tk}: {e}")
            continue
        cmd = compose_tts_cmd(script, voice)
        if args.dry_run:
            print(f"DRY {tk}:", " ".join(cmd[:8]), "...")
            continue
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"TTS failed for {tk}:\n{r.stderr[-800:]}")
        url = ""
        for line in (r.stdout or "").splitlines():
            line = line.strip()
            if line.startswith("http") and (".mp3" in line or ".wav" in line or ".m4a" in line):
                url = line
        if not url:
            try:
                doc = json.loads(r.stdout)
                if isinstance(doc, list):
                    doc = doc[0]
                url = doc.get("result_url") or doc.get("url") or ""
            except Exception:
                pass
        if not url:
            raise SystemExit(f"could not find voice URL in CLI output for {tk}:\n{r.stdout[-800:]}")
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {"reels": []}
        MANIFEST.write_text(json.dumps(merge_manifest(manifest, date, tk, url), indent=1),
                            encoding="utf-8")
        print(f"OK {tk} voice -> {url}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
