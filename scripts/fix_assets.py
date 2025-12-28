import os
import sys
from pathlib import Path

ROOT = Path(r"c:\workspace\cthulu")
assets = [ROOT / 'assets' / 'cthulu-black.png', ROOT / 'assets' / 'cthulu-white.png']

def hexdump(b):
    return ' '.join(f"{x:02x}" for x in b[:16])


def ensure_pillow():
    try:
        from PIL import Image
        return Image
    except Exception:
        print('Pillow not found, attempting to install...')
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'Pillow'])
        try:
            from PIL import Image
            return Image
        except Exception as e:
            print('Failed to import Pillow after install:', e)
            raise


def process(path, Image):
    print('\nProcessing:', path)
    if not path.exists():
        print('  MISSING')
        return False
    try:
        with open(path, 'rb') as f:
            hdr = f.read(8)
        print('  header:', hexdump(hdr))
        png_sig = bytes([0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A])
        if hdr != png_sig:
            print('  WARNING: file does not start with PNG signature')
            # Detect UTF-8 replacement sequence that may have replaced 0x89
            if hdr.startswith(b'\xef\xbf\xbdPNG'):
                print('  Detected UTF-8 replacement for 0x89; attempting to repair header')
                with open(path, 'rb') as f:
                    data = f.read()
                # Replace leading 3 bytes (0xEF 0xBF 0xBD) with single 0x89 byte
                if data.startswith(b'\xef\xbf\xbd'):
                    new_data = b'\x89' + data[3:]
                    # write repaired bytes to a .repaired.png file to avoid destructive overwrites
                    repaired_path = path.with_name(path.stem + '.repaired' + path.suffix)
                    with open(repaired_path, 'wb') as f:
                        f.write(new_data)
                    print('  Header repaired to', repaired_path)
                    print('  new header:', hexdump(new_data[:8]))
                    # use repaired_path for subsequent checks
                    path = repaired_path
                    hdr = new_data[:8]
                else:
                    print('  Unexpected header pattern; skipping automatic repair')
        # Try to open with Pillow
        img = Image.open(path)
        img.load()
        print(f'  opened OK - format={img.format}, mode={img.mode}, size={img.size}')
        # Convert to RGBA for safety
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        out_path = path
        # overwrite with optimized PNG
        img.save(out_path, format='PNG', optimize=True)
        sz = out_path.stat().st_size
        print(f'  re-saved OK, size={sz} bytes')
        return True
    except Exception as e:
        print('  ERROR processing image:', e)
        return False


if __name__ == '__main__':
    Image = ensure_pillow()
    all_ok = True
    for p in assets:
        ok = process(p, Image)
        all_ok = all_ok and ok
    if all_ok:
        print('\nAll assets processed successfully')
    else:
        print('\nOne or more assets failed to process. Consider replacing corrupted files.')
