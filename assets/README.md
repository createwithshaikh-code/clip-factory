# Assets

## Sound effects: `assets/sfx/`

Put files here as `<name>.mp3` or `.wav`. The file name (without extension) is the name used in `plan.json`,
so keep names short and clear. Suggested starter set:

`vine_boom`, `bruh`, `oh_my_god`, `record_scratch`, `airhorn`, `sad_violin`, `wow`, `fart`, `emotional_damage`,
`suspense_hit`, `whoosh`, `ding`, `crowd_laugh`, `crickets`, `rizz`, `taco_bell_bong`

Free sources: pixabay.com/sound-effects, freesound.org (check each license), or generate your own with the
ElevenLabs MCP (`text_to_sound_effects`). SFX files are small, so they are committed to git and every
computer gets the same set.

## Music: `assets/music/<mood>/`

Folders: `hype`, `funny`, `sad`, `emotional`, `chill`, `suspense`. A random track from the clip's mood folder
plays quietly under the clip.

Use only music you are allowed to use (YouTube Audio Library, Pixabay Music, or a paid royalty-free library).
Popular songs trigger Content ID: the money from that Short goes to the label, or the video gets blocked.

Music files are big and are **not** committed (see `.gitignore`). Share the music folder between computers with
Google Drive/Dropbox and point the channel to it with `music.folder: "/path/to/shared/music"` (or copy it in).

## Fonts: `assets/fonts/`

Optional. Drop a bold `.ttf` (for example Montserrat Black or Bebas Neue from Google Fonts) and set
`captions.font: "Montserrat-Black.ttf"` in a channel file. Without one, the system's bold font is used.
