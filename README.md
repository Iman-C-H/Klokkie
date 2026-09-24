# Klokkie – PWA

## Lokal testen
    python3 -m http.server 8080
Dann http://localhost:8080 öffnen. Chrome DevTools → Application → Manifest / Service Workers,
Lighthouse → PWA.

Auf dem Handy vor dem Deployment testen (PWAs brauchen HTTPS):
    npx localtunnel --port 8080     # oder: cloudflared tunnel --url http://localhost:8080

## Sprachdateien (offline-fähige Stimme)
Klokkie spielt eigene MP3s ab, wenn `audio/index.json` existiert, sonst die Browserstimme.
Es gibt 726 Dateien: 720 Uhrzeiten (tijd/HH-MM.mp3) + 6 Satzbausteine (zin/*.mp3).
Beispiel: "Het is" + "Kwart over drie." werden nahtlos hintereinander abgespielt.

### Variante A – automatisch mit Piper (kostenlos, offline, ca. 5–10 Min.)
    docker build -t klokkie-tts tools/tts
    docker run --rm -v "$PWD/audio:/work/audio" klokkie-tts

Optionen:
    -e LENGTH_SCALE=1.25     # langsamer sprechen (Standard 1.15)
    -e FORCE=1               # alle Dateien neu erzeugen
    -e SPEAKER=0             # Sprecher wählen bei Mehrsprecher-Stimmen
    docker build --build-arg VOICE=nl/nl_BE/rdh/medium/nl_BE-rdh-medium -t klokkie-tts tools/tts
Hörproben der Stimmen: https://rhasspy.github.io/piper-samples/
(nl_NL = Niederlande, nl_BE = Flämisch. Lizenz im MODEL_CARD der Stimme prüfen.)

### Variante B – echte Stimme / anderer TTS-Dienst
`tools/tts/phrases.tsv` enthält alle Dateinamen + Texte. Einfach MP3s mit genau diesen Namen
in `audio/` legen (z. B. von einer Lehrkraft eingesprochen) und danach index.json erzeugen:
    docker run --rm -v "$PWD/audio:/work/audio" klokkie-tts   # erzeugt nur Fehlendes + index.json
Einzelne Dateien lassen sich so auch gezielt austauschen: Datei ersetzen, Befehl erneut ausführen.

Satzliste neu erzeugen (falls die Formulierungen geändert werden):
    cd tools/tts && python3 phrases.py

## Deployment
Statisch: Ordner (ohne tools/) auf Netlify / Cloudflare Pages / GitHub Pages hochladen.
Docker:
    docker build -t klokkie .
    docker run -d -p 8080:80 klokkie
TLS über einen Reverse-Proxy (Traefik/Caddy mit Let's Encrypt).

## Updates ausrollen
- App-Code geändert: in sw.js `VERSION` hochzählen.
- Audio geändert: nichts zu tun, index.json bekommt automatisch eine neue Version
  und die Geräte laden die Sprachdateien neu.

## Installieren
- Android / Chrome / Edge (Laptop): Knopf "📲 Installeren" oder Browser-Menü → "App installieren".
- iPhone / iPad (Safari): Teilen-Symbol → "Zum Home-Bildschirm".
  Hinweis: Ist der Stummschalter am iPhone aktiv, bleibt die App stumm.

## GitHub Pages (automatisch)
Jeder Push auf `main` startet `.github/workflows/deploy.yml`: Sprachdateien erzeugen (gecacht),
Seite zusammenstellen, auf GitHub Pages veröffentlichen.
Einmalig: Repo → Settings → Pages → Source: "GitHub Actions".
