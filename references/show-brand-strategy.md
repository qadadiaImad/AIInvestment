# Sol & Rex News — brand strategy

**Owner rule, 2026-08-08.** How the show's fixed identity and its
per-episode variables are separated. Read before making any opening card,
profile asset or new vertical.

---

## 1. The rule

> One opening image per **vertical**. Every episode inside that vertical
> reuses the same background and the same cast art; **only the text
> changes**. If the vertical changes, **everything** changes — new
> background, and the cast get new clothes.

A "vertical" is a subject area, not a topic. Finance is one. History would
be another. Politics might be another, or might sit inside one of those —
that is an editorial call, not a technical one.

### Why this is the rule

Six reels that share a set, a colour, a wordmark and a lighting scheme read
as **one channel**. Six reels that each invent their own opening read as
six channels, and the audience never accumulates recognition. The variable
that carries the episode is the **title**, and it is the only thing that
should move.

The corollary matters just as much: **the wardrobe is part of the set.**
Sol's burgundy cardigan and yellow bow tie belong to the finance desk. Put
that costume in front of a history set and the frame contradicts itself —
so a new vertical is a full re-dress, not a background swap.

---

## 2. Fixed vs swap, precisely

Implemented in `scripts/vector/make_opening.py`. The card is 1080×1920 and
has exactly two zones.

| zone | y-range | contents | changes |
|------|---------|----------|---------|
| **FIXED** | 150–406 | amber rule · `SOL & REX` · `NEWS` · teal rule | never, within a vertical |
| **SWAP** | 470–900 | episode number, title (max 2 lines) | every episode |
| **FIXED** | 900–1920 | the set, and the cast at the desk | never, within a vertical |

Nothing outside the swap zone may move between episodes. A title card whose
furniture shifts reads as a different show.

**Title limit:** Rockwell Bold at 120px fits roughly 11 characters per
line. The script *warns* on overflow rather than clipping silently —
ep.3/4/5 currently trip it and need shorter titles.

---

## 3. Who generates what

This split is not stylistic; each half was learned by failing the other way.

| element | tool | why |
|---|---|---|
| **opening set** | **grok-cli** (`grok-cli image`, Grok Imagine) | handles a rich lit studio far better than the local models. Generated once per vertical, committed as a finished asset. |
| **cast** | **canon RGBA renders only** — never generated | grok has no idea who Sol and Rex are and invents two strangers. Same for any fresh SDXL pass: prompt+seed cannot hold identity (measured — three poses, three different people). |
| **all lettering** | **code** (PIL / Remotion, real font) | image models cannot render text. This project has produced "STODUIL", garbled Japanese twice, and fake numerals. A title card is typography. |
| **wall exhibits** | **Z-Image** | see [[market-lessons-handoff]] §4 |

`grok-cli` is authenticated via SuperGrok OAuth at `~/tools/grok-cli`, no
API key. `grok-cli image --aspect-ratio 9:16 --resolution 1k` returns a URL;
download it and commit the asset.

---

## 4. The finance vertical, as built

```
VERTICAL = {
    "name": "finance",
    "set":  "set_a.jpg",     # grok: news studio, chart wall, amber ticker
    "sol":  "sol_smug_v1",   # burgundy cardigan, yellow bow tie
    "rex":  "rex_skeptic",   # grey vest, white shirt
}
```

Palette, shared with the episodes themselves: navy `#0B1220`, cream
`#F4EEE0`, amber `#E8B054`, teal `#7CE0A2`.

### Starting a new vertical

1. Generate a new set with grok at 9:16, no people and no text in the
   prompt — the cast and the type are added in code.
2. Re-dress the cast. This needs **new canon art**, which means masked
   inpainting from an approved base (proven: identity outside the mask is
   pixel-identical) — not a fresh generation.
3. Copy the `VERTICAL` block, change all three fields together.
4. Everything else — layout, type, rules, colours — stays.

---

## 5. Brand assets

| asset | file |
|---|---|
| logo, square | `content/brand/logo/logo_news_square.png` |
| logo, horizontal | `content/brand/logo/logo_news_horizontal.png` |
| bow-tie mark, cut out | `content/brand/logo/_bowtie_cut.png` |
| profile picture | `content/brand/lora/sol_portrait.png` |
| second portrait | `content/brand/lora/rex_portrait_b.png` |
| openings | `content/brand/opening/opening_ep{1..5}.png` |

**Handle:** `@solrexnews` · display name **Sol & Rex News**.
Deliberately not `@solandrexnews` — run together, "sol" + "andrex" reads as
a toilet-paper brand, which a hostile naming screen caught.

Cleared fallbacks: `@solsdesk`, `@solatsix`, `@deskwithsol`, `@oldmansol`,
`@solexplains`, `@thelagwatch`.

**Bio** must keep **"parody"** and normally **"not advice"**, even on
historical or political posts — the moment one episode touches markets, a
profile with no disclaimer works against you, and it costs three words.

---

## 6. Known defects in the current assets

- The bow-tie mark carries a **white sticker outline** and painterly
  shading baked in from generation. Fine on navy, wrong anywhere else. If
  it becomes the permanent mark, redraw it in code as flat vector — that
  also yields a true SVG that scales and recolours.
- The horizontal logo renders `·` as a **tofu box**; Rockwell lacks the
  glyph. Use a bullet or en-dash.
- Ep.3/4/5 opening titles **overflow** the swap plate.
