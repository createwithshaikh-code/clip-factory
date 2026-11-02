# SEO for clip titles (US audience)

Claude writes `title`, `description`, `hashtags` and `tags` for every clip in plan.json.
`./cf validate` checks them against the channel's `seo:` block, and `./cf render` writes them
(plus the channel's evergreen tags) into the `.txt` next to each video.

## What SEO can and cannot do for Shorts

Most Shorts views come from the Shorts feed, and the feed decides mainly on how viewers react:
how many watch instead of swiping, how much of the clip they watch, rewatches, likes, shares.
A title cannot rescue a weak clip there. The hook in the first second matters more than any keyword.

Metadata still matters in three places, and that is where these rules pay off:
1. **YouTube search.** People type "kai cenat", "speed ronaldo", "druski coulda been records".
   Clips with the name and the event in the title rank for those searches for weeks.
2. **Suggested / related.** Clear names and topics help YouTube put the clip next to the creator's
   own videos and other clips of the same moment.
3. **Classifying the first viewers.** Clean metadata helps YouTube show the clip to fans of that
   creator first, and those viewers are the ones who watch to the end.

So: good SEO helps the right people find the clip. It does not guarantee reach.

## Titles

Formula: **[Creator name] + [what happens / who is involved] + [a curiosity or emotion hook]**

- Creator name in the **first ~40 characters** (the Shorts feed cuts the title around there).
  `validate` warns if it is missing or too late.
- Name the **guest, place or event** when people would search it: "Kai Cenat and Druski",
  "IShowSpeed meets Ronaldo", "Speed in Brazil", "Mafiathon", "Coulda Been Records".
- 40-70 characters. Plain US English. One CAPS word for emphasis at most ("Speed LOST it").
- Say what happens, but not the payoff: "Kai Cenat's chat found out who was at the door" not
  "Kai Cenat funny moment #47".
- Never claim something that does not happen in the clip. Misleading titles break YouTube's
  spam policy and kill retention anyway (viewers swipe when the promise is not kept).
- Never put another famous name in the title unless that person is in the clip.
- Every title in a batch must be different. No templates repeated word for word.

Patterns that fit US stream-clip audiences:

| pattern | example |
|---|---|
| Name + reaction | `IShowSpeed couldn't believe what he saw in Tokyo` |
| Name + guest | `Druski tried to sign this rapper on the spot` |
| Name + "when" situation | `Kai Cenat when chat finds the one thing he hid` |
| Name + stakes / number | `Speed bet $10,000 on this kick` |
| Question | `Did Kai Cenat really just do this live?` |
| Quote (short, the actual line) | `Druski: "You're not even in the building"` |

## Description

1. First line: who, what, where in plain words (this is what search reads most):
   `IShowSpeed tries a street football challenge in London during his IRL stream.`
2. Second line: your one-line take or context (the same voice as the commentary, not the same words).
3. The credit line is added automatically ("Original: <uploader> <url>").
4. 3-5 hashtags: creator, topic, `#shorts`. More than that looks spammy, and YouTube ignores
   every hashtag on a video that has more than 60.

## Tags

YouTube says tags play a small role, mostly helping with misspellings. They are cheap, so:
- The channel's `seo.tags` holds evergreen tags and common misspellings ("kai senat", "drewski",
  "i show speed"). They are added to every clip automatically.
- Per clip, add 2-5 `tags` for the specific moment: guest name, place, event, the meme phrase.

## US targeting

There is no "show this Short to the US" switch for organic videos. What does work:
- **YouTube Studio > Settings > Channel > Basic info > Country of residence: United States**, and
  set each video's language to English. (Team task, one time per channel.)
- US English, US slang and US references in titles and commentary.
- Post at US times (`ops/strategy.md`, default 12:00 and 19:00 US Eastern).
- Pick moments US viewers care about: US guests, NBA/NFL, US cities, US memes.

## Keeping keywords fresh

`./cf discover <channel>` lists the creator's newest videos and the clips of them that already went
viral. Before writing titles, read `research/<channel>/videos.md` and reuse the **names, events and
phrases** that appear in the high-view titles (not their exact wording). Ongoing events
(a tour, a subathon, a collab) are the strongest search terms while they are happening.
The ChatGPT channel manager should add the current trending terms per channel to `ops/strategy.md`;
compare `views_7d` in `ops/posting_log.csv` to see which title patterns worked.

## Adding a channel

Add a `seo:` block to `channels/<channel>.yaml` (the template has one): `keyword` is the exact
name people search, `aliases` are other names the title may use ("Speed"), `hashtags` are the
defaults, `tags` are evergreen tags plus misspellings.
