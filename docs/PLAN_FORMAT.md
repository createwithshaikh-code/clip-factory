# plan.json format

Claude writes one `plan.json` per source video in `work/<video_id>/`. `prepare` writes a
`plan.template.json` next to it to copy from. Check it with `python -m clipfactory validate <path>`.

```json
{
  "video_id": "druski-abc123",
  "channel": "druski",
  "clips": [
    {
      "id": "c01",
      "start": 1834.2,
      "end": 1866.0,
      "title": "Druski didn't expect THIS answer",
      "hook_text": "HE WAS NOT READY FOR THIS",
      "mood": "funny",
      "layout": "face",
      "commentary": "This is the audition that broke the whole studio.",
      "commentary_at": 0.0,
      "sfx": [
        {"t": 6.4, "name": "vine_boom"},
        {"t": 14.1, "name": "bruh", "volume": 0.7}
      ],
      "zooms": [
        {"t": 6.4, "scale": 1.35, "dur": 1.0}
      ],
      "description": "Druski at Coulda Been Records. #druski #comedy",
      "hashtags": ["#shorts", "#druski", "#funny"]
    }
  ]
}
```

| field | required | meaning |
|---|---|---|
| `id` | yes | unique in this plan, e.g. c01, c02 |
| `start`, `end` | yes | seconds in the source video. Length must fit the channel (default 20-45 s; hard limit 8-60 s) |
| `title` | yes | YouTube title, under 70 characters |
| `hook_text` | no | big text in a box at the top for the first `hook.seconds` (default 3 s). Short, caps |
| `mood` | no | music folder: `hype`, `funny`, `sad`, `emotional`, `chill`, `suspense` (default hype) |
| `layout` | no | `face` (follow the face) or `fit_blur` (whole frame over blurred background). Default from channel |
| `commentary` | no, but strongly advised | 1-2 spoken sentences of added context/opinion |
| `commentary_at` | no | when the voice starts, seconds from clip start (default 0). Original audio is ducked while it plays |
| `sfx` | no | `t` = seconds from clip start, `name` = file name in `assets/sfx` without extension, optional `volume` |
| `zooms` | no | `t` seconds from clip start, `scale` (1.2-1.45 looks good), `dur` seconds held |
| `description`, `hashtags` | no | written to the `.txt` next to the video for whoever uploads |

Captions come from the transcript automatically (word by word, centre of the screen).
