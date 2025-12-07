# MQL5 Handbook Importer

This directory contains import scripts and tooling for creating the `docs/mql5_handbook` content.

import_mql5.py — importer script

Usage examples:

- Dry run for Phase 1 (no files written):
  python import_mql5.py --phase phase1 --dry-run --verbose

- Import all phases and write files:
  python import_mql5.py --all

Notes:
-- The importer does not produce tags in frontmatter — tags and tag extraction were intentionally removed.
- Author frontmatter is intentionally omitted per the user's request; frontmatter will include `title`, `original_url`, `phase`, `date` (where available), `article_id`, and `tags`.
- The importer downloads images and attachments into `docs/mql5_handbook/phaseN/assets/<article_id>/` and rewrites links in Markdown to the relative asset path.
- Optional dependencies: `html2text` to produce nicer Markdown output. The script falls back to a simplified conversion if `html2text` is not present.

Requirements:
- Python 3.10+
- pip install requests beautifulsoup4
- (optional) pip install html2text

Legal / Attribution:
- Articles are stored verbatim with `original_url` metadata and contain a copyright notice when present in the content.
- Please ensure you have rights to reproduce the content in this repo. The import script is meant for internal knowledge management and educational use; if publishing externally, obtain proper permission from the MQL5 author/site.
