#!/usr/bin/env python3
"""Erzeugt phrases.tsv: alle Sätze, die Klokkie vorliest (Dateiname <TAB> Text).
Die Logik entspricht dutchTime() in index.html."""
NUM = ['nul','één','twee','drie','vier','vijf','zes','zeven','acht','negen',
       'tien','elf','twaalf','dertien','veertien']

def hour_name(h):
    h %= 12
    return NUM[12 if h == 0 else h]

def amount(n):
    if n in (5, 10): return NUM[n]
    return 'één minuut' if n == 1 else NUM[n] + ' minuten'

def dutch_time(h, m):
    cur, nxt = hour_name(h), hour_name(h + 1)
    if m == 0:  return f'{cur} uur'
    if m == 15: return f'kwart over {cur}'
    if m == 30: return f'half {nxt}'
    if m == 45: return f'kwart voor {nxt}'
    if m < 15:  return f'{amount(m)} over {cur}'
    if m < 30:  return f'{amount(30 - m)} voor half {nxt}'
    if m < 45:  return f'{amount(m - 30)} over half {nxt}'
    return f'{amount(60 - m)} voor {nxt}'

CLIPS = [
    ('zin/het-is', 'Het is'),
    ('zin/zet-de-klok-op', 'Zet de klok op'),
    ('zin/goed-zo', 'Goed zo!'),
    ('zin/bijna', 'Bijna!'),
    ('zin/jouw-klok-zegt', 'Jouw klok zegt'),
    ('zin/probeer-het-nog-eens', 'Probeer het nog eens.'),
]

if __name__ == '__main__':
    rows = list(CLIPS)
    for h in range(12):
        for m in range(60):
            text = dutch_time(h, m)
            rows.append((f'tijd/{(h or 12):02d}-{m:02d}', text[0].upper() + text[1:] + '.'))
    with open('phrases.tsv', 'w', encoding='utf-8') as f:
        for key, text in rows:
            f.write(f'{key}\t{text}\n')
    print(f'{len(rows)} Sätze geschrieben')
