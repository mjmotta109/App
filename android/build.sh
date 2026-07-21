#!/bin/bash
# Construye la APK personal de FFTA (WebView + EmulatorJS/mGBA + ROM embebida).
# La ROM NO está en el repo: pasá la tuya como argumento.
#
# Uso:  ./build.sh /ruta/a/tu/rom.gba [salida.apk]
#
# Dependencias (Ubuntu): aapt apksigner zipalign dalvik-exchange android-framework-res
#                        openjdk (javac/keytool), npm, curl
set -euo pipefail

ROM="${1:?Uso: ./build.sh rom.gba [salida.apk]}"
OUT="${2:-FFTA.apk}"
HERE="$(cd "$(dirname "$0")" && pwd)"
BUILD="$HERE/build"
EJS_VER=4.2.3
ANDROID_ALL_URL="https://repo1.maven.org/maven2/org/robolectric/android-all/9-robolectric-4913185-2/android-all-9-robolectric-4913185-2.jar"
FRAMEWORK_RES=/usr/share/android-framework-res/framework-res.apk

mkdir -p "$BUILD/assets/data/cores" "$BUILD/classes"

# 1. EmulatorJS frontend + núcleo mGBA desde npm (ambas variantes wasm)
if [ ! -f "$BUILD/assets/data/loader.js" ]; then
  tmp=$(mktemp -d)
  (cd "$tmp" && npm pack "@emulatorjs/emulatorjs@$EJS_VER" "@emulatorjs/core-mgba@$EJS_VER" >/dev/null \
    && for f in *.tgz; do mkdir "${f%.tgz}" && tar xzf "$f" -C "${f%.tgz}"; done)
  cp -r "$tmp"/emulatorjs-emulatorjs-*/package/data/* "$BUILD/assets/data/"
  cp "$tmp"/emulatorjs-core-mgba-*/package/mgba-wasm.data \
     "$tmp"/emulatorjs-core-mgba-*/package/mgba-legacy-wasm.data "$BUILD/assets/data/cores/"
  cp -r "$tmp"/emulatorjs-core-mgba-*/package/reports "$BUILD/assets/data/cores/reports"
  rm -rf "$tmp"
fi

# 2. Assets de la app
cp "$HERE/assets/index.html" "$BUILD/assets/"
cp "$ROM" "$BUILD/assets/ffta.gba"

# 3. classpath del framework para compilar
[ -f "$BUILD/android-all.jar" ] || curl -sSL -o "$BUILD/android-all.jar" "$ANDROID_ALL_URL"

# 4. Compilar, dexear, empaquetar
javac --release 8 -nowarn -cp "$BUILD/android-all.jar" -d "$BUILD/classes" \
  "$HERE/src/com/mj/ffta/MainActivity.java"
dalvik-exchange --dex --output="$BUILD/classes.dex" "$BUILD/classes"
(cd "$HERE" && aapt package -f -M AndroidManifest.xml -S res -A "$BUILD/assets" \
  -I "$FRAMEWORK_RES" -F "$BUILD/app.unsigned.apk")
(cd "$BUILD" && zip -q app.unsigned.apk classes.dex)
zipalign -f 4 "$BUILD/app.unsigned.apk" "$BUILD/app.aligned.apk"

# 5. Firmar (keystore personal autogenerado, se reutiliza entre builds)
KS="$HERE/personal.keystore"
[ -f "$KS" ] || keytool -genkeypair -keystore "$KS" -storepass android -keypass android \
  -alias ffta -dname "CN=FFTA Personal" -keyalg RSA -keysize 2048 -validity 10000
apksigner sign --ks "$KS" --ks-pass pass:android --key-pass pass:android \
  --out "$OUT" "$BUILD/app.aligned.apk"

echo "APK lista: $OUT"
