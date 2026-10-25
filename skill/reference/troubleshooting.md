# Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Playwright or Pillow is missing` | `mockmatch doctor --install`: a venv in `~/.local/share/mockmatch/venv` with Playwright, Pillow and Chromium. The CLI switches to it by itself. |
| `the browser did not start` | Read `build/mockmatch/daemon.log`. A stale `build/mockmatch/session.json` after a crash: `mockmatch close`, then `open` again. |
| `no browser` | The browser stops after 3 idle hours (`MOCKMATCH_IDLE_HOURS`). `mockmatch open <url>` again. |
| `@e5 is gone` | Refs change after every `ui`. Run `ui` and take the new ref, or click by text. |
| click hits the wrong element | Text matches several elements: the CLI prefers an exact match on a clickable element in the viewport. Use `@ref` from `ui` or `css=<selector>`. |
| `--expect` fails, but the page is right | The text is not in `innerText` (an image, a canvas, a hidden element). Expect another text, or `wait` longer with `--timeout`. |
| `compare`: everything is `missing` + `extra` | Wrong `--frame`: `mockmatch frames` lists them. Or the site renders other texts: compare a section with `--site-frame`, add `data-mockmatch` to key elements. |
| `font-family` differs everywhere | The site does not load the design's web font, or the name differs (`Inter` vs `Inter Variable`). Load the same font; the line names both families. |
| pixel diff marks the whole bottom half | Something above shifted vertically. Fix the element lines first; regions shrink with them. |
| `pull` saved no images | Only files from the design's own folder are saved. External images stay as URLs. |
| `serve_url` expired | `render_preview` again: it gives a new one. Pull once, then compare the local copy. |
| local `http://localhost` does not open | The dev server is not running. Start it in the background first, then `mockmatch open`. |
