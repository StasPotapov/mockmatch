#!/usr/bin/env python3
"""PreToolUse hook for Read: keeps full-size mockmatch screenshots out of the context.

Denies a Read of `build/mockmatch/<run>/<cell>/design.png` or `site.png` (full frames, often 1280×3000+)
and of `build/mockmatch/shots/*.png` (screenshots for the person). Crops in `diff/`, the overlay,
`look/` and `thumbs/` images pass: they are downscaled.
"""
import json
import re
import sys

FULL = re.compile(r"/build/mockmatch/[^/]+/[^/]+/(design|site)\.png$")
SHOT = re.compile(r"/build/mockmatch/shots/[^/]+\.png$")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    path = str((data.get("tool_input") or {}).get("file_path") or "")
    if FULL.search(path):
        why = ("mockmatch: full-size frame (thousands of tokens). Read the crops in diff/r<N>.png, "
               "diff/overlay.png, or make a small copy: mockmatch thumb <image> --crop x0,y0,x1,y1.")
    elif SHOT.search(path):
        why = "mockmatch: a screenshot for the person. For yourself use mockmatch look (640 px) or mockmatch thumb."
    else:
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": why}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
