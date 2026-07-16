"""Toolkit de ROM hacking para GBA (FFTA). Funciones reutilizables."""
import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB

ROM_BASE = 0x08000000

def load(path):
    return bytearray(open(path,'rb').read())

def header(d):
    return {
        'title': d[0xA0:0xAC].split(b'\x00')[0].decode('ascii','replace'),
        'game_code': d[0xAC:0xB0].decode('ascii','replace'),
        'maker': d[0xB0:0xB2].decode('ascii','replace'),
        'version': d[0xBC],
    }

def disasm(d, off, count=16, thumb=False):
    """Desensambla `count` instrucciones desde offset de archivo `off`."""
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB if thumb else CS_MODE_ARM)
    out=[]
    for i in md.disasm(bytes(d[off:off+count*4]), ROM_BASE+off):
        out.append(f"{i.address:08X}: {i.mnemonic:<7} {i.op_str}")
        if len(out)>=count: break
    return out

def lz77_decompress(d, off):
    """Descomprime datos LZ77 (formato BIOS GBA, SWI 0x11/0x12). off = byte de cabecera 0x10."""
    assert d[off]==0x10, f"No es LZ77 en {off:#x} (byte={d[off]:#x})"
    size = d[off+1] | (d[off+2]<<8) | (d[off+3]<<16)
    src = off+4; out=bytearray()
    while len(out)<size:
        flags = d[src]; src+=1
        for b in range(8):
            if len(out)>=size: break
            if flags & (0x80>>b):
                info = (d[src]<<8)|d[src+1]; src+=2
                length = (info>>12)+3
                disp = (info & 0xFFF)+1
                start = len(out)-disp
                for k in range(length):
                    out.append(out[start+k])
            else:
                out.append(d[src]); src+=1
    return bytes(out), src-off  # datos, tamaño comprimido consumido

def find_lz77_blocks(d, start=0, end=None, min_size=256, limit=20):
    """Localiza cabeceras LZ77 plausibles (0x10 + tamaño coherente)."""
    end = end or len(d)
    hits=[]
    i=start
    while i < end-4 and len(hits)<limit:
        if d[i]==0x10:
            size = d[i+1]|(d[i+2]<<8)|(d[i+3]<<16)
            if min_size<=size<=0x20000:
                try:
                    dec,comp = lz77_decompress(d,i)
                    if len(dec)==size and comp>16:
                        hits.append((i,size,comp))
                        i+=comp; continue
                except Exception:
                    pass
        i+=4  # las cabeceras suelen estar alineadas a 4
    return hits

def find_pointer_tables(d, min_run=8, start=0, end=None):
    """Encuentra series de punteros 0x08xxxxxx consecutivos (tablas de datos)."""
    end = end or len(d)
    tables=[]; i=start; run=[]
    while i < end-4:
        w = int.from_bytes(d[i:i+4],'little')
        if 0x08000000 <= w < 0x08000000+len(d):
            run.append(i)
        else:
            if len(run)>=min_run:
                tables.append((run[0], len(run)))
            run=[]
        i+=4
    if len(run)>=min_run: tables.append((run[0],len(run)))
    return tables
