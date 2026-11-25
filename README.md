# The World in One Day — 25 November 2026

[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/AT79x/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/AT79x/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

A program that writes one 1024x1024 PNG summing up the world news of
Wednesday 25 November 2026, for the make.fun
[news-image-20261125 bounty](https://make.fun/bounty/news-image-20261125).

Front page with a dark world map: one HERO story (Saudi-led strikes hit
Hodeidah port, Yemen) plus 6 numbered cards — Shenzhou-24 lifts off with
Pakistan's first astronaut, a cyberattack hits the CIA and the US
intelligence office, Indonesia's vice-president resigns, Real Madrid
rout PSV 5-1, the UN reports five women killed every hour, and a blast
in Hanoi kills six. Every story is pinned to the map by a numbered
marker in its own colour. See NEWS.md for the sources each story was
verified against.

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Pure Python 3 standard library, no network, no files read at run time:
every pixel is drawn in code, deterministically, so two runs write
byte-identical PNGs. Output: `out/entry.png` (1024x1024, under 1 MiB).

## Layout

- `main.py` — the entry program: draws the front page and writes the PNG
- `NEWS.md` — the seven stories and the sources they were verified against

## License

MIT — see `LICENSE`.

---
Built with [make.fun](https://make.fun) — referral code `t4a9a15t`.
