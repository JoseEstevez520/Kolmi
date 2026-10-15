"""Does the web model write interactive pieces that run, show something and read well?

Each case in pieces.json is a brief the way the web agent writes one for an Artifact. The model
writes the piece with the same prompt and the same checks as the daily pass (`web._draw`), then
a headless Chromium draws it on the library's own sandbox runtime and measures:

- valid:    it passed the structural checks, with their one retry;
- runs:     it mounted with no script error and nothing says it could not run;
- shows:    something is on screen before it is touched (text and height; a first control whose
            click more than doubles the text is taken to hide its content);
- touch:    a control exists and touching one changes the page;
- fits:     no horizontal scroll at 340 px;
- light/dark: the text has enough contrast, 3:1 at least, in each theme (a part with a gradient
            behind it is skipped).

Use it to compare a prompt or a model before a change goes live. It touches no database, writes
nothing but what --keep asks for, and needs the dev extras (`pip install -r requirements-dev.txt`,
then a Chromium: `playwright install chromium`, or --chromium with the path of one you have).
Run from backend/ with the model's settings in the environment or backend/.env (LLM_API_KEY,
LLM_BASE_URL, LLM_MODEL), or another model's with --model / --base-url / --api-key-env:

    .venv/bin/python -m evals.run_piece_evals
    .venv/bin/python -m evals.run_piece_evals --only brand-sheet --keep /tmp/pieces
    .venv/bin/python -m evals.run_piece_evals --model some-model --repeat 2
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# The settings need these to load; nothing here reaches Supabase.
for name, value in (("SUPABASE_URL", "http://localhost"), ("SUPABASE_SERVICE_KEY", "eval"), ("CLASS_CODE", "eval")):
    os.environ.setdefault(name, value)

from app.agents import web  # noqa: E402
from app.agents.client import OpenAILLM  # noqa: E402
from app.config import get_settings  # noqa: E402

CASES = Path(__file__).with_name("pieces.json")
RUNTIME = Path(__file__).resolve().parents[2] / "frontend" / "node_modules" / "elastic-ui" / "dist" / "sandbox-runtime.js"
COLUMNS = ["valid", "runs", "shows", "touch", "fits", "light", "dark"]

PAGE = """<!doctype html><html data-theme="{theme}"><head><meta charset="utf-8">
<style>html,body{{margin:0;background:var(--color-bg);color:var(--color-fg);font-family:var(--font-sans);font-size:14px;line-height:1.5}}</style>
</head><body><div id="app"></div></body></html>"""

# Contrast of every visible text, against the nearest backgrounds behind it. Parts with a gradient
# or an image behind them are skipped: their colour can't be read from here.
CONTRAST_JS = """() => {
  const parse = (c) => {
    let m = c.match(/rgba?\\(([^)]+)\\)/);
    if (m) { const p = m[1].split(/[ ,\\/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; }
    m = c.match(/color\\(srgb ([^)]+)\\)/);
    if (m) { const p = m[1].split(/[ \\/]+/).filter(Boolean).map(Number); return [p[0] * 255, p[1] * 255, p[2] * 255, p.length > 3 ? p[3] : 1]; }
    return null;
  };
  const lum = ([r, g, b]) => [r, g, b].map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }).reduce((a, v, i) => a + v * [0.2126, 0.7152, 0.0722][i], 0);
  const over = (top, under) => { const a = top[3]; return [0, 1, 2].map((i) => top[i] * a + under[i] * (1 - a)).concat(1); };
  const page = parse(getComputedStyle(document.body).backgroundColor) || [255, 255, 255, 1];
  const bad = [];
  let worst = 21;
  const walker = document.createTreeWalker(document.getElementById('app'), NodeFilter.SHOW_TEXT);
  const seen = new Set();
  while (walker.nextNode()) {
    const node = walker.currentNode;
    const el = node.parentElement;
    if (!el || seen.has(el) || !node.textContent.trim()) continue;
    seen.add(el);
    const box = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    if (box.width < 2 || box.height < 2 || style.visibility === 'hidden' || style.display === 'none' || Number(style.opacity) < 0.3) continue;
    let bg = null, skip = false, layers = [];
    for (let p = el; p && p !== document.documentElement; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (s.backgroundImage !== 'none') { skip = true; break; }
      const c = parse(s.backgroundColor);
      if (c && c[3] > 0) { layers.push(c); if (c[3] >= 0.99) break; }
    }
    if (skip) continue;
    bg = page;
    for (const layer of layers.reverse()) bg = over(layer, bg);
    const fg = parse(style.color);
    if (!fg) continue;
    const text = over(fg, bg);
    const l1 = lum(text), l2 = lum(bg);
    const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    worst = Math.min(worst, ratio);
    if (ratio < 3) bad.push(node.textContent.trim().slice(0, 28) + ' ' + ratio.toFixed(1));
  }
  return { bad, worst: Number(worst.toFixed(2)) };
}"""

TOUCH_JS = """async () => {
  const app = document.getElementById('app');
  const snap = () => app.innerHTML;
  const length = () => app.innerText.length;
  const controls = [...app.querySelectorAll('button, [role=tab], [role=button], [role=switch], [role=radio], [role=checkbox], [role=slider], summary, input, select, textarea')].filter((el) => {
    const b = el.getBoundingClientRect();
    return b.width > 2 && b.height > 2 && !el.disabled;
  }).slice(0, 14);
  if (!controls.length) return { controls: 0, changed: false, hollow: false };
  const before = length();
  let changed = false, hollow = false, first = true;
  for (const el of controls) {
    const was = snap(), wasLen = length();
    if (el.tagName === 'INPUT' && el.type === 'range') {
      const max = Number(el.max || 100), min = Number(el.min || 0);
      el.value = String(Number(el.value) > (min + max) / 2 ? min + (max - min) * 0.2 : min + (max - min) * 0.8);
      el.dispatchEvent(new Event('input', { bubbles: true }));
    } else if (el.tagName === 'INPUT' && el.type === 'color') {
      el.value = '#cc3300';
      el.dispatchEvent(new Event('input', { bubbles: true }));
    } else if (el.tagName === 'INPUT' && (el.type === 'number' || el.type === 'text')) {
      el.value = String((Number(el.value) || 1) * 2);
      el.dispatchEvent(new Event('input', { bubbles: true }));
    } else if (el.getAttribute('role') === 'slider') {
      el.focus();
      for (const key of ['End', 'Home', 'ArrowRight']) {
        el.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true }));
        await new Promise((r) => setTimeout(r, 60));
        if (snap() !== was) break;
      }
    } else if (el.tagName === 'SELECT') {
      el.selectedIndex = (el.selectedIndex + 1) % el.options.length;
      el.dispatchEvent(new Event('change', { bubbles: true }));
    } else {
      el.click();
    }
    await new Promise((r) => setTimeout(r, 120));
    if (snap() !== was) {
      changed = true;
      if (first && length() > Math.max(before * 1.6, before + 60)) hollow = true;
      break;
    }
    first = false;
  }
  return { controls: controls.length, changed, hollow };
}"""


def draw(llm: Any, case: dict[str, Any], language: str) -> tuple[str, str]:
    return web._draw(llm, "piece", case["brief"], case["label"], case.get("notes", ""), language)


def measure(browser: Any, piece: str) -> dict[str, Any]:
    """Draw the piece at 340 px in each theme and measure it."""
    result: dict[str, Any] = {}
    for theme in ("light", "dark"):
        context = browser.new_context(viewport={"width": 340, "height": 800}, color_scheme=theme)
        page = context.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.set_content(PAGE.format(theme=theme))
        page.add_script_tag(path=str(RUNTIME))
        page.evaluate("(piece) => ElasticUiSandbox.mount(piece, { labels: {} })", piece)
        page.wait_for_timeout(500)
        text = page.evaluate("() => document.getElementById('app').innerText")
        height = page.evaluate("() => document.getElementById('app').getBoundingClientRect().height")
        failed = "could not run" in text.lower() or "could not be loaded" in text.lower()
        contrast = page.evaluate(CONTRAST_JS)
        if theme == "light":
            result["errors"] = errors
            result["failed"] = failed
            result["text"] = len(text.strip())
            result["height"] = height
            result["overflow"] = page.evaluate("() => document.documentElement.scrollWidth - innerWidth")
            result["touch"] = page.evaluate(TOUCH_JS)
            result["screenshot"] = page.screenshot(full_page=True)
        result[theme] = contrast
        context.close()
    return result


def judge(m: dict[str, Any]) -> dict[str, tuple[bool, str]]:
    touch = m["touch"]
    return {
        "runs": (not m["failed"] and not m["errors"], "; ".join(m["errors"])[:80] or ("it says it could not run" if m["failed"] else "")),
        "shows": (m["text"] >= 80 and m["height"] >= 80 and not touch["hollow"], "hollow until touched" if touch["hollow"] else f'{m["text"]} chars, {int(m["height"])} px'),
        "touch": (touch["controls"] > 0 and touch["changed"], "nothing to touch" if not touch["controls"] else "touching changes nothing"),
        "fits": (m["overflow"] <= 1, f'{m["overflow"]} px too wide'),
        "light": (not m["light"]["bad"], ", ".join(m["light"]["bad"][:3])),
        "dark": (not m["dark"]["bad"], ", ".join(m["dark"]["bad"][:3])),
    }


def main() -> int:
    from playwright.sync_api import sync_playwright

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", help="the model; LLM_MODEL by default")
    parser.add_argument("--base-url", help="an OpenAI-compatible endpoint; LLM_BASE_URL by default")
    parser.add_argument("--api-key-env", default="LLM_API_KEY", help="the variable holding the key")
    parser.add_argument("--only", help="only the case with this id")
    parser.add_argument("--repeat", type=int, default=1, help="write each case this many times")
    parser.add_argument("--keep", type=Path, help="a folder to save each piece and its screenshot in")
    parser.add_argument("--chromium", help="the path of a Chromium to use instead of Playwright's own")
    parser.add_argument("--verbose", action="store_true", help="say what is wrong in each failed check")
    options = parser.parse_args()

    settings = get_settings()
    key = os.environ.get(options.api_key_env) or settings.llm_api_key
    if not key:
        print(f"No key: set {options.api_key_env} (or LLM_API_KEY in backend/.env).", file=sys.stderr)
        return 2
    if not RUNTIME.exists():
        print(f"No runtime at {RUNTIME}: run npm install in frontend/.", file=sys.stderr)
        return 2
    model = options.model or settings.llm_model
    llm = OpenAILLM(api_key=key, base_url=options.base_url or settings.llm_base_url, model=model)

    data = json.loads(CASES.read_text(encoding="utf-8"))
    cases = [c for c in data["cases"] if not options.only or c["id"] == options.only]
    if options.keep:
        options.keep.mkdir(parents=True, exist_ok=True)

    totals = {c: 0 for c in COLUMNS}
    runs = 0
    print(f"{'case':14}" + "".join(f"{c:>7}" for c in COLUMNS))
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=options.chromium) if options.chromium else pw.chromium.launch()
        for case in cases:
            for n in range(options.repeat):
                runs += 1
                piece, problem = draw(llm, case, data["language"])
                marks: dict[str, tuple[bool, str]] = {"valid": (bool(piece), problem)}
                if piece:
                    measured = measure(browser, piece)
                    marks.update(judge(measured))
                    if options.keep:
                        (options.keep / f"{case['id']}-{n}.vue").write_text(piece, encoding="utf-8")
                        (options.keep / f"{case['id']}-{n}.png").write_bytes(measured["screenshot"])
                else:
                    marks.update({c: (False, "no piece") for c in COLUMNS if c != "valid"})
                for c in COLUMNS:
                    totals[c] += marks[c][0]
                print(f"{case['id']:14}" + "".join(f"{('ok' if marks[c][0] else 'FAIL'):>7}" for c in COLUMNS), flush=True)
                if options.verbose:
                    for c in COLUMNS:
                        if not marks[c][0] and marks[c][1]:
                            print(f"{'':14}{c}: {marks[c][1]}")
        browser.close()
    print(f"{'':14}" + "".join(f"{totals[c]}/{runs:>3}"[:7].rjust(7) for c in COLUMNS))
    print(f"\n{model}, {runs} piece(s)")
    return 0 if all(totals[c] == runs for c in COLUMNS) else 1


if __name__ == "__main__":
    sys.exit(main())
