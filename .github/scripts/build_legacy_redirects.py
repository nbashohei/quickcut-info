"""Build a GitHub-Pages-only redirect artifact; never modify Cloudflare sources."""
import argparse
import html
import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape

SOURCE = Path(__file__).resolve().parents[2]
OLD_BASE = "https://nbashohei.github.io/quickcut-info/"
NEW_BASE = "https://quickcut.app/"


class HeadLinks(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.canonicals = []
        self.languages = {}
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "link" and a.get("rel") == "canonical":
            self.canonicals.append(a["href"])
        if tag == "link" and a.get("rel") == "alternate" and a.get("hreflang") != "x-default":
            self.languages[a["hreflang"].lower()] = a["href"]


def validate_target(url):
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.netloc != "quickcut.app" or
            parts.query or parts.fragment or not re.fullmatch(r"/[A-Za-z0-9/_.-]*", parts.path)):
        raise ValueError(f"Unsafe canonical target: {url}")
    return url


def render_redirect(target, languages=None):
    target = validate_target(target)
    languages = languages or {}
    for url in languages.values():
        validate_target(url)
    # Static zero-second refresh is visible to crawlers without JavaScript.
    # JS augments it with query/fragment preservation for old app deep links.
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QuickCut — moved to quickcut.app</title>
<link rel="canonical" href="{html.escape(target, quote=True)}">
<meta id="redirect" http-equiv="refresh" content="0; url={html.escape(target, quote=True)}">
<script>
(() => {{
  let target = new URL({json.dumps(target)});
  const languages = {json.dumps(languages, sort_keys=True)};
  let code = '';
  try {{ code = decodeURIComponent(location.hash.slice(1)).toLowerCase(); }} catch {{}}
  if (Object.prototype.hasOwnProperty.call(languages, code)) {{
    target = new URL(languages[code]);
  }} else {{
    target.hash = location.hash;
  }}
  target.search = location.search;
  document.getElementById('redirect').content = '0; url=' + target.href;
  document.addEventListener('DOMContentLoaded', () => {{
    document.getElementById('destination').href = target.href;
  }});
  location.replace(target.href);
}})();
</script>
</head><body>
<h1>QuickCut has moved</h1>
<p><a id="destination" href="{html.escape(target, quote=True)}">Continue to quickcut.app</a></p>
</body></html>
'''


def build(source, output):
    source, output = source.resolve(), output.resolve()
    if output == source or source in output.parents or output in source.parents:
        raise ValueError("Output must be outside the source checkout")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output directory must be empty; existing files are never removed")
    pages = sorted(p for p in source.rglob("*.html")
                   if not any(part.startswith('.') for part in p.relative_to(source).parts)
                   and p.relative_to(source).parts[0] != "assets")
    planned, verification = [], []
    for page in pages:
        relative = page.relative_to(source)
        text = page.read_text(encoding="utf-8")
        if re.fullmatch(r"google[\w-]+\.html", page.name) and text.strip().startswith("google-site-verification:"):
            verification.append(relative)
            continue
        links = HeadLinks(text)
        if len(links.canonicals) != 1:
            raise ValueError(f"Expected one canonical in {relative}")
        target = validate_target(links.canonicals[0])
        content = render_redirect(target, links.languages if relative == Path("index.html") else None)
        planned.append((relative, target, content))
    if not planned:
        raise ValueError("No public HTML pages found")
    output.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for relative, target, content in planned:
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        manifest[relative.as_posix()] = target
        # Also support extensionless old help/privacy/licenses URLs.
        if relative.parent == Path('.') and relative.name != "index.html":
            alias = output / relative.stem / "index.html"
            alias.parent.mkdir(parents=True, exist_ok=True)
            alias.write_text(content, encoding="utf-8")
            manifest[relative.stem + "/index.html"] = target
    for relative in verification:
        shutil.copyfile(source / relative, output / relative)
    # Keep previously public media URLs working; no private production files copied.
    if (source / "assets").is_dir():
        if any(p.is_symlink() for p in (source / "assets").rglob('*')):
            raise ValueError("Asset symlinks are not allowed")
        shutil.copytree(source / "assets", output / "assets")
    (output / ".nojekyll").touch()
    (output / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {NEW_BASE}sitemap.xml\n")
    # Old sitemap remains available to help crawlers revisit the moved URLs.
    urls = [OLD_BASE + (p[:-10] if p.endswith('index.html') else p) for p in manifest]
    (output / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'  <url><loc>{escape(url)}</loc></url>\n' for url in urls) + '</urlset>\n')
    (output / "redirect-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    # Unknown URLs remain real 404s, not misleading redirects to the home page.
    (output / "404.html").write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Page not found</title><h1>Page not found</h1><p>QuickCut is now at <a href="https://quickcut.app/">quickcut.app</a>.</p></html>\n')
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = build(SOURCE, args.output)
    print(f"Built {len(manifest)} redirect entry points in {args.output}")
