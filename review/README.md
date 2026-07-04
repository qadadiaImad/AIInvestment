# Post Review dashboard

Local web app to review generated social posts (reels + carousels), read each post's caption +
audio/narration script, and attach comments that regeneration will honor.

## Run
    cd review
    pip install -r requirements.txt
    python app.py            # http://localhost:5005

## What it reads / writes
- Reads (never writes): ../higgs/* and ../content/carousel_*/<TK>/
- Reads/writes: ../feedback/post_comments.json  (the comment store; git-tracked)

## Comments → regeneration
Comments are captured here, not acted on here. When you regenerate a post, the generator reads its
**open** comments and folds them into the prompt:

    cd review && python comments.py <post_id>      # e.g. 2026-06-22_NVDA_reel
    # or, in code:  from comments import read_store, load_for_post

`post_id` = `<date>_<TICKER>_<kind>` (e.g. `2026-06-22_NVDA_reel`). After regenerating, mark the
comments resolved (in the dashboard, or PATCH /api/comments/<id> {"resolved": true}).
