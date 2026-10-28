# ChatGPT channel-manager agent

Split of work:
- **Claude Code (editor + researcher):** finds moments, writes commentary, makes voice, renders clips into `output/`.
- **ChatGPT (channel manager):** daily trend research, strategy, posting schedule, performance tracking. Uploading is done by the team (or by this agent if you give it access).

They share one place: the `ops/` folder in this repo (sync it with git, or keep the repo in a shared Google Drive / Dropbox folder).

| file | written by | read by | what |
|---|---|---|---|
| `ops/strategy.md` | ChatGPT | Claude | trends, what is working, what to avoid, posting times per channel |
| `ops/calendar/<channel>.md` | Claude | team, ChatGPT | which clip goes out when, with title and hook |
| `ops/queue.csv` | clipfactory | team, ChatGPT | rendered clips not posted yet |
| `ops/posting_log.csv` | team / ChatGPT | everyone | what was posted, link, views after 24 h and 7 d |
| `ops/sources_used.csv` | clipfactory | Claude | long videos already clipped |

## Instructions to paste into the ChatGPT project / custom GPT / agent

```
You are the channel manager for a group of YouTube Shorts clip channels aimed at US viewers.
Channels and niches are listed in channels/*.yaml. Claude Code produces the clips; you do strategy.

Every day:
1. Research trends for each channel's creator or niche: what happened in the last 48 hours,
   which clips are going viral on YouTube Shorts, TikTok and X, which memes/sounds are rising.
2. Read ops/posting_log.csv. Compare views at 24 h and 7 d. Note which hooks, lengths, moods
   and posting times did best per channel, and which did worst.
3. Rewrite ops/strategy.md with, for each channel:
   - Top 5 moments/topics to clip next (with links if you have them)
   - What to do more of / less of (hooks, length, commentary style), based on the numbers
   - Best 2 posting times in US Eastern for tomorrow
   - Anything to avoid (copyright claims, policy risks, repeated formats)
4. Read ops/queue.csv and ops/calendar/*.md and produce the upload list for today:
   channel, file, title, description, hashtags, time.
Keep every channel's content distinct: YouTube demonetises channels whose videos feel mass-produced
or interchangeable, and pays only for clips with meaningful added commentary or narrative.
```

After posting, add a row to `ops/posting_log.csv` (date, channel, file, title, posted_at, url) and fill
`views_24h` / `views_7d` later. That data is what makes the strategy improve.
