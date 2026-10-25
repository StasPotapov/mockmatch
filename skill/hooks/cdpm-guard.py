#!/usr/bin/env python3
"""PreToolUse hook for Read: keeps full-size cdpm screenshots out of the context.

Denies a Read of `build/cdpm/<run>/<cell>/design.png` or `site.png` (full frames, often 1280×3000+)
and of `build/cdpm/shots/*.png` (screenshots for the person). Crops in `diff/`, the overlay,
`look/` and `thumbs/` images pass: they are downscaled.
"""
import json
import re
import sys

FULL = re.compile(r"/build/cdpm/[^/]+/[^/]+/(design|site)\.png$")
SHOT = re.compile(r"/build/cdpm/shots/[^/]+\.png$")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    path = str((data.get("tool_input") or {}).get("file_path") or "")
    if FULL.search(path):
        why = ("cdpm: full-size frame (thousands of tokens). Read the crops in diff/r<N>.png, "
               "diff/overlay.png, or make a small copy: cdpm thumb <image> --crop x0,y0,x1,y1.")
    elif SHOT.search(path):
        why = "cdpm: a screenshot for the person. For yourself use cdpm look (640 px) or cdpm thumb."
    else:
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": why}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
