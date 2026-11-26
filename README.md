# BASS CHAOS V2 PRO - Komplettes Repo

## Start lokal
```bash
pip install -r requirements.txt
python app.py
# Browser: http://localhost:5000
```

## Deploy auf Render
Repo pushen, Render liest `render.yaml` automatisch.
Start: `gunicorn app:app --bind 0.0.0.0:$PORT`

## Was ist drin?
- Frontend: `index.html` (alles in einer Datei, Web Audio API, kein Build nötig)
- Backend: `app.py` (Flask) - dient Frontend aus + Proxy für Track-Suche
- Track-APIs (alle gratis, kein Key nötig, ausser FMA-Key optional):
  - `GET /api/search?q=techno&sources=deezer,itunes,archive,fma`
  - Deezer: 30s Previews, Cover, Dauer
  - iTunes: 30s Previews, Cover
  - Internet Archive: echte CC / Public Domain Full-Tracks (MP3)
  - FMA: Such-Link (FMA-API braucht eigenen API-Key)
  - `GET /api/archive-file/<identifier>` - findet echte MP3-Datei zu Archive-Item
  - `GET /api/audio?url=...` - Audio-Proxy (nur Deezer/Apple/archive.org, Range-Support) damit Decks in Master-REC + Visualizer laufen
  - `GET /health`

## Features Frontend
Sirenen, Bass-Arten, Deep Bass, Beats, Melodien, FX, Voice/Rufe (SpeechSynthesis),
Spass-Buttons, Einstellungen + Presets, 2 Turntables (Deck A/B, Crossfader, Pitch, Scratch),
Drum Machine (16-Step, 8 Spuren), Melodie-Studio (Klavier, Querfloete, Synth, Orgel, Gitarre, Violine, Sax, Marimba),
Eigene Voices aufnehmen (MediaRecorder, Handy-Mikro), Master-Aufnahme (MediaStreamDestination),
Pro DJ Top 10, Track-Suche -> in Deck A/B laden, Favoriten (localStorage), Android-optimiert.

## Recht
Deezer/iTunes = nur 30s Previews. Archive/FMA/Jamendo = CC / Public Domain, Lizenz je Track prüfen.
Keine Chart-Full-Tracks ohne Lizenz.
