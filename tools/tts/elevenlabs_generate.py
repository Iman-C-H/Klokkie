#!/usr/bin/env python3
"""Erzeugt die Klokkie-Sprachdateien mit ElevenLabs.

Umgebungsvariablen:
  ELEVENLABS_API_KEY   API-Schlüssel (Pflicht)
  ELEVENLABS_VOICE_ID  ID der Stimme aus "My Voices" (Pflicht)
  ELEVENLABS_MODEL     Standard eleven_multilingual_v2
  ELEVENLABS_LANGUAGE  optional, z. B. nl (nur bei Modellen, die das unterstützen)
  PITCH                optional, z. B. 1.06 = Stimme etwas höher/"süßer" (1.0 = unverändert)
  OUT                  Zielordner, Standard voice
  FORCE=1              Ordner leeren und alles neu erzeugen

Bereits vorhandene Dateien werden übersprungen. Ist das Monatskontingent aufgebraucht,
stoppt das Skript sauber; beim nächsten Start geht es an derselben Stelle weiter.
index.json wird erst geschrieben, wenn ALLE Dateien vorhanden sind.
"""
import hashlib, json, os, shutil, subprocess, sys, tempfile, time
import urllib.error, urllib.request

KEY = os.environ.get('ELEVENLABS_API_KEY', '').strip()
VOICE = os.environ.get('ELEVENLABS_VOICE_ID', '').strip()
MODEL = os.environ.get('ELEVENLABS_MODEL') or 'eleven_multilingual_v2'
LANG = os.environ.get('ELEVENLABS_LANGUAGE', '').strip()
PITCH = float(os.environ.get('PITCH') or 1.0)
OUT = os.environ.get('OUT', 'voice')
TSV = os.environ.get('TSV', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phrases.tsv'))
FORCE = os.environ.get('FORCE') == '1'
FFMPEG = shutil.which('ffmpeg')


class QuotaExceeded(Exception):
    pass


def synth(text):
    url = f'https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_44100_128'
    body = {'text': text, 'model_id': MODEL,
            'voice_settings': {'stability': 0.55, 'similarity_boost': 0.75}}
    if LANG:
        body['language_code'] = LANG
    for attempt in range(8):
        req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), method='POST', headers={
            'xi-api-key': KEY, 'Content-Type': 'application/json', 'Accept': 'audio/mpeg'})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            msg = e.read()[:400].decode('utf-8', 'replace')
            if 'quota' in msg.lower() or 'credits' in msg.lower():
                raise QuotaExceeded(msg)
            if e.code == 429 or e.code >= 500:
                wait = min(60, 2 ** attempt)
                print(f'\n  ElevenLabs {e.code}, warte {wait}s …', flush=True)
                time.sleep(wait)
                continue
            sys.exit(f'ElevenLabs-Fehler {e.code}: {msg}\n(API-Schlüssel und Voice-ID prüfen)')
        except urllib.error.URLError as e:
            print(f'\n  Netzwerkfehler ({e.reason}), neuer Versuch …', flush=True)
            time.sleep(min(60, 2 ** attempt))
    sys.exit('ElevenLabs ist nicht erreichbar, Abbruch.')


def postprocess(src, dst):
    """Stille abschneiden, optional Tonhöhe anheben, Lautstärke angleichen."""
    filters = ['silenceremove=start_periods=1:start_threshold=-50dB', 'areverse',
               'silenceremove=start_periods=1:start_threshold=-50dB', 'areverse']
    if abs(PITCH - 1.0) > 0.001:
        filters += [f'asetrate=44100*{PITCH}', 'aresample=44100', f'atempo={1 / PITCH:.5f}']
    filters.append('loudnorm=I=-16:TP=-1.5')
    subprocess.run([FFMPEG, '-nostdin', '-loglevel', 'error', '-y', '-i', src,
                    '-af', ','.join(filters), '-ac', '1', '-ar', '44100', '-b:a', '64k', dst], check=True)


def main():
    if not KEY or not VOICE:
        sys.exit('ELEVENLABS_API_KEY und ELEVENLABS_VOICE_ID müssen gesetzt sein.')
    if FORCE and os.path.isdir(OUT):
        shutil.rmtree(OUT)
    rows = [l.rstrip('\n').split('\t', 1) for l in open(TSV, encoding='utf-8') if l.strip()]
    for d in ('tijd', 'zin'):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
    index_path = os.path.join(OUT, 'index.json')
    todo = [(k, t) for k, t in rows
            if not (os.path.exists(os.path.join(OUT, k + '.mp3')) and os.path.getsize(os.path.join(OUT, k + '.mp3')) > 0)]
    chars = sum(len(t) for _, t in todo)
    print(f'Stimme {VOICE}, Modell {MODEL}, Pitch {PITCH}: {len(rows) - len(todo)} vorhanden, '
          f'{len(todo)} fehlen (~{chars} Zeichen)')
    done = 0
    with tempfile.TemporaryDirectory() as tmp:
        try:
            for key, text in todo:
                data = synth(text)
                dst = os.path.join(OUT, key + '.mp3')
                if FFMPEG:
                    raw = os.path.join(tmp, 'raw.mp3')
                    open(raw, 'wb').write(data)
                    postprocess(raw, dst)
                else:
                    open(dst, 'wb').write(data)
                done += 1
                print(f'\r{done:4d}/{len(todo)}  {key:<28}', end='', flush=True)
        except QuotaExceeded as e:
            print(f'\n\nKontingent aufgebraucht ({done} neue Dateien gespeichert).')
            print('Nächsten Monat (oder nach einem Upgrade) den Workflow erneut starten – es geht hier weiter.')
            print(f'Antwort von ElevenLabs: {e}')
            if os.path.exists(index_path):
                os.remove(index_path)
            return
    print()
    files = [k + '.mp3' for k, _ in rows]
    h = hashlib.md5()
    for f in files:
        h.update(open(os.path.join(OUT, f), 'rb').read())
    index = {'version': h.hexdigest()[:10], 'credit': 'Stem gemaakt met ElevenLabs', 'files': files}
    json.dump(index, open(index_path, 'w'), separators=(',', ':'))
    print(f'Fertig: alle {len(files)} Dateien vorhanden, Version {index["version"]}')


if __name__ == '__main__':
    main()
