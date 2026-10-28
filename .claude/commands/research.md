---
description: Research a channel's creator and list the best moments to clip. Usage /research <channel>
argument-hint: <channel>
---
Research for channel: $ARGUMENTS. Do not render anything.

1. Read `channels/$ARGUMENTS.yaml` and `ops/strategy.md`.
2. Run `./cf discover $ARGUMENTS` and read `research/$ARGUMENTS/videos.md`.
3. Web-search the creator's recent viral moments, memes and drama (last 30 days), and which clips of them got the most views.
4. Write `research/$ARGUMENTS/ideas.md`: a ranked list of 10-20 moments to clip, each with the source video URL,
   approximate time if known, the hook, and why people will watch. Mark which ones are already in `ops/sources_used.csv`.
