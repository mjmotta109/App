# Guía de modding — FFTA (AFXP)

Hoja de ruta para los cuatro objetivos, de más fácil a más difícil. Todo el trabajo
se hace con `tools/ffta_tools.py` y un emulador (mGBA recomendado) para probar.

> **Legal:** el ROM hacking para uso personal con una copia propia es legítimo. No
> distribuyas la ROM ni parches que la incluyan. Comparte solo parches IPS/UPS.

## Flujo de trabajo general

1. Trabajar sobre una **copia** de la ROM, nunca el original.
2. Localizar la tabla/dato con el toolkit.
3. Editar bytes con un editor hex o script Python.
4. Probar en mGBA (savestates para iterar rápido).
5. Generar parche: `flips --create original.gba modificada.gba parche.bps`.

---

## 1. Stats / balance  *(dificultad: baja)*

Lo más accesible. Los stats de jobs, armas, objetos y leyes están en tablas de
registros de tamaño fijo en la zona `0x300000+` y `0x500000+`.

**Método:**
- Ubicar la tabla con `find_pointer_tables` o buscando valores conocidos (p. ej. el
  precio de un objeto en la tienda) con búsqueda de valor.
- Deducir el *stride* (tamaño de registro) mirando la repetición de patrones.
- Editar el campo (daño, coste MP, precio…) respetando su ancho (1–2 bytes).

**Riesgo:** bajo. No cambia tamaños ni punteros.

---

## 2. Gráficos / sprites  *(dificultad: media)*

Tiles GBA 4bpp (16 colores) + paletas de 16 colores (BGR555).

**Método:**
- Si el asset es LZ77: `lz77_decompress()` → editar tiles → recomprimir → reinsertar.
  Si el recomprimido es más grande, insertarlo en zona libre (`0xD80000+`) y
  actualizar el puntero.
- Si va sin comprimir: editar directamente con un editor de tiles (formato GBA 4bpp).
- Paletas: 32 bytes por paleta, colores BGR555 (`0bBBBBBGGGGGRRRRR`).

**Riesgo:** medio. Cuidado con el orden de tiles y el tamaño tras recomprimir.

---

## 3. Desensamblar código  *(dificultad: alta)*

Para cambiar *lógica* (fórmulas de daño, IA, condiciones de misión).

**Método:**
- `disasm(d, off, thumb=True/False)` con capstone. La mayoría del código de juego
  es **Thumb**; el arranque y algunas rutinas son ARM.
- Identificar la rutina siguiendo referencias desde las tablas de punteros.
- Parchear instrucciones (p. ej. cambiar un `bne` por `beq`, o un inmediato).
- Para código nuevo, ensamblar con `arm-none-eabi-as` e insertarlo en zona libre,
  redirigiendo con un `bl`/`b`.

**Riesgo:** alto. Un byte mal deja la ROM inarrancable; usar savestates y diffs.

---

## 4. Agregar misiones  *(dificultad: muy alta — mini-proyecto)*

Es el objetivo más complejo porque combina datos + texto + lógica. Plan realista:

**Fase A — Entender el formato de misión.**
Las misiones (quests del pub) son registros que enlazan: texto de descripción,
recompensas (gil, objetos, AP), requisitos (nivel, objetos a entregar), tipo de
despacho o batalla, y mapa asociado. Hay que localizar la **tabla de misiones**
(una de las tablas de punteros grandes) y mapear cada campo del registro
comparando dos misiones conocidas.

**Fase B — Clonar una misión existente.**
El primer hito no es "inventar" sino **duplicar** una misión que ya funciona:
copiar su registro a una entrada nueva y verificar que aparece en el pub. Esto
valida que entendimos el formato y el sistema de conteo de misiones.

**Fase C — Ampliar la tabla.**
Si el juego tiene un contador fijo de misiones, hay que:
- Mover/expandir la tabla de misiones a zona libre (`0x900000` o `0xD80000+`).
- Actualizar el puntero base y el contador (que probablemente esté *hardcodeado*
  en el código → requiere el objetivo 3, desensamblado).

**Fase D — Contenido nuevo.**
Recompensas, requisitos, texto (objetivo texto/`.tbl`) y, si es batalla, un mapa y
colocación de enemigos.

**Riesgo:** muy alto. Recomiendo abordarlo por fases y celebrar la Fase B (clon
funcional) como primer gran hito antes de crear contenido original.

---

## Herramientas externas recomendadas

- **mGBA** — emulador con debugger, viewer de memoria/tiles/paletas.
- **Floating IPS (flips)** — crear/aplicar parches BPS/IPS.
- **arm-none-eabi-binutils** — `as`/`objdump` para código nuevo (`apt install`).
- **Tinke / GBA Graphics Editor** — para tiles y paletas.
