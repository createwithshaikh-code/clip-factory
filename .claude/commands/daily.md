---
description: Daily run for one channel (research -> clips -> calendar). Usage /daily <channel>
argument-hint: <channel>
---
Daily content run for channel: $ARGUMENTS

Follow CLAUDE.md. Steps:
1. Read `channels/$ARGUMENTS.yaml`, `ops/strategy.md` (ChatGPT's trends and posting times) and `ops/sources_used.csv`.
2. Check what is already rendered and not posted: `./cf queue`, then read `ops/queue.csv`.
   If this channel already has 3+ days of clips waiting, stop and say so instead of making more.
3. Run `./cf discover $ARGUMENTS`, then read `research/$ARGUMENTS/videos.md`.
   Use web search too: what did this creator do this week that people are talking about?
4. Choose 1-2 source videos that are recent, popular, and NOT in `ops/sources_used.csv`.
5. For each, do the /clip steps (prepare -> plan -> validate -> voice -> render). Make `posts_per_day` clips plus 1-2 spares.
6. Append to `ops/calendar/$ARGUMENTS.md` (create it if needed) a table for the coming day(s):
   | date | time (US Eastern) | file | title | hook | why it should work |
   Use posting times from `ops/strategy.md`; if there are none, use 12:00 and 19:00 US Eastern.
7. Report a short summary: clips made, files, and anything the team should check.
