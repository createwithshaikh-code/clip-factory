# clip-factory

লম্বা স্ট্রিম বা ভিডিও থেকে ৩০ থেকে ৪৫ সেকেন্ডের ভার্টিকাল Shorts বানানোর টুল, অনেকগুলো চ্যানেলের জন্য।
এতে মুখ ট্র্যাক করে জুম, শব্দ ধরে হাইলাইট হওয়া সাবটাইটেল, হুক টেক্সট, মুড অনুযায়ী মিউজিক, সাউন্ড ইফেক্ট আর কমেন্টারি ভয়েস থাকে।
Windows-এর জন্য বানানো।

**কে কী করে:**
- **Claude Code** (আপনার Claude সাবস্ক্রিপশন): রিসার্চ, ভালো মুহূর্ত বাছাই, কমেন্টারি লেখা, ElevenLabs দিয়ে ভয়েস বানানো আর রেন্ডার চালানো। আলাদা কোনো LLM API লাগে না।
- **Python টুল** (এই repo): ডাউনলোড, ট্রান্সক্রিপ্ট (পিসিতেই, ফ্রি), এডিট আর রেন্ডার।
- **ChatGPT এজেন্ট**: ট্রেন্ড রিসার্চ, স্ট্রাটেজি, কখন পোস্ট করবেন, পারফরম্যান্স দেখা ([docs/CHATGPT_AGENT.md](docs/CHATGPT_AGENT.md))।
- **আপনারা**: আপলোড।

## ১. প্রতিটা Windows পিসিতে একবার সেটআপ

PowerShell খুলে ক্রম ধরে এগুলো চালান:

```powershell
# ১. Git ইনস্টল (Claude Code-এরও এটা লাগে)
winget install --id Git.Git -e

# ২. Claude Code ইনস্টল, তারপর একবার `claude` চালিয়ে লগইন করুন
irm https://claude.ai/install.ps1 | iex

# ৩. নতুন একটা PowerShell খুলে repo নামান আর সেটআপ চালান
git clone https://github.com/createwithshaikh-code/clip-factory.git
cd clip-factory
powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1
```

সেটআপ স্ক্রিপ্ট ffmpeg, Python 3.12, uv আর দরকারি প্যাকেজ ইনস্টল করে। ElevenLabs API key চাইলে key না থাকলে শুধু Enter চাপুন।
শেষ হলে নতুন একটা PowerShell খুলে `cd clip-factory`, তারপর `.\cf.cmd check` চালিয়ে দেখুন সব ঠিক আছে কি না।

ElevenLabs key না থাকলে Windows-এর ফ্রি বিল্ট-ইন ভয়েস ব্যবহার হবে (চ্যানেল ফাইলে `engine: system`)। key পেলে `engine: elevenlabs` করে দেবেন।

তারপর:
1. `assets/sfx/`-এ আপনার সাউন্ড ইফেক্ট রাখুন (যেমন `vine_boom.mp3`, `bruh.mp3`)। কোন নামে রাখবেন তা [assets/README.md](assets/README.md)-তে আছে।
2. `assets/music/<mood>/`-এ লাইসেন্স করা বা রয়্যালটি-ফ্রি মিউজিক রাখুন (hype, funny, sad, emotional, chill, suspense)।
3. `channels/*.yaml`-এ প্রতিটা চ্যানেলের সোর্স লিংক, ElevenLabs ভয়েস আর রঙ ঠিক করে দিন।

## ২. প্রতিদিনের কাজ

repo ফোল্ডারে `claude` চালান, তারপর লিখুন:

| কমান্ড | কী হয় |
|---|---|
| `/daily druski` | strategy পড়ে, নতুন ভিডিও খোঁজে, দিনের ২টা (আর কয়েকটা বাড়তি) ক্লিপ বানায়, ক্যালেন্ডারে লেখে |
| `/clip kai-cenat https://youtube.com/watch?v=...` | নির্দিষ্ট একটা ভিডিও থেকে ক্লিপ বানায় |
| `/research ishowspeed` | কোন মুহূর্তগুলো ক্লিপ করা উচিত তার র‍্যাঙ্ক করা লিস্ট বানায়, রেন্ডার করে না |

বানানো ভিডিও যায় `output/<চ্যানেল>/`-এ। প্রতিটা `.mp4`-এর পাশে একটা `.txt` থাকে, যেটাতে টাইটেল, ডেসক্রিপশন আর হ্যাশট্যাগ লেখা।
যেগুলো এখনো পোস্ট হয়নি তার লিস্ট থাকে `ops/queue.csv`-এ। পোস্ট করার পর `ops/posting_log.csv`-এ একটা লাইন যোগ করুন।

## নতুন চ্যানেল

```bash
.\cf.cmd new-channel nba-moments      # channels/nba-moments.yaml তৈরি হবে, খুলে এডিট করুন
```

প্রতিটা চ্যানেলের আলাদা ফন্ট, রঙ, ভয়েস, SFX আর মিউজিক ফোল্ডার দিন। তাহলে চ্যানেলগুলো একরকম দেখাবে না, আর YouTube-এর "inauthentic content" পলিসিতে আটকানোর ঝুঁকি কমবে।

## হাতে চালানোর কমান্ড

```
.\cf.cmd check                      # সব ইনস্টল আছে কি না
.\cf.cmd discover <channel>         # ক্রিয়েটরের ভিডিও আর আগে ভাইরাল হওয়া ক্লিপের লিস্ট -> research/<channel>/videos.md
.\cf.cmd prepare <url|file> --channel <channel>   # ডাউনলোড + ট্রান্সক্রিপ্ট + digest.txt
.\cf.cmd validate work/<id>/plan.json
.\cf.cmd render work/<id>/plan.json [--only c01 c02]
.\cf.cmd status                     # work/-এ কোন ভিডিও কতদূর গেছে
.\cf.cmd queue                      # ops/queue.csv আপডেট
.\cf.cmd clean <id> [--source]      # অস্থায়ী ফাইল মুছে জায়গা খালি করা
```

## কয়েকটা কথা মনে রাখবেন

- **মনিটাইজেশন:** YouTube শুধু কেটে বানানো ক্লিপে টাকা দেয় না, মিউজিক, SFX আর সাবটাইটেল থাকলেও না। প্রতিটা ক্লিপে নিজস্ব কমেন্টারি বা কনটেক্সট থাকা দরকার। `.\cf.cmd validate` কমেন্টারি না থাকলে সতর্ক করে দেয়।
- **কপিরাইট:** খেলার ম্যাচ ফুটেজ আর জনপ্রিয় গান থেকে সবচেয়ে বেশি স্ট্রাইক আর ক্লেইম আসে। স্ট্রিমারদের অফিশিয়াল ক্লিপিং প্রোগ্রাম (যেমন Whop Content Rewards) সবচেয়ে নিরাপদ।
- **স্পিড:** Nvidia GPU থাকলে ট্রান্সক্রিপ্ট অনেক দ্রুত হয়। GPU না থাকলে CPU-তে `small` মডেল ভালো চলে। মান আরও ভালো চাইলে চ্যানেল ফাইলে `transcribe.model: medium` দিন।
- **কম্পিউটারের মধ্যে শেয়ার:** কোড, চ্যানেল ফাইল, SFX আর `ops/` git দিয়ে শেয়ার হয়। মিউজিক ফোল্ডার Drive বা Dropbox দিয়ে শেয়ার করুন। `work/` আর `output/` প্রতিটা কম্পিউটারে আলাদা থাকে।

ফোল্ডার: `clipfactory/` (কোড), `channels/` (চ্যানেল প্রোফাইল), `assets/` (sfx, music, fonts), `ops/` (strategy, ক্যালেন্ডার, লগ),
`docs/` (plan ফরম্যাট, ElevenLabs, ChatGPT এজেন্ট), `.claude/commands/` (`/daily`, `/clip`, `/research`), `CLAUDE.md` (Claude-এর জন্য মূল নির্দেশনা)।
