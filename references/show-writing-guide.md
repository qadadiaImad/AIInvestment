# The FairMarket/Bubbles Writing Guide — merged, critique-survived rules

*Derived 2026-08-09 by a four-study workflow (ep.1 mechanics, topic & flow,
comedy, audio) each torn into by an adversarial critique, then synthesised.
Only rules that survived critique are here. The comedy study died on a
connection error; its ground is partly covered by the other three, so the
humour section is thinner than it should be and is the first thing to
re-run.*


## 0. What this guide is and how to use it

Merges three independent studies of ep.1 (approved) vs ep.3 (rejected — "boring, not smooth cnv, not funny, topic never introduced explicitly, ambiguous, bad storytelling") and their adversarial critiques. Every rule below is one that **survived critique**: either the critique found no hole in it, or the critique's proposed fix has been folded in. Rules the critiques killed (unbounded "the open," ungrounded exclamation-mark causality, single-example bookend elevated to law) are dropped or rewritten with a number attached. All quotes are cited `file:line` and were re-grepped against `remotion/src/compositions/FairMarketEp1.tsx` and `Bubbles.tsx` this session — **verified**, not carried over from the studies on trust.

**Top-to-bottom for a writer:** sections 1-6 are in the order you write them (open → structure → dialogue → jokes → close → production). **For a reviewer:** section 7 is a single pass/fail checklist scoring a finished draft against every rule below, in the same order.

The owner's complaint had three parts. Each is answered by a named cluster of rules, not scattered advice:
- *"topic never introduced explicitly"* → §1
- *"not funny"* → §4
- *"not smooth cnv / bad storytelling"* → §2, §3

## 1. Open: name the topic, don't gesture at it

**Rule 1.1 — Concrete noun in line 1.** State the subject as a nameable noun in the first line, never a metaphor standing in for it. Test: can a first-time viewer name the subject after line 1 alone?
- PASS, ep.1 (`FairMarketEp1.tsx:217`): SOL "Kid… let me tell you about the so-called 'fair' market." → *market*.
- FAIL, ep.3 (`Bubbles.tsx:222`): SOL "Kid... let me show you the machine behind every crash." → 'machine' names no subject; the viewer knows only that something crashes.

**Rule 1.2 — The topic word by beat 4, and it must itself be a topic, not a quality.** The line that pays off the cold open's tension must name a mechanism the viewer can look up — a noun (POLITICS, LEVERAGE, a BUBBLE) — never an epistemic quality (MATH, LOGIC) that only describes how calculable the explanation is.
- PASS, ep.1 (`FairMarketEp1.tsx:255`): "Sometimes… it trades on POLITICS."
- FAIL, ep.3 (`Bubbles.tsx:241`): "Sometimes... it's just MATH." 'Math' is not a subject a viewer can search for.

**Rule 1.3 — One dated, named, real anchor within the first 5 lines, and the episode's own title-word must appear inside that same 5-line window.** The anchor comes from SOL, before any framework/enumeration language starts. This folds two things the flow-critique flagged separately (an anchor-timing rule and a keyword-timing rule) into one checkable window, because the critique showed the keyword rule alone was unfalsifiable ("the open" has no boundary) — pinning it to the same 5-line window as the anchor gives it one.
- PASS, ep.1 (`FairMarketEp1.tsx:~`, quoted in the mechanics study): "July 2022. The Speaker's household sold NVIDIA - days before the chip subsidies passed. At a loss, kid." — date, name, action, all inside line 5.
- FAIL, ep.3 (`Bubbles.tsx:541`): the word "bubble" — the episode's own title concept — is not spoken until the second-to-last line, REX "So the bubble didn't cost you money?" No dated anchor lands before the four-part framework begins at line 273.

*Reviewer check:* read only lines 1-5. Circle the subject noun, the mechanism word, and the anchor (date+name+action). All three present in that window = pass. Any one missing = the topic is not "introduced explicitly."

## 2. Structure: a causal chain, never a recited framework

**Rule 2.1 — Ban verbatim-reused ordinal/part labels.** No two SOL lines in the episode may open with an ordinal structural label ("Part one," "Part two," "Step one,"...) applied to two different examples without new causal content connecting them. This is the fix the flow-critique explicitly demanded for the old, untestable "causal chain" rule: instead of asking a reviewer to judge whether "each line answers a question raised by the line before it" (unfalsifiable), grep the script for ordinal openers and treat >1 use of the same 4-part list against a second example as an automatic fail.
- FAIL, ep.3 (`Bubbles.tsx:273,311,343,368`): "Part one. Money gets cheap." / "Part two. A story shows up." / "Part three. Leverage." / "Part four. Someone has to sell." — then (`Bubbles.tsx:497`, quoted in the mechanics study) "Run it back eight years. Same four parts. Different story." reapplies the identical labeled structure to 2008, i.e. a taxonomy recited twice, not a story that builds.
- Fix direction: if a framework genuinely has ordered stages, dramatize each stage as a **consequence** of the one before ("cheap money → so a story can get funded → so leverage compounds it → so someone eventually has to sell") with no numbered headers, the way ep.1 chains trade → tracked-like-a-leaderboard → turned-into-an-index → both-sides-fund-exists → filings-are-45-days-late → performance → leveraged → so-watch-committees, never once labeling a step.

**Rule 2.2 — No character holds the floor more than 2 consecutive line/line2 beats without the other character landing a beat that passes the Rule 3.1 delete-test.** This closes the gap both critiques flagged as missing entirely: word-count caps (§6) stop a monologue from being *long*, but say nothing about it being *uninterrupted*. Ten short 6-word lines back to back is still a lecture. The four-part run above is the concrete failure case this rule targets — cross-check it against 2.1 rather than treating them as separate defects.

## 3. Conversation: make every line earn its place opposite the other one

**Rule 3.1 — The delete-test (binary, per REX line).** Delete the line. If SOL's next line reads identically in spirit, rewrite REX's line into one of three things: a question SOL's next line specifically answers, a wrong guess SOL corrects, or a pushback SOL rebuts.
- FAIL (`Bubbles.tsx:472`, quoted in the flow study, SOL's line preceding it): SOL "Eleven and a half TRILLION. Gone." / REX "Trillion? With a T?" / SOL "With a T, kid." — delete REX's line and SOL's reply is unchanged in spirit. Two monologues wearing a dialogue costume.
- PASS (`FairMarketEp1.tsx:313` + next line, quoted in the flow study): REX "One trade. One person. That's a coincidence, boss, not a strategy." / SOL "One? People track these disclosures like a leaderboard." SOL's line cannot exist without REX's specific objection.

**Rule 3.2 — Echo-word handoff, with a number attached.** Both critiques killed the earlier version of this rule for saying "use as default connective tissue" with no count. Fixed version: land the echo-word handoff (repeat the other speaker's key word as a question, then pivot) on **at least 5 exchanges per ~40-line episode** (ep.3's accepted rewrite shipped it 7 times against a rejected draft that shipped it zero times — both numbers are load-bearing, not aspirational), and require at least one instance inside the first 5 lines and at least one inside any run of 3+ consecutive stat/number lines (this is also where Rule 3.1 most often fails, per the TRILLION example above — the fix for that exact line is an echo-word pivot, not a bare confirmation).
- Working example already in ep.3 (`Bubbles.tsx:349,355`): REX "Leverage - like a crowbar? More leverage means more power, right?" / SOL "Crowbar? ...With one, YOU control the wobble. Borrowed money... the wobble controls YOU." The device works when used — the defect is coverage, not knowledge of the device.

## 4. Humor: two levers, not one gag repeated

The old guide's humor coverage was a single mandated beat — both critiques called that a floor, not a fix for "not funny." Two independent, countable levers, plus one hard ban:

**Rule 4.1 — At least 2 propose-and-deflate beats per episode.** REX proposes a plausible shortcut/scheme; SOL punctures it with a *specific* hidden cost (not a shocked reaction). This is a joke shape that can escalate each use — one target is a floor, not a ceiling.
- PASS (`FairMarketEp1.tsx:456,464`): REX "Then I'll just copy them! Buy what they buy!" / SOL "Copy them. With a filing from six weeks ago?"
- Ep.3 has zero instances — REX only ever reacts to information SOL hands him; he never proposes an action for SOL to shoot down.

**Rule 4.2 — The echo-word handoff (Rule 3.2) doubles as the second humor lever** when it lands on a subversion rather than a straight pivot (repeat the word, then undercut or reverse its meaning) — this is measured in the audio study as "nearly every laugh beat in ep.1." Rule 3.2's count (≥5) is also the humor-density floor; don't write a separate joke budget on top of it.

**Rule 4.3 — Hard ban: the same reaction shape may not fire more than twice in one episode.** A shocked gasp at a large number is a joke exactly once or twice; the third repetition reads as a tic, not a punchline.
- FAIL, ep.3: five consecutive instances of the identical shape — "A THIRD of a house, gone?" ... "Trillion? With a T?" — big-stat-then-exclaim, run without escalation or variation.

## 5. Close: answer your own opening word, then tell the viewer what to do

**Rule 5.1 — Bookend the cold-open word or frame in the closing line.** The final SOL line must directly reuse or answer the exact word/frame the episode opened on.
- PASS (`FairMarketEp1.tsx:645`): opens on "fair" (line 217) → closes "Fair? No. But now you can read it."
- FAIL (`Bubbles.tsx:222,547`): opens on "the machine behind every crash" → closes "No. It cost you TIME." 'Machine' never returns; the opening frame is dropped, not resolved.

**Rule 5.2 — End on one plain imperative before any closing hook — never a historical-fact verdict alone.** The last substantive line must tell the viewer what to *do*, not just what happened.
- PASS (`FairMarketEp1.tsx:628`): "Watch what they sit near. Committees. Hearings. Then do your own homework."
- FAIL, ep.3: last substantive line is a verdict ("It cost you TIME") with nothing for the viewer to act on.

Write these two as one beat, in this order: bookend word first, imperative second — the bookend closes the story loop, the imperative gives the payoff a use.

## 6. Production-facing line rules (what makes the script speakable, not just readable)

These come from the audio study and are kept only where the critique found no hole (the exclamation-mark rule was dropped — its own evidence showed the yelping fix was a DELIVERY-setting change, not a punctuation rewrite, so it doesn't belong here as causal law; note it below as a caveat instead).

- **Numbers/currency/percent are always spelled as words** ("two point six billion," "forty-five days"), never digits or symbols — verified zero `%`/`$` hits corpus-wide except calendar years and one day-count.
- **ALL-CAPS is a screen-only emphasis cue, not a delivery instruction** — the render pipeline title-cases it (`POLITICS` → `politics`) before the model ever sees it. Real emphasis comes from sentence shape and ellipses, not shouting caps.
- **Ellipses are the pause primitive** — place them deliberately as a beat before a punchline ("Kid… let me tell you..."), not as decoration. Concrete floor: at least one ellipsis-driven pause per act, always immediately before a joke or reveal line, never mid-exposition.
- **Contractions are the norm** ("that's," "doesn't," "it's") — formalizing dialogue into written-report English is the single measured cause the audio study names for ep.3's early draft reading as narration rather than two people talking.
- **Line-length target, measured against both owner-approved scripts:** average 10-11 words/line, longest line ≤25 words, ≥20% of beats at ≤6 words. Ep.3's rejected draft measured 11.6/34/19%; its accepted rewrite moved to 5.9/13/63%.
- **PERFORM tags** (`[sigh]`, `[clear_throat]`, `[whisper]`, `[gasp]` — the only four that render) at roughly 20-33% of lines, one per line, never on two consecutive lines from the same character.
- *Caveat, not a rule:* if a REX beat reads as "yelping," the fix that actually shipped was retuning the character's DELIVERY settings (exaggeration/cfg_weight/temperature), not rewriting `!`/`?!` punctuation — don't chase this in the script.

## 7. Reviewer checklist — score a draft top to bottom

Read only what's needed for each check; don't skim the whole script hunting for exceptions — if a rule's window doesn't contain what it asks for, it fails.

**Topic (§1)** — read lines 1-5 only
- [ ] 1.1 Line 1 names a concrete noun subject
- [ ] 1.2 By beat 4, a topic-word (not a quality-word) pays off the open
- [ ] 1.3 A dated/named real anchor lands by line 5, and the episode's title concept is spoken somewhere in that same window

**Structure (§2)** — grep the whole script
- [ ] 2.1 Zero instances of an ordinal/part label reapplied to a second example
- [ ] 2.2 No speaker holds the floor >2 consecutive beats without an interrupting beat that passes 3.1

**Conversation (§3)** — line-by-line pass over every REX line, then a count
- [ ] 3.1 Every REX line passes the delete-test
- [ ] 3.2 ≥5 echo-word handoffs, including one in the first 5 lines and one inside any 3+-line number run

**Humor (§4)** — count across the whole script
- [ ] 4.1 ≥2 propose-and-deflate beats (specific cost, not a gasp)
- [ ] 4.2 Echo-word count from 3.2 also satisfies the humor floor
- [ ] 4.3 No reaction shape (e.g. shocked-gasp-at-number) fires more than twice

**Close (§5)** — read only the last 2 lines
- [ ] 5.1 Final line bookends the cold-open word/frame
- [ ] 5.2 The beat before the sign-off is a plain imperative, not a verdict alone

**Production (§6)** — mechanical scan
- [ ] No digit/`%`/`$` outside a year or day-count
- [ ] No load-bearing meaning riding on ALL-CAPS alone
- [ ] Line-length stats within target band
- [ ] PERFORM tags in budget, none back-to-back same speaker

**Ship gate:** all of §1, §3.1, §5 must be 100% pass — these three map directly to the owner's three named complaints (explicit topic, smooth conversation, funny) and are non-negotiable. §2, §4, §6 failures should be logged and fixed but don't block a first read-aloud pass. Before recording, read the draft aloud against this list rather than asserting compliance — the studies exist because two prior scripts typechecked against looser versions of these rules and still shipped the defects they were meant to catch.
