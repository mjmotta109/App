# Ingeniería inversa del sistema de misiones — FFTA (AFXP, Europe)

Resultado del análisis estático de la ROM. Todo son **offsets y layouts** (hechos de
formato), derivados y verificados sobre los bytes. La ROM no se incluye.

## Arquitectura de datos hallada

El "sistema de misiones" no es una sola tabla, sino tres piezas enlazadas:

```
  TEXTO (nombres/descripciones)  ─┐
  DEFINICIÓN de misión (recompensas/requisitos)  ─┼─►  el motor las combina
  SCRIPT de evento/batalla  ─────┘
```

### 1. Tablas de texto (multi-idioma)  — `0x71E57C`+

Cinco tablas de punteros a cadenas, en la zona `0x72xxxx`:

| Tabla        | Entradas | Destino 1º   |
|--------------|----------|--------------|
| `0x71E57C`   | 100      | `0x430248`   |
| `0x720D40`   | 767      | `0x71E70C`   |
| `0x724C34`   | 753      | `0x72193C`   |
| `0x7274C8`   | 725      | `0x725DEC`   |
| `0x72C3F8`   | 512      | `0x72CBF8`   |
| `0x72F378`   | 767      | `0x72CBF8`   |

Las cadenas **no** son ASCII: usan una **font table con diccionario**. Empiezan por
`01 FF 00` o `01 B1 …` y terminan en `00`; los bytes `0x80xx` son códigos de
diccionario (par de bytes → sílaba/palabra). Editar texto = reconstruir el `.tbl` +
respetar terminadores y punteros.

### 2. Raíces de datos referenciadas desde el código — `0x300000`–`0x340000`

Punteros `0x08xxxxxx` incrustados en el código (`0x000000`–`0x180000`) que apuntan a
`0x30xxxx`. Son las bases de las estructuras que el motor indexa (formaciones, mapas,
eventos). Patrón recurrente en los registros: `00 00 00 40 00 0C D1 00 <u32>`.

### 3. Tabla de scripts de evento/batalla — `0x3384E4`+  *(formato verificado)*

Contenedor de scripts, un registro por evento/batalla. **Layout confirmado en 23/23
registros:**

```
struct EventScript {
    u8   count;        // nº de sub-scripts (actores/fases)
    u8   pad;          // 0x00
    u8   flag;         // 0x01
    u8   mode;         // 0xA8
    u32  interp_ptr;   // SIEMPRE 0x0814D9FC  (intérprete del bytecode)
    u32  sub_ptr[count]; // punteros 0x0833xxxx a cada bloque de bytecode
    /* ... bloques de bytecode a continuación ... */
};
```

Ejemplos: `0x3384E4` count=12, `0x33869C` count=5, `0x338A08` count=4,
`0x338C74` count=2.

**Bytecode del script** (intérprete en `0x0814D9FC`): stream de comandos de 1 byte +
operandos. Comandos observados: `BC 00` (inicio actor), `BB xx` (¿id/pos?),
`BD xx`/`BE xx` (coordenadas), `C4 00`, `BF 40`, `C1 xx`, `C0 40`, `86 …` (bloque de
animación con tripletas tipo `d7 34 88` = comando/valor/param). `B0` = relleno/NOP.

## Lo que falta: la tabla de DEFINICIÓN de misión

La tabla que liga cada misión con su **nombre (id de texto), descripción (id),
recompensa (gil/AP/objetos), requisitos (nivel, objetos, días) y tipo** es un array
de registros compactos de tamaño fijo, todavía sin localizar por análisis estático
(no tiene una firma tan marcada como el intérprete `0x0814D9FC`).

### Cómo fijarla (dos vías)

1. **Búsqueda por valor conocido (estática).** Tomar una misión con datos conocidos
   (p. ej. recompensa exacta en gil de una misión temprana) y buscar ese u16/u32 con
   `python3 tools/ffta.py find rom.gba <valor>`. Las coincidencias en la zona de
   datos, repetidas a intervalo fijo, revelan el registro y su *stride*.
2. **Watchpoint en emulador (dinámica, más fiable).** En mGBA, poner un breakpoint de
   lectura sobre la RAM donde el juego carga los datos de la misión al abrir el pub;
   el `LDR` que dispara apunta a la base de la tabla en ROM. De ahí se deduce el
   *stride* y cada campo.

Una vez fijada la tabla y su *stride*, "agregar una misión" sigue el plan por fases de
`MODDING_GUIDE.md`: **clonar** una entrada existente → ampliar la tabla hacia zona
libre (`0x900000` / `0xD80000+`) → parchear el contador (probablemente *hardcodeado*,
requiere el objetivo de desensamblado) → enlazar texto, recompensas y un `EventScript`
nuevo para la batalla.
