# App Android personal — FFTA

App instalable que arranca **directo al juego**, sin emulador visible. Es un
empaquetado, no una conversión: el juego es código ARM7 ligado al hardware de la
GBA, así que dentro de la app corre un núcleo de emulación (**mGBA** compilado a
WebAssembly, vía **EmulatorJS**) con la ROM embebida en los assets.

> **Solo uso personal.** La APK contiene la ROM: no la distribuyas ni la subas a
> ningún sitio. El repo solo guarda el código de la app (la ROM y la APK están en
> `.gitignore`).

## Arquitectura

```
APK
 ├─ classes.dex          MainActivity: WebView + microservidor HTTP en 127.0.0.1
 ├─ assets/index.html    configuración de EmulatorJS (core mgba, es-ES, autostart)
 ├─ assets/data/         frontend EmulatorJS 4.2.3 (npm @emulatorjs/emulatorjs)
 ├─ assets/data/cores/   mgba-wasm.data + mgba-legacy-wasm.data (npm @emulatorjs/core-mgba)
 └─ assets/ffta.gba      tu ROM
```

Decisiones clave:

- **Microservidor HTTP interno** (loopback, puerto efímero) en vez de `file://`:
  evita todas las restricciones de XHR/fetch del WebView. `targetSdk 27` para que
  el tráfico cleartext a localhost no requiera configuración extra.
- **Ambas variantes del core** (`mgba-wasm` y `mgba-legacy-wasm`): EmulatorJS elige
  según las capacidades del navegador; incluir solo una rompe en algunos WebView
  (bug detectado en el smoke test).
- **Sin Android SDK de Google**: se construye con paquetes de Ubuntu (`aapt`,
  `dalvik-exchange`, `zipalign`, `apksigner`, `android-framework-res`) + el jar
  de robolectric como classpath. Útil donde `dl.google.com` no está disponible.
- Controles táctiles: el gamepad virtual integrado de EmulatorJS.
- Guardado: menú de EmulatorJS → Save State (persiste en el almacenamiento del
  WebView de la app). El guardado interno del juego también persiste.

## Construir

```bash
sudo apt install aapt apksigner zipalign dalvik-exchange android-framework-res
cd android && ./build.sh /ruta/a/tu/rom.gba FFTA.apk
```

## Instalar en el teléfono

1. Pasá `FFTA.apk` al teléfono (cable, Drive, etc.).
2. Abrila; Android pedirá permitir "instalar apps desconocidas" para ese origen.
3. Aceptá (la firma es tu keystore personal autogenerado).
4. Ícono **FFTA** en el launcher → toca → juego.

## Verificación

Smoke test con Chromium (mismo motor Blink que el WebView de Android) sirviendo
los assets exactos de la APK: la ROM arranca hasta la pantalla de selección de
idioma. Captura en el historial de la conversación.

## Limitaciones conocidas

- Rendimiento: mGBA-wasm en WebView va sobrado para FFTA (juego táctico, no
  exige timing extremo), pero es menor que un emulador nativo.
- Si el WebView del teléfono es muy viejo (< Android 8), actualizá "Android
  System WebView" desde Play.
- El audio arranca tras el primer toque en pantalla si el sistema bloquea el
  autoplay.
