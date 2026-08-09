"""Episode 3's beat table, v2 — rewritten for VOICE.

v1 was correct and boring. The owner's note: ep.1 works because "voices
often reflect emotions and well pronounced HA!", the characters "queued
well their sentences to express the mood", and ep.3 by comparison is "a
little bit boring and not funny" with no "pace".

Three things changed, all of them measurable against ep.1:

1. THE ECHO. Nearly every laugh in ep.1 is Sol repeating Rex's own word
   back at him and then dropping it - "HA! ...Fundamentals." / "One?" /
   "Copy them. With a filing from six weeks ago?". v1 had none of it and
   Sol simply lectured. v2 runs the move seven times: bad banks, cheap, a
   name, excuse, crowbar, forced, once.

2. UNIT LENGTH, not speed. Pace in ep.1 comes from two-syllable beats -
   "WHAT?!", "Six weeks?", "No." v1's longest line was 34 words against
   ep.1's 25, and only 19% of its beats were six words or shorter. v2 is
   52 beats with roughly 60% at six words or fewer.

3. PERFORM TAGS. v1 shipped with ZERO, against ep.1's eight. Every line
   was generated flat. Nine beats here carry a tag, and they are listed in
   PERFORM_TAGS below so make_all_vo_local.py can pick them up.

The spine and every figure are unchanged - this was a voice pass, not a
facts pass. Numbers stay ROUNDED in the dialogue and exact on the wall,
which is the house rule and also just how people talk.

  imported by build_composition.py
"""
from __future__ import annotations

# (speaker, vo, line, wall_kind, wall, pose, two_shot)
#   wall_kind: E=exhibit  G=graphic  H=hold
B = [
 ("SOL","b01_sol_machine","Kid... let me show you the machine behind every crash.","E","b_machine",0,0),
 ("REX","b02_rex_badbanks","Boss! It's all just bad banks, right?!","H","",0,1),
 ("SOL","b03_sol_ha","HA! ...Bad banks.","H","",3,0),
 ("SOL","b04_sol_math","Sometimes... it's just MATH.","H","",1,0),
 ("REX","b05_rex_what","WHAT?!","H","",3,0),
 ("SOL","b06_sol_fourparts","Four parts. No villain. Every single time.","G","machine_parts",0,0),
 ("REX","b07_rex_name","Give me a name, boss. I'll write it down.","E","b_empty_chair",0,0),
 ("SOL","b08_sol_aname","A name?","H","",3,0),
 ("SOL","b09_sol_partone","Part one. Money gets cheap.","H","",1,0),
 ("REX","b10_rex_discount","Cheap like a discount?","H","",2,0),
 ("SOL","b11_sol_cheap","Cheap. ...Like the loan you couldn't afford - suddenly you can.","G","fedfunds",0,0),
 ("SOL","b12_sol_onepercent","Fed funds fell under ONE percent.","H","",1,0),
 ("SOL","b13_sol_months","Under one and a half... for TWENTY-TWO months.","H","",0,0),
 ("REX","b14_rex_free","Twenty-two months of free money?!","H","",0,0),
 ("SOL","b15_sol_parttwo","Part two. A story shows up.","E","b_corkboard",1,0),
 ("REX","b16_rex_true","In '08 the story was - houses always go up. That's just TRUE.","H","",1,0),
 ("SOL","b17_sol_only","True. Until it's the only reason anyone gives for the price.","G","caseshiller",0,0),
 ("REX","b18_rex_excuse","So it's not a reason. It's an EXCUSE.","H","",0,0),
 ("SOL","b19_sol_learning","Excuse? ...Now you're learning, kid.","H","",3,0),
 ("SOL","b20_sol_partthree","Part three. Leverage.","E","b_block_tower",1,0),
 ("REX","b21_rex_crowbar","Leverage - like a crowbar? More leverage means more power, right?","H","",0,0),
 ("SOL","b22_sol_youcontrol","Crowbar? ...With one, YOU control the wobble.","H","",1,0),
 ("SOL","b23_sol_controlsyou","Borrowed money... the wobble controls YOU.","H","",0,0),
 ("SOL","b24_sol_partfour","Part four. Someone has to sell.","E","b_falling_card",1,0),
 ("REX","b25_rex_margin","Forced? Like a margin call?","H","",1,0),
 ("SOL","b26_sol_forced","Forced. The lender wants cash you don't have.","G","machine_loop",0,0),
 ("REX","b27_rex_banks","Okay - so the BANKS. They're the villain. They went first.","E","b_cracked_facade",0,0),
 ("SOL","b28_sol_no","No.","H","",3,0),
 ("SOL","b29_sol_bottomblock","That's the tower losing its bottom block.","H","",1,0),
 ("REX","b30_rex_whostacked","Then who stacked it?","E","b_conveyor",2,0),
 ("SOL","b31_sol_broker","The broker. The bank. The buyer who believed the story.","H","",0,0),
 ("REX","b32_rex_nobody","So nobody's responsible?","H","",1,0),
 ("SOL","b33_sol_everyone","Everyone's responsible. Nobody's the villain.","G","machine_parts",0,0),
 ("SOL","b34_sol_houses","House prices fell TWENTY-SEVEN percent.","G","caseshiller",1,0),
 ("REX","b35_rex_third","A THIRD of a house, gone?","H","",0,0),
 ("SOL","b36_sol_market","The market fell FIFTY-FIVE percent.","G","drawdown2008",0,0),
 ("REX","b37_rex_half","More than HALF?!","H","",3,0),
 ("SOL","b38_sol_jobs","Unemployment. Four point four... to TEN.","G","unrate",1,0),
 ("SOL","b39_sol_trillion","Eleven and a half TRILLION. Gone.","G","wealth",0,0),
 ("REX","b40_rex_witht","Trillion? With a T?","H","",2,0),
 ("SOL","b41_sol_witht","With a T, kid.","H","",3,0),
 ("REX","b42_rex_once","Okay but - that's the big one. That's ONCE.","E","b_two_machines",0,0),
 ("SOL","b43_sol_once","Once?","H","",3,0),
 ("SOL","b44_sol_runback","Run it back eight years.","H","",1,0),
 ("SOL","b45_sol_internet","Same four parts. Different story. This time... the internet.","H","",0,0),
 ("SOL","b46_sol_seventyseven","Dot-com fell SEVENTY-SEVEN percent.","G","dotcom",1,0),
 ("REX","b47_rex_what2","WHAT?!","H","",3,0),
 ("SOL","b48_sol_backtoeven","Took until twenty-fifteen to get back to even.","H","",0,0),
 ("REX","b49_rex_fifteen","Fifteen years?!","H","",0,0),
 ("SOL","b50_sol_fifteen","Fifteen years, kid.","H","",1,0),
 ("REX","b51_rex_notmoney","So the bubble didn't cost you money?","E","b_machine_lit",1,0),
 ("SOL","b52_sol_time","No. It cost you TIME.","H","",3,0),
]

# The four tags measured to actually change Chatterbox's delivery. [gasp]
# goes on Rex's takes, [sigh] on Sol at his weariest, [whisper] on the two
# lines that should drop to almost nothing, [clear_throat] before a
# correction.
PERFORM_TAGS = {
    "b01_sol_machine": "sigh",
    "b02_rex_badbanks": "gasp",
    "b05_rex_what": "gasp",
    "b14_rex_free": "gasp",
    "b27_rex_banks": "gasp",
    "b29_sol_bottomblock": "clear_throat",
    "b31_sol_broker": "sigh",
    "b37_rex_half": "gasp",
    "b44_sol_runback": "whisper",
    "b47_rex_what2": "gasp",
    "b50_sol_fifteen": "sigh",
    "b52_sol_time": "whisper",
}

# ---- the 22s Shorts cut, same voice ------------------------------------
# Leads on the verified fifteen-years fact, runs the echo move once
# ("Fifteen YEARS?!" -> "HA! ...Fifteen years."), and closes so the last
# frame hands back to the first.
SHORT = [
 ("SOL","s1_sol_fifteen","The last bubble took fifteen years to get back to even.","G","dotcom",0),
 ("REX","s2_rex_fifteen","Fifteen YEARS?!","H","",3),
 ("SOL","s3_sol_ha","HA! ...Fifteen years.","E","b_machine",3),
 ("SOL","s4_sol_time","It doesn't cost you money, kid. It costs you TIME.","H","",1),
 ("SOL","s5_sol_four","Four parts. No villain. Every single time.","G","machine_parts",0),
 ("REX","s6_rex_villain","So who's the villain?","H","",1),
 ("SOL","s7_sol_nobody","...Nobody. Watch the machine.","E","b_machine_lit",1),
]

SHORT_TAGS = {
    "s2_rex_fifteen": "gasp",
    "s3_sol_ha": "",
    "s4_sol_time": "sigh",
    "s7_sol_nobody": "whisper",
}
