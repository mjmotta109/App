# FFTA ROM Hacking Toolkit

Herramientas y documentación para analizar y modificar **Final Fantasy Tactics
Advance** (GBA, game code `AFXP`, Europe).

> ⚠️ **La ROM NO se incluye** (excluida en `.gitignore`). Usá tu propia copia legal.
> El ROM hacking para uso personal es legítimo; no distribuyas la ROM ni parches
> que la contengan — comparte solo parches IPS/BPS.

## Contenido

- `tools/ffta_tools.py` — librería: cabecera GBA, desensamblado ARM/Thumb (capstone),
  descompresor LZ77, buscador de bloques LZ77 y de tablas de punteros.
- `tools/ffta.py` — CLI sobre la librería.
- `docs/ROM_ANALYSIS.md` — análisis de la ROM (mapa, tablas, arranque).
- `docs/MODDING_GUIDE.md` — hoja de ruta para stats, gráficos, código y misiones.

## Requisitos

```bash
pip install capstone
```

## Uso rápido

```bash
python3 tools/ffta.py header "FFTA.gba"
python3 tools/ffta.py disasm "FFTA.gba" 0xC0 12          # arranque ARM
python3 tools/ffta.py disasm "FFTA.gba" 0x100 8 --thumb  # código Thumb
python3 tools/ffta.py ptrs   "FFTA.gba" 0x400000 0x900000  # tablas de datos
python3 tools/ffta.py lz77   "FFTA.gba" 0xB00D9C         # descomprimir bloque
python3 tools/ffta.py find   "FFTA.gba" 0x03E8           # buscar valor 1000
```
