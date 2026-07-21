# Mejoras de gráficos y fluidez — estado del análisis

## 1. Gráficos: realce de paletas ✅ (parche generado)

La GBA no permite subir resolución ni profundidad de color (hardware fijo: 240×160,
tiles 4bpp, BGR555). La mejora visual viable es **repaletizado**.

### Hallazgos

- Región de gráficos `0xB00000–0xD80000`: **~5500 paletas** BGR555 plausibles
  (16 colores, alineadas a 32 bytes), agrupadas en **328 bancos** de ≥4 paletas
  consecutivas (3363 paletas en bancos).
- Heurística de detección: 16 u16 < `0x8000`, ≥8 colores únicos, rampa de
  luminancia suave, color 0 habitualmente transparente (score > 2.6).

### Herramienta

`tools/palette_boost.py` — escanea los bancos, sube saturación/brillo en HSV y
emite un **parche IPS** (no modifica la ROM original; el color 0 transparente se
respeta):

```bash
python3 tools/palette_boost.py rom.gba vibrant.ips 1.35 1.08
```

Parche de referencia generado sobre la ROM AFXP: 3363 paletas, 82 823 bytes
modificados, cabecera y tamaño intactos (verificado aplicándolo en memoria).
Aplicación: renombrar el `.ips` como la ROM y mGBA lo aplica al vuelo, o usar
Floating IPS. Ajustar `sat`/`val` al gusto y regenerar.

**Pendiente de validación visual en emulador.** El escáner es heurístico: si algún
banco fuese un falso positivo se vería como colores raros en un gráfico concreto;
en ese caso, bajar el umbral de score o excluir ese banco y regenerar.

## 2. Fluidez: constantes de espera ⏳ (requiere paso dinámico)

FFTA corre a 60 fps; la lentitud percibida son **esperas deliberadas** (velocidad
de texto, pausas de animación, delays de IA). Son constantes en código Thumb.

### Hallazgos estáticos

- El juego **no** usa `VBlankIntrWait` (swi 5) para sus esperas de juego: los
  hits de `05 df` en `0x15bcxx`/`0x15d3xx` caen en datos, no en código (el
  desensamblado produce opcodes ARMv7 inexistentes en ARM7TDMI).
- Sincronización real: **dispatcher de IRQ propio** en ROM `0xFC` (instalado en
  `0x03007FFC` por el boot). Lee `REG_IE/IF` (`0x04000200`), y despacha por bits:
  VBlank (bit 0) → rama `0x18C`, vía tabla de handlers en RAM.
- Consecuencia: los bucles de espera del juego consultan un **contador de frames
  en IWRAM** incrementado por el handler de VBlank. Ese contador vive en RAM, así
  que su dirección no puede fijarse solo con análisis estático de la ROM.

### Siguiente paso (emulador)

1. En mGBA: pausar durante un diálogo lento y buscar en IWRAM (`0x03000000+`) el
   contador que se incrementa 1/frame (memory search: "increased by 1").
2. Watchpoint de lectura sobre ese contador → los `LDR` que disparan son las
   rutinas de espera; los inmediatos comparados contra él (p. ej. `cmp rN, #8`)
   son las **constantes de velocidad** (texto, animación, cursor).
3. Localizado el inmediato en ROM, el parche es de 1–2 bytes por constante
   (`#8 → #2`), empaquetable en el mismo IPS.
