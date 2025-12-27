#!/usr/bin/env python3
"""
Import MQL5 articles to repo as Markdown files with local assets and Notion-derived tags
- Reads phase manifests (phase1/manifest.md etc.)
- Fetches each article, extracts title and main article HTML
- Converts HTML -> Markdown (html2text if available, fallback to simplistic conversion)
- Downloads images and attachments under phaseN/assets/<article_id>
- Writes a Markdown file under phaseN/articles/<article_id>-slug.md
- Builds YAML frontmatter: title, original_url, date (if available), phase, article_id, tags
- Does NOT include author in frontmatter (user requested to remove author)

Usage:
  python import_mql5.py --phase phase1 --dry-run
  python import_mql5.py --all --dry-run

Notes:
- Expects BeautifulSoup, requests and html2text optional
- Uses Notion-like tag extraction rules from gold_standard/scripts/notion_publisher.py

"""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from datetime import datetime
from time import sleep
MAX_ASSET_SIZE = 5 * 1024 * 1024  # 5MB default per asset limit to avoid huge downloads

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    raise SystemExit("Please install dependencies: pip install requests beautifulsoup4")

# Optional: html2text for nicer Markdown
try:
    import html2text
except Exception:
    html2text = None

# Removed tagging logic (user requested no tags).
# ------------------------------ Helper functions ------------------------------


def slugify(title: str) -> str:
    out = re.sub(r"[^a-zA-Z0-9\- ]+", "", title)
    out = out.replace(" ", "-")
    out = re.sub(r"-+", "-", out)
    return out.strip("-")[:150]


def download_asset(url: str, dest_folder: Path) -> Path:
    dest_folder.mkdir(parents=True, exist_ok=True)
    local_filename = url.split("/")[-1]
    local_path = dest_folder / local_filename

    # Use streaming to not consume memory on large files
    # Handle data URI (base64 embedded) like: data:image/jpeg;base64,...
    try:
        # Remove URL fragment if present (e.g. svg#views-usage)
        from urllib.parse import urldefrag
        url, _ = urldefrag(url)
        if url.startswith("data:"):
            import base64
            import hashlib
            # data:[<mediatype>][;base64],<data>
            try:
                header, b64data = url.split(",", 1)
                # attempt to extract file extension from header
                m = re.search(r"data:([\w/+]+);base64", header)
                ext = ".bin"
                if m:
                    mime = m.group(1)
                    if "/" in mime:
                        ext = "." + mime.split("/")[1].split(";")[0]
                # create a filename from md5 to avoid long data URIs
                name_hash = hashlib.md5(b64data.encode("utf-8")).hexdigest()
                local_filename = f"{name_hash}{ext}"
                local_path = dest_folder / local_filename
                data = base64.b64decode(b64data)
                with open(local_path, "wb") as f:
                    f.write(data)
                return local_path
            except Exception as e:
                raise RuntimeError(f"Failed to decode data URI: {e}")
        try:
            resp = requests.get(url, stream=True, headers={"User-Agent": "Mozilla/5.0"}, timeout=(5, 20))
        except Exception as e:
            raise RuntimeError(f"requests.get failed for {url}: {e}")
        if resp.status_code == 200:
            content_len = resp.headers.get('Content-Length')
            if content_len and int(content_len) > MAX_ASSET_SIZE:
                raise RuntimeError(f"Asset too large ({content_len} bytes) - skipping")
            with open(local_path, "wb") as f:
                shutil.copyfileobj(resp.raw, f)
            return local_path
        else:
            raise RuntimeError(f"Failed to download {url} - status {resp.status_code}")
    except Exception as e:
        raise RuntimeError(f"download_asset failed for {url}: {e}")


# ------------------------------ HTML -> Markdown ------------------------------

def html_to_markdown(html: str) -> str:
    if html2text:
        h = html2text.HTML2Text()
        h.wrap_links = False
        h.ignore_images = False
        return h.handle(html)
    else:
        # fallback: use BeautifulSoup to get a near-plain text with some basic markdown:
        soup = BeautifulSoup(html, "html.parser")
        # Convert headings
        for header in soup.find_all(re.compile("^h[1-6]$")):
            level = int(header.name[1])
            header.replace_with(f"\n{'#' * level} {header.get_text(strip=True)}\n")

        # Convert code blocks
        for pre in soup.find_all("pre"):
            code_text = pre.get_text()
            pre.replace_with("\n```\n" + code_text + "\n```\n")

        # Convert images: already handled separately
        for img in soup.find_all("img"):
            alt = img.get("alt", "")
            src = img.get("src", "")
            img.replace_with(f"![{alt}]({src})")

        # Convert links
        for a in soup.find_all("a"):
            href = a.get("href", "")
            text = a.get_text(strip=True)
            a.replace_with(f"[{text}]({href})")

        text = soup.get_text("\n")
        # Collapsing multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text


# ------------------------------ Article import flow ------------------------------

def parse_phase_manifest(manifest_path: Path) -> list[dict]:
    """Return list of dicts with title, url, article_id (if present) from a simple manifest.md"""
    entries = []
    content = manifest_path.read_text(encoding="utf-8")

    # Look for lines that include a URL and optional article_id:    ..  — https://... (article_id: 20488)
    url_line_regex = re.compile(r"-\s+(.+?)—\s*(https?://[^\s]+)\s*(\(article_id:\s*([0-9]+)\))?", re.IGNORECASE)

    for m in url_line_regex.finditer(content):
        title = m.group(1).strip()
        url = m.group(2).strip()
        article_id = m.group(4) if m.group(4) else None
        entries.append({"title": title, "url": url, "article_id": article_id})

    # If that fails, try to find lines that just contain the URL
    if not entries:
        url_only_regex = re.compile(r"https?://[^)\n\s]+")
        for line in content.splitlines():
            m = url_only_regex.search(line)
            if not m:
                continue
            url = m.group(0)
            title_guess = line.split(url)[0].strip().strip('-').strip()
            entries.append({"title": title_guess or None, "url": url, "article_id": None})

    return entries


def fetch_article_and_save(phase: str, manifest_entry: dict, dry_run=False, verbose=True, assets_enabled: bool = False):
    url = manifest_entry["url"]
    article_id = manifest_entry.get("article_id")
    provided_title = manifest_entry.get("title")

    if verbose:
        print(f"→ Fetching: {url}")

    # Safety check: ensure we don't produce nested docs path. root should be docs/mql5_handbook
    root = Path(__file__).resolve().parent.parent
    root_str = str(root).replace('\\', '/')
    if root_str.count('docs/mql5_handbook') > 1:
        raise RuntimeError(f"Unsafe root path in fetch_article_and_save: {root_str}")

        # Try with retries to handle transient failures
        session = requests.Session()
        max_tries = 3
        for attempt in range(max_tries):
            try:
                resp = session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=(5, 20))
                break
            except Exception as e:
                if attempt == max_tries - 1:
                    raise
                print(f"  ⚠ Retrying ({attempt + 1}/{max_tries}) due to: {e}")
                sleep(1 + attempt)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Title
    title_tag = soup.find("h1")
    title = (title_tag.get_text(strip=True) if title_tag else provided_title) or "Untitled"

    # Date - try to find a typical date format in the meta or page
    date_tag = soup.find("time") or soup.find("span", class_=re.compile(r"date|time|published", re.I))
    date_str = None
    if date_tag:
        date_str = date_tag.get_text(strip=True)
        # try to parse into YYYY-MM-DD
        try:
            parsed_date = datetime.strptime(date_str.strip(), "%d %B %Y")
            date_str = parsed_date.isoformat().split("T")[0]
        except Exception:
            # keep what we got
            pass

    # Main article body: prefer div.article__text, article, or div[itemprop=articleBody]
    body = soup.find("div", class_=re.compile(r"article__text|article-text|article_text|main-article|article_body|article__body"))
    if not body:
        body = soup.find("article")
    if not body:
        # fallback: find section with many paragraphs
        paragraphs = soup.find_all("p")
        if len(paragraphs) > 3:
            body = BeautifulSoup('\n'.join([str(p) for p in paragraphs[:100]]), "html.parser")
        else:
            # fallback to entire HTML
            body = soup

    # Convert HTML to markdown-ish
    try:
        md_body = html_to_markdown(str(body))
    except Exception as e:
        print(f"  ⚠ HTML -> MD conversion failed for {url}: {e}. Falling back to text extraction.")
        md_body = BeautifulSoup(str(body), "html.parser").get_text("\n")

    # Tagging removed — per user request do not produce tags
    tags = []

    # Replace images and download them (skip downloading when dry_run)
    article_assets_dir = Path(__file__).resolve().parent.parent / phase / "assets"
    if article_id:
        article_assets_dir = article_assets_dir / str(article_id)
    else:
        article_assets_dir = article_assets_dir / slugify(title)

    # Find images inside the body -- we used src to inline; convert them to relative
    soup_body = BeautifulSoup(str(body), "html.parser")
    for img in soup_body.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if not src:
            continue
        # Normalize URL
        if src.startswith("//"):
            src = "https:" + src
        if src.startswith("/"):
            src = "https://www.mql5.com" + src

        # Download image to assets
        try:
            if not dry_run and assets_enabled:
                local_path = download_asset(src, article_assets_dir)
            else:
                local_path = article_assets_dir / Path(src.split('/')[-1])
            # Make a relative path for the markdown file
            rel_path = os.path.relpath(local_path, (Path(__file__).resolve().parent.parent / phase))
            # Replace in markdown text (we have previous md_body generated before) - safe approach: add new markdown for images
            md_body = md_body.replace(src, rel_path.replace("\\", "/"))
        except Exception as e:
            print(f"  ⚠ Asset download failed for {src}: {e}")

    # Handle attachments with /download in anchors
    for a in soup_body.find_all("a", href=True):
        href = a.get("href")
        if href and '/download/' in href:
            if href.startswith("/"):
                href = "https://www.mql5.com" + href
            try:
                if not dry_run and assets_enabled:
                    local_path = download_asset(href, article_assets_dir)
                else:
                    local_path = article_assets_dir / Path(href.split('/')[-1])
                rel_path = os.path.relpath(local_path, (Path(__file__).resolve().parent.parent / phase))
                md_body = md_body.replace(href, rel_path.replace("\\", "/"))
            except Exception as e:
                print(f"  ⚠ Attachment download failed {href}: {e}")

    # Build YAML frontmatter (no author)
    frontmatter = {
        "title": title,
        "original_url": url,
        "phase": phase,
    }

    if article_id:
        frontmatter["article_id"] = str(article_id)
    if date_str:
        frontmatter["date"] = date_str

    # Write markdown file to phase/articles
    dest_dir = Path(__file__).resolve().parent.parent / phase / "articles"
    dest_dir.mkdir(parents=True, exist_ok=True)

    slug = slugify(title)
    filename = f"{article_id or 'noid'}-{slug}.md"
    out_path = dest_dir / filename

    yaml_text = "---\n"
    for k, v in frontmatter.items():
        if isinstance(v, list):
            yaml_text += f"{k}: [{', '.join([repr(x) for x in v])}]\n"
        else:
            yaml_text += f"{k}: \"{v}\"\n"
    yaml_text += "---\n\n"

    md_content = yaml_text + "# " + title + "\n\n" + md_body

    if dry_run:
        print(f"  (dry run) would write: {out_path}")
    else:
        out_path.write_text(md_content, encoding="utf-8")
        print(f"  ✓ Wrote: {out_path}")

    return {
        "file": str(out_path),
        "title": title,
        "assets_dir": str(article_assets_dir),
    }


def run_import(phases: list[str], dry_run: bool = True, verbose: bool = True, assets_enabled: bool = False):
    # The parent.parent directory is already the `docs/mql5_handbook` directory
    root = Path(__file__).resolve().parent.parent
    # Safety assertion: ensure we don't generate path with duplicate `docs/mql5_handbook` components
    root_str = str(root).replace('\\', '/')
    if root_str.count('docs/mql5_handbook') > 1:
        raise RuntimeError(f"Unsafe root path detected (duplicate docs): {root_str}")

    manifest_files = []
    for phase in phases:
        mf = root / phase / "manifest.md"
        if not mf.exists():
            print(f"Manifest missing for {phase}: {mf}")
            continue
        manifest_files.append(mf)

    print(f"Phases to import: {', '.join(phases)}")

    for mf in manifest_files:
        entries = parse_phase_manifest(mf)
        print(f"Found {len(entries)} entries in {mf.name}")

        for entry in entries:
            try:
                result = fetch_article_and_save(mf.parent.name, entry, dry_run=dry_run, verbose=verbose, assets_enabled=assets_enabled)
                if verbose and not dry_run:
                    print(f"  Saved file: {result['file']}")
            except Exception as e:
                print(f"  ✗ Failed to import {entry['url']}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import MQL5 articles to docs/mql5_handbook")
    parser.add_argument("--phase", type=str, help="Phase to import (phase1, phase2, phase3)")
    parser.add_argument("--all", action="store_true", help="Import all phases")
    parser.add_argument("--dry-run", action="store_true", help="Don't write files, show actions")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--assets", action="store_true", help="Download assets (images and attachments). Default: False")

    args = parser.parse_args()

    phases = []
    if args.all:
        phases = ["phase1", "phase2", "phase3"]
    elif args.phase:
        phases = [args.phase]
    else:
        print("Please specify --phase or --all")
        sys.exit(1)

    if not args.dry_run:
        print("⚠️  Running importer in WRITE mode - files will be modified. Use --dry-run to preview first.")

    run_import(phases=phases, dry_run=args.dry_run, verbose=args.verbose, assets_enabled=args.assets)
