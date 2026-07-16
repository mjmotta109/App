# Análisis de la ROM — Final Fantasy Tactics Advance (Europe)

> La ROM **no** está en el repositorio (`.gitignore` excluye `*.gba`). Colocá tu
> propia copia legal junto al toolkit para reproducir este análisis.

## Identificación

| Campo            | Valor                                  |
|------------------|----------------------------------------|
| Juego            | Final Fantasy Tactics Advance          |
| Región           | Europe (En, Fr, De, Es, It)            |
| Título interno   | `FFTA_INTER.`                          |
| Game code        | `AFXP`                                 |
| Maker code       | `01` (Nintendo)                        |
| Versión          | `0`                                    |
| Tamaño           | 16 MB (16 777 216 bytes)               |
| Datos reales     | terminan en `0xFFFC00` (resto `0xFF`)  |
| CPU              | ARM7TDMI (ARM + Thumb)                  |
| Base en memoria  | `0x08000000`                           |

El *entry point* (`0x00`) es un salto ARM `B` a `0x080000C0`, tras la cabecera de
192 bytes. El arranque es el runtime estándar de GBA:

```
080000C0: mov  r0, #0x12        ; modo IRQ
080000C4: msr  cpsr_fc, r0
080000C8: ldr  sp, [pc, #0x28]  ; stack IRQ
080000CC: mov  r0, #0x1f        ; modo System
080000D0: msr  cpsr_fc, r0
080000D4: ldr  sp, [pc, #0x18]  ; stack usuario
...
080000EC: bx   r1               ; salto al runtime C
```

## Mapa de la ROM (por entropía, bloques de 512 KB)

| Rango                 | Contenido probable                     |
|-----------------------|----------------------------------------|
| `0x000000–0x180000`   | Código del motor + datos               |
| `0x180000–0x300000`   | Audio crudo (entropía > 7.5)           |
| `0x300000–0x480000`   | Tablas de datos                        |
| `0x500000–0x880000`   | Datos empaquetados / texto / tablas    |
| `0x900000–0xA80000`   | **Hueco libre** (relleno) — insertable |
| `0xB00000–0xD80000`   | Gráficos / mapas                       |
| `0xD80000–0xFFFC00`   | **Relleno `0xFF`** — zona libre grande |

Las dos zonas de relleno (`0x900000` y `0xD80000+`) son espacio aprovechable para
insertar datos nuevos (misiones, tablas ampliadas) sin pisar contenido existente.

## Tablas de punteros localizadas

Series de punteros `0x08xxxxxx` consecutivos (candidatas a tablas de datos que el
juego indexa: habilidades, objetos, unidades, misiones, gráficos):

| Offset ROM   | Nº entradas |
|--------------|-------------|
| `0x71E57C`   | 100         |
| `0x720D40`   | 767         |
| `0x724C34`   | 753         |
| `0x7274C8`   | 725         |
| `0x72C3F8`   | 512         |
| `0x72F378`   | 767         |

## Compresión

FFTA usa **LZ77 de la BIOS de GBA** (cabecera `0x10`) de forma selectiva (p. ej.
bloque confirmado en `0xB00D9C`: 1104 B descomprimidos). Buena parte de los
gráficos van en contenedores propios referenciados por las tablas de punteros, no
como LZ77 plano. El audio de `0x180000–0x300000` no está comprimido con LZ77.

## Texto

Casi no hay ASCII legible: el texto usa **codificación propia con font table**.
Editar diálogos requiere reconstruir el `.tbl` y respetar los punteros.
