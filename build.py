#!/usr/bin/env python3
"""
build.py — a tiny, dependency-free production build step.

This sandbox has no network access, so real bundlers (esbuild,
terser, vite build) aren't installable here. This script does the
same *category* of work by hand:
  1. Strips comments and blank lines from every JS module
  2. Minifies the CSS (comments, whitespace, redundant newlines)
  3. Concatenates the JS modules in dependency order into one file
     and rewrites the HTML to load a single script instead of an
     ES module graph — fewer requests, faster first paint.
  4. Copies everything into dist/, ready to deploy as-is.

Run: python3 build.py
"""

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"


def minify_js(text: str) -> str:
    out_lines = []
    for line in text.splitlines():
        # Strip // comments (verified safe: no "://" substrings in source)
        line = re.sub(r"(?<!:)//.*$", "", line)
        line = line.rstrip()
        if line.strip() == "":
            continue
        out_lines.append(line)
    code = "\n".join(out_lines)
    # Strip /* */ block comments (non-greedy, none of our files use them
    # for anything but header banners)
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
    return code.strip() + "\n"


def minify_css(text: str) -> str:
    css = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{}:;,])\s*", r"\1", css)
    css = re.sub(r";}", "}", css)
    return css.strip()


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "css").mkdir(parents=True)

    # --- CSS ---
    css_src = (ROOT / "css" / "styles.css").read_text()
    (DIST / "css" / "styles.css").write_text(minify_css(css_src))

    # --- JS: concatenate in dependency order, stripping import/export
    #     so the result runs as a single classic <script> with no
    #     module graph to resolve (fewer network round-trips).
    order = [
        "js/data.js",
        "js/utils.js",
        "js/state.js",
        "js/router.js",
        "js/views/catalog.js",
        "js/views/product.js",
        "js/views/cart.js",
        "js/main.js",
    ]
    bundle_parts = []
    for rel in order:
        src = (ROOT / rel).read_text()
        src = re.sub(r"^\s*import\s.+?;\s*$", "", src, flags=re.MULTILINE)
        src = re.sub(r"^\s*export\s+(default\s+)?", "", src, flags=re.MULTILINE)
        bundle_parts.append(f"/* --- {rel} --- */\n" + minify_js(src))
    bundle = "\n".join(bundle_parts)

    (DIST / "js").mkdir(parents=True)
    (DIST / "js" / "bundle.min.js").write_text(bundle)

    # --- HTML: point at the single bundle + minified CSS ---
    html = (ROOT / "index.html").read_text()
    html = html.replace('href="css/styles.css"', 'href="css/styles.css"')
    html = html.replace(
        '<script type="module" src="js/main.js"></script>',
        '<script src="js/bundle.min.js" defer></script>',
    )
    (DIST / "index.html").write_text(html)

    before = sum((ROOT / rel).stat().st_size for rel in order) + (ROOT / "css" / "styles.css").stat().st_size
    after = (DIST / "js" / "bundle.min.js").stat().st_size + (DIST / "css" / "styles.css").stat().st_size
    print(f"Source (JS+CSS): {before:,} bytes")
    print(f"Dist   (JS+CSS): {after:,} bytes")
    print(f"Reduction: {100 * (1 - after / before):.1f}%")
    print(f"\nBuilt to: {DIST}")


if __name__ == "__main__":
    build()
