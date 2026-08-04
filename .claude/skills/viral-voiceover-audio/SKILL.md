---
name: viral-voiceover-audio
description: >
  Choose and DIRECT the voiceover + audio for @valuewithvalues finance Reels (flat-2D deadpan
  sketch): human vs AI/TTS tradeoff, viral-vs-cringe voice choices, deadpan delivery/emotion-tag
  checklist, when captions-only beats VO, and music-bed/ducking/SFX strategy (2025-26,
  source-backed). Use AFTER the script (short-form-scripting) when producing audio via
  gen_qr_audio.py. Triggers: "voiceover", "voice", "VO", "TTS", "which voice", "music", "audio",
  "sound", "newsroom bed", "does this sound cringe".
---

# Viral Voiceover & Audio — Voice, Delivery, Music (2025-26)

Assumes our format: flat-2D deadpan finance sketch, ~15-20s, word-by-word captions, pitched-TTS
VO + newsroom bed (`gen_qr_audio.py` — Windows SAPI pitched ~1.16× + numpy news bed). The sketch
already has a deadpan animated **newsroom-anchor character** — treat its voice + bed as a
**character asset**, consistent across episodes, not a generic narrator.

## Human vs AI/TTS

| Factor | Human/cloned | Stock AI/TTS |
|---|---|---|
| Trust | ~55% | ~23% (less than half) |
| Speed | slower | fast, scriptable |
| Fatigue | low (distinctive, parasocial) | **high** if a default/top-10 preset — IDed in ~2 words |

**For us:** a **consistent, non-default recurring voice** = the character's voice. If using
ElevenLabs/Play.ht, pick from the wider library (240+ voices), never the homepage default. Our
current SAPI-pitched voice is the placeholder anchor voice — upgrade to a non-default neural
voice (edge-tts/ElevenLabs) but keep it CONSISTENT once chosen.

## Viral vs cringe voices

| Choice | Verdict |
|---|---|
| Obscure/non-top-10 voice + explicit pacing prompt ("casual energy, micro-pause before payoff") | ✅ avoids the AI-slop tell |
| Voice-cloned character voice (~60s sample) | ✅ recurring recognition |
| Emotion-tagged delivery (spike at hook, punch on payoff) | ✅ flat AI delivery is the #1 swipe-away driver |
| Hormozi-style authoritative, high-tempo, low-filler cadence | ✅ reads as expertise in finance |
| Default/top-10 ElevenLabs preset (2025 "Adam/Brian") | ❌ instant AI-slop tell |
| Old robotic TikTok TTS ("Jessie"/Google sing-song) for serious content | ❌ stale meme, kills credibility |
| Cinematic "movie-trailer" deep narrator | ❌ wrong register, overproduced |
| Flat, monotone, no emotion tagging | ❌ #1 cited AI-voice-fatigue driver |

## Delivery checklist (mark these IN the script before TTS)

1. **Emotion-tag every beat:** `[energy: high]` on the hook, `[energy: conversational]` through
   setup/turn, `[energy: flat/deadpan punch]` on the button. **Deadpan is a *directed* flatness
   (calm, matter-of-fact), NOT undirected monotone** — write `[deadpan]` explicitly.
2. Default pace **135-160 wpm** — Hormozi cadence = short punchy sentences + minimal filler, not faster speech.
3. **Audio-first:** write VO line + rhythm before locking storyboard timing, so word-slams sync with a pose change / chart zoom.
4. Word-by-word styled captions are mandatory regardless of VO quality — most viewers are sound-off.

## Captions-only (no VO) — when

- Rapid-fire numeric/chart content where visual+caption carries the full payoff.
- Fast/cheap script tests before committing render + VO-sync time.
- Not our default (the anchor voice builds recognition); reserve for occasional pure-data posts (which also save at ~3× the rate of talking-head finance on IG).

## Music / audio bed

| Practice | Guidance |
|---|---|
| **Newsroom bed (default)** | keep low, **ducked ~-15 to -20dB under VO** during speech; swell only in the 0.5-1s pause after the hook / before the button |
| **Trending sound** | a discovery lever, but a consistent bed/stinger builds show identity — use trending sound as an occasional variant, not the backbone |
| **SFX as interrupts** | sting/whoosh/text-slam on the Turn beat's number reveal = pattern interrupt + "this is the payoff" cue |
| **Overused / avoid** | the exact same 1-second "breaking news" sting on every post (vary the stinger every few videos, keep the register); meme audio on serious takes; Subway-Surfers split-attention audio under finance VO (hurts credibility + comprehension) |

## Our-stack notes

- Protect the deadpan-anchor + newsroom-bed identity — keep voice + bed consistent across episodes rather than chasing sounds.
- Reserve the 170-200 wpm hype register for a rare punch-line only — it breaks the deadpan bit.
- `gen_qr_audio.py`: raise VO quality by swapping SAPI for a non-default neural voice; keep `PITCH` + the bed's ducking consistent.

Full write-up + source URLs: [`docs/research/voiceover-audio.md`](../../../docs/research/voiceover-audio.md).
