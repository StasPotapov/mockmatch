---
name: mockmatch
description: "Drives a headless browser for the agent while it builds a website, and checks the site against the design, with deterministic commands instead of guessing from screenshots: reads the page as compact text, clicks by text and reports what changed, types, presses keys, scrolls, waits and asserts, runs several steps in one call, reads console errors and failed requests, shows computed styles, changes viewport size and theme. Its main job is the design check: `mockmatch compare` takes a Claude Design canvas frame (or an HTML mockup, or a PNG) and the site, matches elements and lists what differs — missing and extra elements, font, size, weight, color, padding, radius, size and spacing — then a pixel diff with regions and crops, an HTML board for the person and a subagent verdict. - Any browser task while building or checking a site: \"open the site\", \"what is on the page\", \"click Sign in\", \"fill in the form\", \"any console errors\", \"why is the button grey\", \"how does it look at 390 px\", \"dark theme\". Design checks: \"does it match the design\", \"compare with the mockup / Claude Design\", \"make it like in the design\", \"pixel perfect\", \"what differs from the layout\"."
argument-hint: "<what to do or check> [--width 1440,390]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
---

# mockmatch

mockmatch is how you work with a browser while building a website. Use it instead of a browser MCP or raw
Playwright. Its commands are deterministic: `click` finds the element by text and reports what appeared
and what went away, `--expect`, `wait` and `assert` confirm a page with one line and an exit code,
`compare` computes design differences in Python. Trust their output; do not look at a screenshot to decide
where to click or whether it worked. A model looks at pictures only for what a script cannot judge.

It has two layers:

- **Browser control.** One headless Chromium per project lives in the background between calls,
  so the page state (logins, open menus, filled forms) survives. One command per action.
- **Design check.** `compare` matches the site against a design frame element by element, then pixel
  by pixel, writes a run folder with an HTML board, and the `mockmatch-eyes` subagent judges the crops.

The CLI is `bin/mockmatch` of this skill: `mockmatch="${CLAUDE_SKILL_DIR}/bin/mockmatch"`. If the variable is not
substituted, take the folder from the "Base directory for this skill" line. Run commands from the
project root: files go to `<project>/build/mockmatch/`. The project is the git root of the current folder;
`MOCKMATCH_PROJECT=<path>` overrides it. Help: `"$mockmatch" <command> -h`. Commands below omit the prefix; set the
variable in every Bash call (it does not persist). First use on a machine: `doctor`, and if it reports
something missing, `doctor --install` (a private venv with Playwright, Chromium and Pillow).

## Browser control

| The person asks | Run |
|---|---|
| open the site, a local page | `open http://localhost:5173` (`--size 390x844`, `--theme dark`); prints the page as text |
| what is on the page | `ui` (viewport), `ui --all`, `ui --find <text>`, `ui --href` |
| click, open a section | `click "<text>" --expect "<text on the next page>"`; also `@e5` from `ui` or `css=<selector>` |
| type into a field | `type "<text>" --into "<field label>"` (`--enter` submits) |
| a key, hover, scroll | `key Escape`, `hover "<text>"`, `scroll down` / `top` / `bottom` / `"<text>"` |
| wait for a page, is a text there | `wait "<text>"`, `assert "<text>"`: exit code 0 or 1 |
| several actions: a form, a known path | `batch 'type a@b.c --into Email' 'click "Sign in" --expect Dashboard' --ui`: stops at the first failure |
| another URL, back, reload | `goto <url>`, `back`, `reload` |
| console errors, failed requests | `log --errors` (`--grep <re>`, `--since 5` minutes, `--clear`) |
| why does it look like that | `style "<text>"` or `style css=.btn --props color,padding` |
| anything else from the page | `eval "<js expression>"` |
| other width or theme | `view 390x844 --theme dark` (the page keeps its state) |
| a screenshot for you | `look` (640 px, ~350 tokens), `look "<text>"` for one element, `--crop x0,y0,x1,y1` |
| a screenshot for the person | `shot <name>`: give the path, do not read it |
| tabs, stop the browser | `tabs`, `tabs --switch 1`, `close` |

Refs `@eN` change after every `ui`: take them from the latest output. After `click` and `key`, read the
`+`/`-` lines: they are the visible texts that appeared and went away. `no visible change` means the click
did nothing visible.

## Design check

Read `reference/design-check.md` before the first `compare` in a session. The short path:

1. **Get the design.** Claude Design: `mcp__claude_design__render_preview` gives a `serve_url` that
   lives an hour. Save it locally once: `pull "<serve_url>" --out design` (the token is not kept). Never
   write the `serve_url` into files or show it to the person. An HTML mockup or a PNG in the repository
   works as is.
2. **Pick the frame.** `frames design/<file>.html` lists the canvas options with sizes and a `--frame`
   selector. Ask the person which option is the one to build if it is not clear.
3. **Compare.** With the site open in the browser (`open …`):
   `compare --design design/<file>.html --frame '<selector>'`. Without `--site` it compares the current tab,
   with its state. The viewport width is the frame width unless `--width 1440,390` is given.
4. **Fix and repeat.** Each line is `design → site`. Fix the `!` lines first: missing elements, fonts,
   sizes, colors, padding. `(+N inside moved)` means children only shifted because of this box: fix the
   box. Run `compare` again until no `!` lines remain. Exit code 1 means major differences remain.
5. **Eyes.** When only `~` lines and pixel regions remain, or the person wants a verdict, start the
   `mockmatch-eyes` subagent (see `reference/design-check.md`, "Verdict"). Then `board` and give the person
   the board path.

## Rules

- Do not take a screenshot to navigate or to check that a click worked: `ui`, `--expect`, `assert`.
- Do not read `design.png`, `site.png` or `shots/*.png`: they are full size (a hook denies it).
  Use `look`, `thumb`, or the crops in `diff/`.
- A pixel diff after a vertical shift marks everything below it. Trust the element lines of `compare`
  first; pixel regions are for what elements cannot show (images, icons, gradients, shadows).
- Text in Claude Design mockups is often placeholder data. A `text "A"→"B"` line is not a defect when the
  site shows real data; say so instead of copying the placeholder.
- `close` the browser when the work is done; it also stops by itself after 3 idle hours.

## Files

- `reference/design-check.md` — compare in detail: design sources, frames, widths and themes, reading the
  output, tolerances, the eyes subagent, the board.
- `reference/troubleshooting.md` — the browser does not start, fonts differ, nothing matches.
- `agents/mockmatch-eyes.md` — the verdict subagent.
