#!/usr/bin/env python3
"""Ayuda a localizar la tabla de DEFINICIÓN de misión por búsqueda de valor conocido.

Dada una recompensa/valor conocido de una misión (p. ej. gil), busca sus apariciones
en la zona de datos y detecta series equiespaciadas (mismo campo en registros
sucesivos), lo que revela el 'stride' del registro y la base de la tabla.

Uso:
  python3 tools/find_mission_table.py <rom.gba> <valor_hex> [ini_hex] [fin_hex]
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import ffta_tools as T
from collections import Counter

def main(a):
    if len(a) < 2:
        print(__doc__); return 1
    d = T.load(a[0]); val = int(a[1], 16)
    ini = int(a[2], 16) if len(a) > 2 else 0x300000
    fin = int(a[3], 16) if len(a) > 3 else 0x720000
    for width in (2, 4):
        needle = val.to_bytes(width, "little")
        hits = [i for i in range(ini, fin - width) if d[i:i+width] == needle]
        if len(hits) < 2:
            print(f"u{width*8}: {len(hits)} coincidencias (insuficiente)"); continue
        deltas = Counter(b - a for a, b in zip(hits, hits[1:]))
        print(f"u{width*8}: {len(hits)} coincidencias. Deltas frecuentes (posible stride):")
        for stride, n in deltas.most_common(5):
            if n >= 2 and 8 <= stride <= 128:
                # base candidata: primer hit alineado a ese stride
                base = min(h for h in hits)
                print(f"   stride={stride:3d}  x{n}  base~{base:#08x}  "
                      f"campo en offset ~{(hits[0]-base) % stride}")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
