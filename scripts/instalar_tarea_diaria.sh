#!/bin/bash
# Programa en el Mac (launchd) una ejecución diaria de scripts/correr_nube.py a las 07:00.
# Si el Mac está dormido a esa hora, macOS la ejecuta al despertar. Si está apagado, se salta ese día.
#   Instalar:     bash scripts/instalar_tarea_diaria.sh
#   Desinstalar:  bash scripts/instalar_tarea_diaria.sh --quitar
set -e
ETIQUETA="cl.uv.ner-aps.nube"
PLIST="$HOME/Library/LaunchAgents/$ETIQUETA.plist"
PROYECTO="$(cd "$(dirname "$0")/.." && pwd)"

if [ "$1" == "--quitar" ]; then
  launchctl unload "$PLIST" 2>/dev/null || true
  rm -f "$PLIST"
  echo "Tarea diaria eliminada."
  exit 0
fi

mkdir -p "$HOME/Library/LaunchAgents" "$PROYECTO/results/logs"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$ETIQUETA</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PROYECTO/.venv/bin/python</string>
    <string>$PROYECTO/scripts/correr_nube.py</string>
  </array>
  <key>WorkingDirectory</key><string>$PROYECTO</string>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>7</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>$PROYECTO/results/logs/launchd_out.log</string>
  <key>StandardErrorPath</key><string>$PROYECTO/results/logs/launchd_err.log</string>
</dict>
</plist>
EOF
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "Listo: correr_nube.py se ejecutará todos los días a las 07:00."
echo "Registro: $PROYECTO/results/logs/correr_nube.log"
echo "Para probarla ahora mismo:  launchctl start $ETIQUETA"
