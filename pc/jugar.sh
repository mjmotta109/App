#!/bin/sh
# Lanzador Linux/macOS
cd "$(dirname "$0")"
if [ "$(uname)" = "Darwin" ]; then
  (python3 -m http.server 8641 --directory assets --bind 127.0.0.1 >/dev/null 2>&1 &)
else
  chmod +x ./server-linux 2>/dev/null
  (./server-linux 8641 &)
fi
sleep 1
xdg-open http://127.0.0.1:8641/ 2>/dev/null || open http://127.0.0.1:8641/
