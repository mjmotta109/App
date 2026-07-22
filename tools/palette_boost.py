#!/usr/bin/env python3
"""Realza la saturación de las paletas de la ROM y genera un parche IPS.

Escanea la región de gráficos buscando bancos de paletas BGR555 (16 colores,
alineadas a 32 bytes) y solo modifica bancos con >= `min_run` paletas
consecutivas (minimiza falsos positivos). No escribe sobre la ROM original:
emite un .ips aplicable con Floating IPS / mGBA.

Uso:
  python3 tools/palette_boost.py <rom.gba> <salida.ips> [sat=1.35] [val=1.08]
"""
import sys, os, colorsys
sys.path.insert(0, os.path.dirname(__file__))
import ffta_tools as T

GFX_START, GFX_END = 0xB00000, 0xD80000
MIN_RUN = 4

def read_pal(d, off):
    return [int.from_bytes(d[off+2*i:off+2*i+2], 'little') for i in range(16)]

def plausible(d, off):
    cols = read_pal(d, off)
    if any(c >= 0x8000 for c in cols) or len(set(cols)) < 8:
        return False
    rgbs = [((v & 0x1F) << 3, ((v >> 5) & 0x1F) << 3, ((v >> 10) & 0x1F) << 3) for v in cols]
    lums = sorted(0.3*r + 0.6*g + 0.1*b for r, g, b in rgbs)
    smooth = sum(1 for a, b in zip(lums, lums[1:]) if b - a < 40) / 15
    sat = sum(max(c) - min(c) for c in rgbs) / 16
    score = len(set(cols))/16 + smooth + (0.5 if cols[0] == 0 else 0) + min(sat/60, 1)
    return score > 2.6

def find_banks(d):
    offs = [o for o in range(GFX_START, GFX_END, 32) if plausible(d, o)]
    banks, run = [], []
    for o in offs:
        if run and o - run[-1] == 32:
            run.append(o)
        else:
            if len(run) >= MIN_RUN: banks.append(run)
            run = [o]
    if len(run) >= MIN_RUN: banks.append(run)
    return banks

def boost_color(v, sat, val):
    r, g, b = (v & 0x1F)/31, ((v >> 5) & 0x1F)/31, ((v >> 10) & 0x1F)/31
    h, s, vv = colorsys.rgb_to_hsv(r, g, b)
    s = min(1.0, s*sat); vv = min(1.0, vv*val)
    r, g, b = colorsys.hsv_to_rgb(h, s, vv)
    return round(r*31) | (round(g*31) << 5) | (round(b*31) << 10)

def write_ips(patches, path):
    with open(path, 'wb') as f:
        f.write(b'PATCH')
        for off, data in patches:
            assert off < 0x1000000 and len(data) < 0x10000
            f.write(off.to_bytes(3, 'big') + len(data).to_bytes(2, 'big') + data)
        f.write(b'EOF')

def main(a):
    if len(a) < 2:
        print(__doc__); return 1
    d = T.load(a[0])
    sat = float(a[2]) if len(a) > 2 else 1.35
    val = float(a[3]) if len(a) > 3 else 1.08
    banks = find_banks(d)
    npal = sum(len(b) for b in banks)
    print(f"bancos: {len(banks)}, paletas a modificar: {npal}")
    patches = []
    for bank in banks:
        for off in bank:
            cols = read_pal(d, off)
            new = b''.join(
                (cols[i] if i == 0 and cols[0] == 0 else boost_color(cols[i], sat, val))
                .to_bytes(2, 'little') for i in range(16))
            old = d[off:off+32]
            if new != old:
                patches.append((off, new))
    write_ips(patches, a[1])
    print(f"IPS escrito: {a[1]} ({len(patches)} registros)")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
