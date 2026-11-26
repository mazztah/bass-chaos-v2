
import os, json, urllib.request, urllib.parse
import requests
from flask import Flask, request, jsonify, send_from_directory, Response, abort
from flask_cors import CORS

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

def fetch_json(url, timeout=12):
    req = urllib.request.Request(url, headers={'User-Agent':'BassChaos-V2/1.0 (contact: dj@basschaos.local)'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8', 'ignore'))

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/health')
def health():
    return jsonify({"status":"ok","app":"Bass Chaos V2 PRO"})

@app.route('/api/search')
def api_search():
    """Aggregiert: ?q=techno&sources=deezer,itunes,archive,fma"""
    q = (request.args.get('q') or 'techno').strip()
    sources = (request.args.get('sources') or 'deezer,itunes,archive,fma').split(',')
    out = []
    errors = {}
    # Deezer - kein Key
    if 'deezer' in sources:
        try:
            d = fetch_json('https://api.deezer.com/search?q=' + urllib.parse.quote(q))
            for t in (d.get('data') or [])[:20]:
                out.append({"source":"DEEZER","title":t.get('title'),"artist":(t.get('artist') or {}).get('name'),"cover":(t.get('album') or {}).get('cover_medium'),"preview":t.get('preview'),"duration":t.get('duration'),"bpm":None,"license":"30s Preview","link":t.get('link')})
        except Exception as e:
            errors['deezer']=str(e)
    # iTunes - kein Key
    if 'itunes' in sources:
        try:
            d = fetch_json('https://itunes.apple.com/search?term='+urllib.parse.quote(q)+'&media=music&limit=20')
            for t in (d.get('results') or []):
                out.append({"source":"ITUNES","title":t.get('trackName'),"artist":t.get('artistName'),"cover":(t.get('artworkUrl100') or '').replace('100x100bb','600x600bb'),"preview":t.get('previewUrl'),"duration":round((t.get('trackTimeMillis') or 0)/1000),"bpm":None,"license":"30s Preview","link":t.get('trackViewUrl')})
        except Exception as e:
            errors['itunes']=str(e)
    # Internet Archive - kein Key, CC / Public Domain
    if 'archive' in sources:
        try:
            aq = f'mediatype:audio AND licenseurl:*creativecommons* AND ({q})'
            url = 'https://archive.org/advancedsearch.php?q='+urllib.parse.quote(aq)+'&fl[]=identifier&fl[]=title&fl[]=creator&rows=20&page=1&output=json'
            d = fetch_json(url)
            for doc in ((d.get('response') or {}).get('docs') or []):
                ident = doc.get('identifier')
                out.append({"source":"ARCHIVE","title":doc.get('title'),"artist":(', '.join(doc['creator']) if isinstance(doc.get('creator'),list) else doc.get('creator')),"cover":f'https://archive.org/services/img/{ident}',"preview":None,"duration":None,"bpm":None,"license":"CC / Public Domain - Lizenz prüfen","link":f'https://archive.org/details/{ident}',"identifier":ident})
        except Exception as e:
            errors['archive']=str(e)
    # Free Music Archive - Direkt-Suche (API braucht Key, deshalb Such-Link + kuratierte CC-Hinweise)
    if 'fma' in sources:
        out.append({"source":"FMA","title":f'FMA-Suche: {q} (in neuem Tab öffnen)',"artist":"Free Music Archive","cover":"","preview":"","duration":None,"bpm":None,"license":"CC - je Track prüfen","link":'https://freemusicarchive.org/search?query='+urllib.parse.quote(q),"is_search_link":True})
    return jsonify({"query":q,"results":out,"errors":errors,"count":len(out)})

@app.route('/api/archive-file/<identifier>')
def archive_file(identifier):
    """Findet die echte MP3-Datei zu einem Archive-Item."""
    try:
        meta = fetch_json(f'https://archive.org/metadata/{identifier}')
        files = meta.get('files') or []
        mp3s = [f for f in files if (f.get('name') or '').lower().endswith('.mp3')]
        if not mp3s:
            return jsonify({"error":"kein mp3 gefunden"}), 404
        # kleinste / erste Datei bevorzugen
        sized = sorted(mp3s, key=lambda x: int(x.get('size') or 0))
        ok = [f for f in sized if 0 < int(f.get('size') or 0) <= 25*1024*1024]
        name = (ok[-1] if ok else sized[0])['name']
        return jsonify({"identifier":identifier,"file":name,"url":f'https://archive.org/download/{identifier}/{urllib.parse.quote(name)}'})
    except Exception as e:
        return jsonify({"error":str(e)}), 500

# ---------- Audio-Proxy: gleiche Domain, damit Web Audio (Master-REC, Visualizer) die Decks hört ----------
ALLOWED_SUFFIXES = ('dzcdn.net', 'deezer.com', 'mzstatic.com', 'apple.com', 'archive.org')

def host_allowed(url):
    p = urllib.parse.urlparse(url)
    h = (p.hostname or '').lower()
    return p.scheme == 'https' and any(h == s or h.endswith('.' + s) for s in ALLOWED_SUFFIXES)

@app.route('/api/audio')
def audio_proxy():
    url = request.args.get('url', '')
    if not host_allowed(url):
        abort(400, 'Host nicht erlaubt')
    headers = {'User-Agent': 'BassChaos-V2/1.0'}
    if request.headers.get('Range'):
        headers['Range'] = request.headers['Range']
    up = requests.get(url, headers=headers, stream=True, timeout=15)
    if not host_allowed(up.url):  # Redirect darf nirgends anders hin
        up.close()
        abort(400, 'Redirect nicht erlaubt')
    if up.status_code not in (200, 206):
        abort(502)
    out = {'Accept-Ranges': 'bytes', 'Cache-Control': 'public, max-age=86400'}
    for k in ('Content-Length', 'Content-Range'):
        if up.headers.get(k):
            out[k] = up.headers[k]
    return Response(up.iter_content(64 * 1024), status=up.status_code,
                    content_type=up.headers.get('Content-Type', 'audio/mpeg'), headers=out)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=bool(os.environ.get('DEBUG')))
