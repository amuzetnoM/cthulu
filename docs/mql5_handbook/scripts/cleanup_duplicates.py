#!/usr/bin/env python3
"""
Consolidate duplicated files under `docs/mql5_handbook/docs/mql5_handbook/*` into `docs/mql5_handbook/*`.
- Moves articles and assets from duplicate path into canonical path whenever necessary.
- Removes duplicate folders once consolidated.
"""

import shutil
from pathlib import Path
import filecmp

ROOT = Path(__file__).resolve().parent.parent
DUP_ROOT = ROOT / "docs" / "mql5_handbook"
CAN_ROOT = ROOT

PHASES = ["phase1", "phase2", "phase3"]

moved = []
merged_assets = []
skipped = []

for phase in PHASES:
    src_phase = DUP_ROOT / phase
    dst_phase = CAN_ROOT / phase

    if not src_phase.exists():
        continue

    # Articles
    src_articles = src_phase / "articles"
    dst_articles = dst_phase / "articles"
    if src_articles.exists():
        dst_articles.mkdir(parents=True, exist_ok=True)
        for f in src_articles.iterdir():
            if f.is_file():
                dst_file = dst_articles / f.name
                if not dst_file.exists():
                    # Move file
                    shutil.move(str(f), str(dst_file))
                    moved.append(str(dst_file))
                else:
                    # Compare
                    try:
                        same = filecmp.cmp(str(f), str(dst_file), shallow=False)
                    except Exception:
                        same = False
                    if same:
                        f.unlink()
                    else:
                        # Keep canonical (dst_file) and remove duplicate
                        f.unlink()
                        skipped.append(str(f))

    # Assets - merge
    src_assets = src_phase / "assets"
    dst_assets = dst_phase / "assets"
    if src_assets.exists():
        dst_assets.mkdir(parents=True, exist_ok=True)
        for asset_dir in src_assets.iterdir():
            if not asset_dir.is_dir():
                continue
            dst_asset_dir = dst_assets / asset_dir.name
            if not dst_asset_dir.exists():
                shutil.move(str(asset_dir), str(dst_asset_dir))
                merged_assets.append(str(dst_asset_dir))
            else:
                # Merge files inside
                for af in asset_dir.iterdir():
                    dst_af = dst_asset_dir / af.name
                    if not dst_af.exists():
                        shutil.move(str(af), str(dst_af))
                    else:
                        # skip or replace? we'll keep dst_af
                        af.unlink()
                # remove empty asset_dir
                try:
                    asset_dir.rmdir()
                except Exception:
                    pass

# Remove duplicate tree if empty
try:
    # Try to remove the nested folder (docs/mql5_handbook)
    if DUP_ROOT.exists():
        shutil.rmtree(str(DUP_ROOT))
except Exception as e:
    print(f"Failed to remove duplicate dir {DUP_ROOT}: {e}")

print("Consolidation finished")
print(f"Moved articles: {len(moved)}")
print(f"Merged assets: {len(merged_assets)}")
print(f"Removed/skipped duplicates: {len(skipped)}")

if moved:
    for m in moved[:20]:
        print("  move:", m)
if merged_assets:
    for a in merged_assets[:20]:
        print("  merged:", a)
if skipped:
    for s in skipped[:20]:
        print("  skipped:", s)
