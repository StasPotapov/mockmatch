# Alternatives

[Русский](alternatives.ru.md)

What existed in October 2026 when cdpm was started, and why cdpm was still written. The facts below come
from project pages and directory listings; none of these tools was installed and measured.

## Browser control for agents

| Tool | What it is | Why not only it |
|---|---|---|
| [agent-browser](https://agent-browser.dev/) (Vercel Labs) | CLI; `snapshot` gives an accessibility tree with `@e1` refs, ~200–400 tokens per snapshot by the authors' numbers | control only, no design check |
| [Playwright CLI](https://www.webfuse.com/blog/playwright-mcp-vs-playwright-cli) | writes snapshots and screenshots to files instead of the context; cited ~27k vs ~114k tokens per task against Playwright MCP (origin of the number unclear) | control only |
| Playwright MCP, chrome-devtools-mcp | MCP servers; snapshots go into the context inline | the token cost cdpm avoids |
| [CDPM](https://github.com/IGELHARINE/CDPM) (IGELHARINE, npm `cdpm-mcp`) | MCP server; up to 30 numbered, logged-in Chrome slots over raw CDP, shared by many Claude Code sessions and subagents, with messages between agents | a different tool with the same name, found after cdpm was named; shared browsers for many agents, no design check |

cdpm takes the same idea (text with refs, results in files) and adds a report of what changed after
each click, `--expect`, and the design check.

## Design vs implementation

| Tool | Approach | Gap for this setup |
|---|---|---|
| [figma-map](https://pkg.go.dev/github.com/kirillbaranov/figma-map) | `verify reconcile` compares computed DOM styles with Figma values, element by element, "is / should be"; `verify pixeldiff` for the worst region | the closest idea; reads designs only from Figma |
| [mcp-perfectpixel](https://glama.ai/mcp/servers/x8pnhgknrb) | deterministic screenshot of a URL vs a design PNG; regions with severity linked to DOM elements | pixels only; design must be a PNG |
| [imugi](https://lobehub.com/mcp/m00n7682-imugi) | loop: screenshot → SSIM + pixelmatch + Claude Vision → patch until 95% | sends images to a model every iteration |
| UI Diff, design-compare, Visual Page Comparison (skill directories) | full screenshots to the model | the most expensive way |

The design lives in Claude Design, and a Claude Design file is HTML. So both sides can be compared as
DOM with computed styles, with no Figma and no model in the loop. Pixels and a cheap subagent cover only
what styles cannot show. No tool found did that for Claude Design or plain HTML mockups.
