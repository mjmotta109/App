#!/usr/bin/env python3
"""CLI del toolkit de romhacking FFTA.

Uso:
  python3 tools/ffta.py header  <rom.gba>
  python3 tools/ffta.py disasm  <rom.gba> <offset_hex> [n] [--thumb]
  python3 tools/ffta.py lz77     <rom.gba> <offset_hex>          # descomprime
  python3 tools/ffta.py findlz   <rom.gba> <ini_hex> <fin_hex>   # busca LZ77
  python3 tools/ffta.py ptrs     <rom.gba> <ini_hex> <fin_hex>   # tablas de punteros
  python3 tools/ffta.py find     <rom.gba> <valor_hex>           # busca un valor (u16/u32)
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import ffta_tools as T

def h(x): return int(x, 16)

def main(a):
    if len(a) < 2:
        print(__doc__); return 1
    cmd, rom = a[0], a[1]
    d = T.load(rom)
    if cmd == "header":
        for k, v in T.header(d).items(): print(f"{k:12}: {v}")
    elif cmd == "disasm":
        off = h(a[2]); n = int(a[3]) if len(a) > 3 and a[3].isdigit() else 16
        thumb = "--thumb" in a
        for line in T.disasm(d, off, n, thumb): print(line)
    elif cmd == "lz77":
        dec, comp = T.lz77_decompress(d, h(a[2]))
        print(f"Descomprimido: {len(dec)} B (consumidos {comp} B comprimidos)")
        print("Primeros 32 B:", dec[:32].hex())
    elif cmd == "findlz":
        for off, size, comp in T.find_lz77_blocks(d, h(a[2]), h(a[3])):
            print(f"{off:#08x}: {comp} B -> {size} B")
    elif cmd == "ptrs":
        for off, n in T.find_pointer_tables(d, 8, h(a[2]), h(a[3])):
            print(f"{off:#08x}: {n} punteros")
    elif cmd == "find":
        val = h(a[2])
        for width in (2, 4):
            needle = val.to_bytes(width, "little")
            hits = [i for i in range(len(d) - width) if d[i:i+width] == needle]
            print(f"u{width*8}: {len(hits)} coincidencias",
                  [f"{x:#x}" for x in hits[:8]], "..." if len(hits) > 8 else "")
    else:
        print(__doc__); return 1
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
