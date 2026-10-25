# mockmatch

[Русский](README.ru.md)

A [Claude Code](https://code.claude.com/docs/en/overview) [skill](https://code.claude.com/docs/en/skills) and the `mockmatch` CLI:
an agent builds a website, drives a headless browser with deterministic commands and checks the
result against the design — a [Claude Design](https://claude.ai/design) frame, an HTML mockup or a PNG.
The agent reads lines of text, not screenshots. A sibling of [adbm](https://github.com/StasPotapov/adbm),
which does the same for Android.

## Why

- **Deterministic.** Python scripts read the page and compare it with the design, not a model looking
  at a screenshot. `mockmatch click "Sign in" --expect "Dashboard"` finds the element by text, clicks it,
  reports which texts appeared and went away, and checks the next page. The same command on the same
  page gives the same answer.
- **The design check is numbers.** `mockmatch compare` renders the design and the site at the same width and
  pairs their elements. Then it lists what differs: `h1 "Build sites…"  font-size 48→40`,
  `missing a "Docs"`, `div box "Card"  padding 20→16  (+2 inside moved)`. The agent fixes CSS from these lines
  and runs the check again. It does not squint at two screenshots.
- **A model where a script cannot help.** Pixel regions that the element lines do not explain (icons,
  images, gradients) become small "design | site" crops. The `mockmatch-eyes` subagent on a cheap model looks
  at them and writes a verdict.
- **Fewer tokens.** A 1280×900 screenshot costs a model ~1500 tokens, a 1280×3000 page ~5000.
  `mockmatch ui` shows a simple page in ~150 tokens and a busy one in ~1500 (capped by `--max`); a `compare` report is 20–40 lines.
- **Easier for you to check.** One HTML board per run: the summary, the verdict, the element lines,
  a "design ◀ ▶ site" swipe view, the diff overlay and the crops.

## What it does

- **Browser control.** One headless Chromium per project lives in the background between calls, so a
  login, an open menu or a filled form survive. Commands: `open`, `ui` (the page as text with `@e1` refs),
  `click`, `type`, `key`, `hover`, `scroll`, `wait`, `assert`, `batch`, `goto`, `back`, `reload`,
  `view` (viewport and theme), `tabs`, `log` (console errors, failed and 4xx/5xx requests),
  `style` (computed styles), `eval`, `look` (a 640 px screenshot for the agent), `shot` (full size, for you).
- **Design sources.** `pull` saves a rendered Claude Design file locally, without its access token.
  `frames` lists the options of a Claude Design canvas with a ready `--frame` selector.
- **Design check.** `compare` pairs elements by `data-mockmatch`, exact text, then similar text and position.
  For each pair it compares font family, size, weight, line height, letter spacing, color, background,
  border, radius, shadow, padding, opacity, size, x, and the gap to the element above. Then it runs a
  pixel diff with regions and crops. It runs several widths (`--width 1440,390`) and themes
  (`--theme light,dark`), against a fresh URL or the live tab with its state.
- **Verdict and board.** `mockmatch-eyes` reads only the crops and writes MATCH / PROBLEM / REVIEW into
  `notes.md`. `board` builds the HTML page.
- **Accounting.** `status` shows calls, tokens `mockmatch` put into the context and a rough estimate of
  tokens saved.

## How a design check goes

1. **Design.** The agent gets a preview URL of the Claude Design file (`render_preview` of the
   `claude_design` MCP), saves it with `mockmatch pull` and picks the option with `mockmatch frames`.
2. **Site.** `mockmatch open http://localhost:5173` — the dev server's page, as text.
3. **Compare.** `mockmatch compare --design design/page.html --frame '[id="1b"] .dv-card'` prints the lines:

   ```
   == 960: 16/17 matched, 1 missing, 1 extra, 8 differ (8 major), match 47%, pixels 10.9%
   ! missing  a "Docs"  @888,21 32x16
   ! h1 "Build sites that match the design"  @40,123  font-size 48→40  line-height 52.8→44  height 53→44
   ! div box "Deterministic Same input, sam…"  @40,368  border-radius 10→6  padding 20→16  height 87→79  (+2 inside moved)
   ```

4. **Fix and repeat** until no `!` lines remain.
5. **Verdict.** `mockmatch-eyes` judges the remaining pixel regions; `mockmatch board` gives you the page.

## Built on

| Tool | License | What it does in mockmatch |
|---|---|---|
| [Playwright for Python](https://playwright.dev/python/) | Apache 2.0 | launches Chromium, connects over the Chrome DevTools Protocol, screenshots |
| [Chromium](https://www.chromium.org) (downloaded by Playwright) | BSD-style | renders the design and the site |
| [Pillow](https://python-pillow.github.io) | MIT-CMU | pixel diff, regions, crops, overlay |

## Install

Requires Python 3.9+. macOS is tested; Linux should work.

**As a Claude Code plugin** (recommended): skill, agent and hook in one step.

```
/plugin marketplace add StasPotapov/sp-tools
/plugin install mockmatch@sp-tools
```

The skill is then called `/mockmatch:mockmatch`. Then ask the agent to run `mockmatch doctor --install`: it creates a venv
with Playwright, Pillow and Chromium in `~/.local/share/mockmatch`, outside the plugin cache, so updates keep it.
To get a new version: `/plugin marketplace update sp-tools`, then `claude plugin update mockmatch@sp-tools`
(in the shell).

**From a clone.** Pick one way: with both, the skill and the hook load twice.
The skill and the agent are symlinks; the hook goes into `~/.claude/settings.json`.

```bash
git clone https://github.com/StasPotapov/mockmatch.git ~/dev/mockmatch
ln -s ~/dev/mockmatch/skill ~/.claude/skills/mockmatch
ln -s ~/dev/mockmatch/skill/agents/mockmatch-eyes.md ~/.claude/agents/mockmatch-eyes.md
~/dev/mockmatch/skill/bin/mockmatch doctor --install   # venv with Playwright, Pillow, Chromium in ~/.local/share/mockmatch
```

The guard hook denies the agent reading full-size screenshots. Add it to `~/.claude/settings.json`
under `hooks.PreToolUse`:

```json
{ "matcher": "Read", "hooks": [{ "type": "command",
  "command": "f=~/.claude/skills/mockmatch/hooks/mockmatch-guard.py; [ -f \"$f\" ] || exit 0; exec python3 \"$f\"" }] }
```

`build/mockmatch/` in the project holds runs, screenshots and the browser state: add `build/` to `.gitignore`.
`mockmatch doctor` warns when it is not ignored.

## Tests

```bash
~/.local/share/mockmatch/venv/bin/pip install pytest
~/.local/share/mockmatch/venv/bin/python -m pytest tests -q
```

Unit tests cover color and style parsing, matching, folding and the hook; browser tests run `compare`
on `tests/fixtures/` and drive the session.

## Files

- `skill/SKILL.md` — the skill: when and how the agent uses `mockmatch`.
- `skill/bin/mockmatch` — the CLI, one Python file.
- `skill/reference/design-check.md` — `compare` in detail; `troubleshooting.md` — symptoms and fixes.
- `skill/agents/mockmatch-eyes.md` — the verdict subagent.
- `skill/hooks/` — the guard hook and its plugin config.
- `tests/` — pytest and HTML fixtures.
- `docs/alternatives.md` — similar tools and why mockmatch exists ([Russian](docs/alternatives.ru.md)).

## License

MIT
