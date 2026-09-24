#!/usr/bin/env bash
# Erzeugt alle Klokkie-Audiodateien mit Piper (offline) und ffmpeg.
# Variablen:  OUT (Zielordner)  MODEL (Piper-Stimme .onnx)  SPEAKER (bei Mehrsprecher-Stimmen)
#             LENGTH_SCALE (>1 = langsamer, Standard 1.15)  FORCE=1 (alles neu erzeugen)
set -euo pipefail
OUT=${OUT:-/work/audio}
TSV=${TSV:-/opt/klokkie/phrases.tsv}
MODEL=${MODEL:-/opt/voices/voice.onnx}
LENGTH_SCALE=${LENGTH_SCALE:-1.15}
FORCE=${FORCE:-0}

mkdir -p "$OUT/tijd" "$OUT/zin"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
total=$(grep -c . "$TSV"); n=0
files=()

while IFS=$'\t' read -r key text; do
  [ -z "$key" ] && continue
  n=$((n+1))
  files+=("$key.mp3")
  if [ -s "$OUT/$key.mp3" ] && [ "$FORCE" != 1 ]; then continue; fi
  printf '%s\n' "$text" | piper --model "$MODEL" ${SPEAKER:+--speaker "$SPEAKER"} \
      --length_scale "$LENGTH_SCALE" --output_file "$tmp/x.wav" >/dev/null 2>&1
  # Stille vorne/hinten abschneiden, Lautstärke angleichen, Mono-MP3
  ffmpeg -nostdin -loglevel error -y -i "$tmp/x.wav" \
    -af "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,loudnorm=I=-16:TP=-1.5" \
    -ac 1 -ar 44100 -b:a 64k "$OUT/$key.mp3"
  printf '\r%4d/%d  %-28s' "$n" "$total" "$key"
done < "$TSV"
echo

# index.json: Version = Prüfsumme über alle Dateien -> Geräte laden nur bei Änderungen neu
version=$(cd "$OUT" && cat "${files[@]}" | md5sum | cut -c1-10)
{
  printf '{"version":"%s","files":[' "$version"
  sep=""; for f in "${files[@]}"; do printf '%s"%s"' "$sep" "$f"; sep=","; done
  printf ']}\n'
} > "$OUT/index.json"
echo "Fertig: ${#files[@]} Dateien, Version $version -> $OUT"
