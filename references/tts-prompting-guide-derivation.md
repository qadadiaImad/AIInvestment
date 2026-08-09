# How `tts-prompting-guide.md` was derived

> This file is the DERIVATION RECORD, not the guide. The guide is
> [`tts-prompting-guide.md`](tts-prompting-guide.md); read that one to write
> a prompt. This one exists so the guide's rules can be traced back to the
> study that produced them and the critique that demoted half of them.

*Derived 2026-08-09 by a four-study workflow (ep.1 mechanics, topic & flow,
comedy, audio) each torn into by an adversarial critique, then synthesised.
Only rules that survived critique are here. The comedy study died on a
connection error; its ground is partly covered by the other three, so the
humour section is thinner than it should be and is the first thing to
re-run.*


## Deliverable

Wrote `C:\Users\imadq\AIInvestment\references\tts-prompting-guide.md` — the merged, checkable guide to prompting the Chatterbox VO pipeline. It supersedes the handed-in study+critique rather than just concatenating them: weak/unverified rules are demoted or given falsifiable specs, missing structural rules from the critique are added as proposed (buildable, not-yet-built) checks, and the stray-"T" hypothesis ranking is corrected using a live finding from this session.

## Load-bearing correction found this session (guide §0)

`git diff HEAD -- scripts/vector/make_all_vo_local.py` shows **uncommitted, same-day (2026-08-09 11:38) local work** that already answers the stray-T question the study left open. A per-tag controlled A/B (`scripts/vector/tag_ab.py`, fixed seed 1234, same line, tag toggled) found `[sigh]` and `[clear_throat]` render as burst-then-gap-then-speech (a vocalised fragment ahead of the words — the measured shape of the owner's complaint), while `[gasp]`/`[whisper]` render clean. This is recorded as a dated comment at `make_all_vo_local.py:169-175`, and `[sigh]`/`[clear_throat]` have already been stripped from ep.3's `PERFORM` dict (`b01_sol_machine`, `b29_sol_bottomblock`, `b31_sol_broker`, `b50_sol_fifteen`, `s4_sol_time`), with ep.1/ep.2 left untouched to preserve their approved audio.

This promotes the study's #1-ranked-as-"low"-likelihood hypothesis (tag partial-vocalisation) to **confirmed for two of the four tags, cleared for the other two**. The study's own aggregate test (`leading_burst.py`, all four tags lumped into one "tagged" bucket) missed this because it averaged a real effect together with a null one; the fix was testing per-tag instead of per-bucket. The guide flags this as uncommitted work — verify it lands in a commit before it's lost — and notes ep.3's audio hasn't yet been regenerated with the corrected `PERFORM` dict, so the falsifying rerun of `leading_burst.py` on fresh ep.3 audio is the one remaining open step, called out explicitly in §4 of the guide.

## What the critique's demotions/additions became in the guide

- The unverified "state the topic in one sentence by beat 4" rule was moved out of the checkable-rules list into a clearly-labeled structural hypothesis (§3), matching the critique's complaint that it sat in the numbered list with a hedge as strong as "treat as a hypothesis, not an established cause."
- The exclamation-mark rule was kept but its causal claim corrected: the documented fix for Rex's yelping was a DELIVERY retune, not punctuation, so the rule now states punctuation and DELIVERY *compound* rather than substitute for each other.
- The ellipsis rule was given a checkable placement/density spec instead of "use them deliberately."
- Turn-taking cap, stakes-clarity, and transition-motivation — the three structural gaps the critique named — are each written up in §3 with a concrete proposed script (`turn_taking_probe.py`, a generalized `echo_move_probe.py`) or an explicit note that no regex/script can do it (stakes-clarity needs a human/LLM classification pass, not a probe).

## Ranked T-hypotheses and automated detection

Section 4 carries all five hypotheses from the study, re-ranked, each with its exact experiment (run or unrun, stated explicitly which). Section 5 lists every existing detector script with what it catches and its exact command, a three-stage gate order (pre-recording script lint → post-recording audio probes → an explicitly-acknowledged unautomatable perceptual-listening gap), and the six not-yet-built checks the guide proposes, ordered cheapest-first to build.
