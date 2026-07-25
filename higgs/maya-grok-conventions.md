# Maya × Grok — required conventions

**Applies to: every prompt written for Grok that features Maya.** These are not
suggestions; a prompt that omits them produces a Maya who isn't *the* Maya, and
persona continuity is the whole reason the character exists.

---

## 1. Always open with the skill invocation

Every Grok prompt featuring Maya **must** start with this line, verbatim:

```
Load the Maya car reel skill and make a new one with this script: …
```

…with the script/brief following after the colon.

This is a literal invocation string for a Grok-side skill — reproduce it exactly
as written (including "car reel"). Don't paraphrase it, don't "fix" it, don't
fold it into a longer sentence. It goes first, before any other instruction.

## 2. Always pin the voice

Any prompt that involves Maya **speaking** must reference her voice fingerprint:

```
For audio, adapt to this voice: /home/workdir/artifacts/maya_voice_fingerprint.wav
```

That path is in **Grok's workspace, not this repo** — it is not checked in here
and won't resolve from a sandbox session. Treat it as an external reference the
Grok side already has.

**This supersedes the old "Maya has no cloned voice" caveat** that appears in
earlier briefs (`CHOKEPOINT_TSMC`, `CONGRESS_UNDERVALUED`). Those were written
before the fingerprint existed. Where a script says voice generation is blocked,
that blocker applies to *this sandbox's* local TTS path only — via Grok, with the
fingerprint above, Maya can speak.

## 3. Keep the identity lock

Physical description stays verbatim from
[`maya-facial-prompt.md`](maya-facial-prompt.md) in every generation. Only the
*setting* varies (home-office / podcast studio / car / etc.). Never re-describe
her from memory — drift is how a recurring character stops being recognizable.

---

## Prompt skeleton

```
Load the Maya car reel skill and make a new one with this script:

<the script or beat-by-beat brief>

For audio, adapt to this voice: /home/workdir/artifacts/maya_voice_fingerprint.wav

Setting: <podcast studio / car / home-office — the only thing that varies>

<identity-lock block, verbatim from maya-facial-prompt.md>

<any layout, duration, or compliance constraints>
```

## Compliance still applies

The skill invocation doesn't override the house rails. Anything Maya says still
needs: educational framing (not advice), certainty labels on claims
(filed/reported), congress trades framed as public record rather than
accusation, and a visible "not financial advice · DYOR" on the deliverable.
