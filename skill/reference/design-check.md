# Design check with `cdpm compare`

`compare` answers "does the site look like the design" with text the agent can act on. It renders the
design and the site in the same headless Chromium at the same width, with animations off, fonts loaded
and the frame snapped to whole pixels. Then it does two passes:

1. **Elements.** Both pages are walked: every element with its own text, every image or icon, every box
   with a background, border or shadow. Elements are paired by `data-cdpm` / `data-testid`, then by exact
   text, then by similar text and position. For each pair it compares font family, size, weight, style,
   line height, letter spacing, color, text transform and decoration, background, border, radius,
   shadow, padding, opacity, width, height, x, and the gap to the element above.
2. **Pixels.** Two screenshots are diffed; changed areas become regions `r1…r8` with crops
   "design | site" in `diff/`. This catches what styles cannot: images, icons, gradients, charts.

## Design sources

| Source | How |
|---|---|
| Claude Design | `render_preview` (MCP `claude_design`) → `serve_url`, then `cdpm pull "<serve_url>" --out design`. The URL holds a token and lives ~1 hour: do not write it into files, do not show it. `pull` saves the rendered page without scripts and the token; commit `design/` so the check repeats without the MCP. |
| HTML mockup in the repo | `--design path/to/mockup.html` as is |
| A live URL | `--design https://…` (for example the old version of the site) |
| PNG / JPG | `--design mock.png`: pixels only, no element lines; the viewport width is the image width |

Claude Design files are canvases: one file holds several options side by side (`1a`, `1b`, …), each a
fixed-width card. `cdpm frames design/<file>.html` lists them:

```
Claude Design canvas: 2 frames
--frame '[id="1a"] .dv-card'  1280x511  1a Landing, light. Blue call to action.
--frame '[id="1b"] .dv-card'  960x511  1b Landing, compact header.
```

Pass that selector as `--frame`. A plain page has one frame, `body`. When the design was drawn at
another scale or the person names the option, use what they say.

## The site side

- **Without `--site`** — the current tab of the running browser (`cdpm open …`), with its state: a logged-in
  page, an open menu, a filled form. Its viewport is switched to the compared width and back.
- **`--site <url>`** — a fresh page, no state.
- **`--site-frame <selector>`** — compare only part of the site (a component, a section) with the frame.
  Coordinates of both sides then start at the frame's top left corner.

## Widths and themes

- No `--width`: the frame width (a Claude Design card) or 1440.
- `--width 1440,768,390` runs one cell per width. A canvas card has a fixed width, so a mobile design is
  usually another frame: compare it separately with its own `--frame`.
- `--theme light,dark` runs each width in both themes (`prefers-color-scheme`).

Cells are named `1280`, or `1280-dark` with several themes. Each cell has `design.png`, `site.png`,
`issues.txt` and `diff/` with `overlay.png` and `r<N>.png`.

## Reading the output

```
== 960: 16/17 matched, 1 missing, 1 extra, 8 differ (8 major), match 47%, pixels 10.9% (…)
! missing  a "Docs"  @888,21 32x16
! a "Product"  @749,21  x 749→805
! h1 "Build sites that match the design"  @40,123  font-size 48→40  line-height 52.8→44  height 53→44
! div box "Deterministic Same input, sam…"  @40,368  border-radius 10→6  padding 20→16  height 87→79  (+2 inside moved)
! p "Text lines, not images."  @361,418  text "Text lines, not images."→"Text lines instead of images."  width 238→246
~ a "Start free trial"  @40,262  background #2a62d6→#1f4fb8
~ extra    button "Subscribe"  @193,264 75x21
pixel regions: r1 @744,16 176x24  r2 @40,128 752x48  r3 @40,184 472x48 …
```

- Every value is `design→site`. `@x,y` is the element's position in the design frame.
- `!` — major: a missing element, another font, size off by 2 px or more, weight, a visible color
  difference, geometry off by 8 px or more. `~` — minor.
- `missing` — in the design, not found on the site. `extra` — on the site, not in the design.
- `box` — a container matched by its whole text; it carries background, border, radius, padding.
- `(+N inside moved)` — N children only moved because this box changed. Fix the box, not them.
- `gap-above` — the distance to the element above. It does not cascade: one shift is one line.
- `text "A"→"B"` — the pairing found similar text. In Claude Design mockups text is often placeholder
  data: real data on the site is not a defect.
- Exit code 1 — there are `!` lines (pixels only: more than 0.5% differ).

Lines are capped at `--lines 40`; the full list is in `<cell>/issues.txt`, everything in `report.json`.

## Fixing loop

1. Fix `missing` and `!` lines from the top: structure first, then typography, then color and spacing.
2. Find the CSS for an element: `cdpm style "<text>"` shows its computed styles on the site.
3. Rerun the same `compare` command. Stop when no `!` lines remain and the person's checklist is met.
   Do not chase `~` lines of 1–3 px forever: say what remains.
4. If the site uses different markup and pairing fails (many `missing` plus `extra` for the same
   texts), add `data-cdpm="<name>"` to the key elements on both sides, or compare a part with
   `--site-frame`.

## Tolerances

- `--tol 1` — px tolerance for font metrics, radius and padding; geometry uses at least 2 px.
- `--color-tol 6` — the largest channel difference (0–255) still treated as the same color.
- Pixel diff: a pixel counts as changed when a channel differs by more than 32; regions are built on an
  8 px grid; the 8 largest are kept.

## Verdict

When pixel regions remain that the element lines do not explain, or the person wants a verdict, start
the `cdpm-eyes` subagent (Agent tool, `subagent_type: cdpm-eyes`) with:

- **Task** — what the page is and what was built.
- **Run** — `build/cdpm/<run>` from the last line of `compare`.
- **CDPM** — the full path to the CLI.
- **Lines** — the `compare` output.

It reads only the crops, writes `notes.md` with MATCH / PROBLEM / REVIEW per region and rebuilds the
board. Fix the PROBLEM lines; tell the person about REVIEW lines.

## Board

`cdpm board [run] [--open]` builds `board.html`: the summary, the verdict, the element lines, a swipe
view "design ◀ ▶ site", the diff overlay and the crops. Give the person the path; do not read it yourself.
