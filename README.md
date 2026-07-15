# Open Video Encoder v0.3.0

Video transcoding tool with two-pass encoding for target file size.

## Features

- **Two-pass encoding** — precise bitrate control for size-limited profiles (Telegram, VK)
- **CRF (quality-based) encoding** — for unlimited-size profiles (YouTube)
- **Auto-strategy queue** — selects CRF or two-pass based on profile `limits.max_size_mb`
- **5 built-in profiles** — YouTube Best, YouTube Good, Telegram Free, Telegram Premium, VK
- **Bitrate calculator** — Cora's formula: `(max_size_mb × 8192) / duration − audio_bitrate`
- **v0.3 FFmpeg parameters** — `-profile:v`, `-g`, `-bf`, color primaries/trc/space, `-ar`

## Quick Start

```bash
# Install dependencies (Python 3.10+, FFmpeg)
pip install -r requirements.txt

# Run GUI
python main.py
```

## Profiles

| Profile | Mode | Limit | Target |
|---|---|---|---|
| `youtube_best` | CRF 18 | None | YouTube 4K |
| `youtube_good` | CRF 22 | None | YouTube 1080p |
| `telegram_free` | Two-pass | 1.9 GB | Telegram Free |
| `telegram_premium` | Two-pass | 3.8 GB | Telegram Premium |
| `vk` | Two-pass | 1.9 GB | VK |

## Project Structure

```
open-video-encoder-v0.3/
├── core/           # Encoding engine, queue, bitrate calculator
├── gui/            # Tkinter GUI
├── profiles/       # JSON encoding presets
├── tests/          # Unit tests
├── main.py         # Entry point
└── project.md      # Project specification
```

## License

MIT