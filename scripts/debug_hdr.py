from pathlib import Path
ROOT = Path(r'c:\workspace\cthulu\assets')
files = [ROOT / 'cthulu-black.png', ROOT / 'cthulu-black.repaired.png', ROOT / 'cthulu-white.png', ROOT / 'cthulu-white.repaired.png']

def hexdump(b, n=64):
	return ' '.join(f"{x:02x}" for x in b[:n])

for p in files:
	if not p.exists():
		print(p, 'MISSING')
		continue
	b = p.read_bytes()
	print('\nFile:', p)
	print(' len', len(b))
	print(' hdr', b[:8])
	print(' hdr hex', hexdump(b, 16))
	print(' first 64 hex', hexdump(b, 64))
	# search for IHDR
	ihdr_idx = b.find(b'IHDR')
	print(' IHDR index:', ihdr_idx)
	if ihdr_idx!=-1:
		print(' IHDR context:', hexdump(b[ihdr_idx-8:ihdr_idx+24], 40))
