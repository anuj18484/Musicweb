import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from jinja2 import DictLoader

app = Flask(__name__)
# Secure config & fallback to SQLite for easy single-file execution
app.config['SECRET_KEY'] = 'super-secret-luxury-key-1337'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///music.db').replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    songs = db.relationship('Song', backref='artist', lazy=True)

class Song(db.Model):
    __tablename__ = 'songs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    album_name = db.Column(db.String(100), nullable=False)
    cover_url = db.Column(db.String(500), nullable=False)
    audio_url = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    is_trending = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    plays = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id, 'title': self.title, 'artist': self.artist.name if self.artist else "Unknown",
            'artist_id': self.artist_id, 'cover_url': self.cover_url, 'audio_url': self.audio_url, 'plays': self.plays
        }

# --- EMBEDDED FRONTEND (HTML/CSS/JS) ---
HTML_TEMPLATES = {
    'base.html': '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aura - Premium Audio</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --bg-dark: #09090b; --sidebar-bg: rgba(18, 18, 22, 0.45); --glass-bg: rgba(255, 255, 255, 0.03); --glass-border: rgba(255, 255, 255, 0.06); --primary-gradient: linear-gradient(135deg, #a855f7 0%, #6366f1 100%); --accent: #a855f7; --text-main: #f4f4f5; --text-muted: #a1a1aa; --player-height: 90px; --transition: all 0.3s ease; }
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Plus Jakarta Sans', sans-serif; -webkit-font-smoothing: antialiased; }
        body { background-color: var(--bg-dark); color: var(--text-main); overflow-x: hidden; min-height: 100vh; }
        #app-container { display: flex; min-height: 100vh; padding-bottom: var(--player-height); }
        aside { width: 260px; background: var(--sidebar-bg); backdrop-filter: blur(20px); border-right: 1px solid var(--glass-border); padding: 2rem 1.5rem; position: fixed; height: calc(100vh - var(--player-height)); z-index: 100; }
        .brand { font-size: 1.5rem; font-weight: 800; background: var(--primary-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 2.5rem; }
        nav ul { list-style: none; display: flex; flex-direction: column; gap: 0.5rem; }
        nav a { display: flex; align-items: center; gap: 1rem; padding: 0.8rem 1rem; color: var(--text-muted); text-decoration: none; font-weight: 500; border-radius: 12px; transition: var(--transition); }
        nav a:hover { color: var(--text-main); background: var(--glass-bg); border: 1px solid var(--glass-border); }
        main { flex: 1; margin-left: 260px; padding: 2rem 3rem; }
        .card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1.5rem; margin-bottom: 2.5rem; }
        .music-card { background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: 16px; padding: 1rem; cursor: pointer; position: relative; transition: var(--transition); }
        .music-card:hover { transform: translateY(-8px); background: rgba(255,255,255,0.06); }
        .music-card img { width: 100%; aspect-ratio: 1; object-fit: cover; border-radius: 12px; margin-bottom: 0.8rem; }
        #premium-player { position: fixed; bottom: 0; left: 0; width: 100vw; height: var(--player-height); background: rgba(10, 10, 12, 0.85); backdrop-filter: blur(30px); border-top: 1px solid var(--glass-border); display: grid; grid-template-columns: 1fr 2fr 1fr; align-items: center; padding: 0 2rem; z-index: 999; }
        .track-details { display: flex; align-items: center; gap: 1rem; }
        .track-details img { width: 55px; height: 55px; border-radius: 8px; object-fit: cover; }
        .control-buttons { display: flex; align-items: center; gap: 1.5rem; justify-content: center; }
        .btn-icon { background: none; border: none; color: var(--text-muted); font-size: 1.2rem; cursor: pointer; transition: var(--transition); }
        .btn-icon:hover { color: var(--text-main); }
        .play-master { width: 40px; height: 40px; background: var(--text-main); color: var(--bg-dark); border-radius: 50%; display: flex; justify-content: center; align-items: center; }
        .progress-timeline { display: flex; align-items: center; gap: 0.8rem; font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem; }
        .slider-bar { flex: 1; -webkit-appearance: none; height: 4px; border-radius: 2px; background: rgba(255,255,255,0.1); cursor: pointer; }
        .slider-bar::-webkit-slider-thumb { -webkit-appearance: none; width: 12px; height: 12px; border-radius: 50%; background: var(--accent); }
        .utility-controls { display: flex; justify-content: flex-end; align-items: center; gap: 1rem; }
        @media (max-width: 768px) { aside { position: fixed; bottom: var(--player-height); left: 0; width: 100%; height: 60px; flex-direction: row; padding: 0; border-top: 1px solid var(--glass-border); } main { margin-left: 0; padding: 1rem; padding-bottom: 100px; } .utility-controls, .progress-timeline { display: none; } #premium-player { grid-template-columns: 2fr 1fr; } }
    </style>
</head>
<body>
    <div id="app-container">
        <aside>
            <div class="brand">AURA</div>
            <nav>
                <ul>
                    <li><a href="/"><i class="fa-solid fa-house"></i> Home</a></li>
                    <li><a href="/search"><i class="fa-solid fa-magnifying-glass"></i> Search</a></li>
                </ul>
            </nav>
        </aside>
        <main>{% block content %}{% endblock %}</main>
    </div>

    <div id="premium-player">
        <div class="track-details">
            <img id="player-cover" src="https://images.unsplash.com/photo-1614613535308-eb5fbd3d2c17?w=150" alt="Cover">
            <div>
                <h4 id="player-title" style="font-size:0.95rem;">No Track</h4>
                <p id="player-artist" style="font-size:0.8rem; color:var(--text-muted);">Select a track</p>
            </div>
        </div>
        <div style="display:flex; flex-direction:column;">
            <div class="control-buttons">
                <button class="btn-icon play-master" id="master-play-btn" onclick="togglePlayState()"><i class="fa-solid fa-play"></i></button>
            </div>
            <div class="progress-timeline">
                <span id="time-current">0:00</span>
                <input type="range" class="slider-bar" id="track-slider" min="0" value="0" step="1" oninput="seekTrack(this.value)">
                <span id="time-duration">0:00</span>
            </div>
        </div>
        <div class="utility-controls">
            <i class="fa-solid fa-volume-high"></i>
            <input type="range" class="slider-bar" id="volume-slider" style="width: 100px;" min="0" max="1" step="0.01" value="0.8" oninput="setVolume(this.value)">
        </div>
    </div>
    <audio id="audio-engine" preload="auto"></audio>

    <script>
        const audio = document.getElementById('audio-engine');
        function playSongEngine(id, title, artist, cover, url) {
            document.getElementById('player-title').innerText = title;
            document.getElementById('player-artist').innerText = artist;
            document.getElementById('player-cover').src = cover;
            audio.src = url;
            audio.play();
            updatePlayBtn(true);
            fetch(`/api/play/${id}`, { method: 'POST' });
        }
        function updatePlayBtn(isPlaying) {
            document.getElementById('master-play-btn').innerHTML = isPlaying ? '<i class="fa-solid fa-pause"></i>' : '<i class="fa-solid fa-play">';
        }
        function togglePlayState() {
            if (!audio.src) return;
            audio.paused ? audio.play() : audio.pause();
            updatePlayBtn(!audio.paused);
        }
        audio.addEventListener('timeupdate', () => {
            const slider = document.getElementById('track-slider');
            if (!isNaN(audio.duration)) {
                slider.max = Math.floor(audio.duration);
                slider.value = Math.floor(audio.currentTime);
                document.getElementById('time-current').innerText = formatTime(audio.currentTime);
                document.getElementById('time-duration').innerText = formatTime(audio.duration);
            }
        });
        function seekTrack(val) { audio.currentTime = val; }
        function setVolume(val) { audio.volume = val; }
        function formatTime(secs) {
            const min = Math.floor(secs / 60); const sec = Math.floor(secs % 60);
            return `${min}:${sec < 10 ? '0' : ''}${sec}`;
        }
    </script>
</body>
</html>
    ''',
    
    'home.html': '''
{% extends 'base.html' %}
{% block content %}
<div style="background: linear-gradient(rgba(0,0,0,0.2), rgba(9,9,11,1)), url('https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=1200'); background-size: cover; background-position: center; height: 250px; border-radius: 24px; padding: 3rem; display: flex; flex-direction: column; justify-content: flex-end; margin-bottom: 2.5rem; border: 1px solid var(--glass-border);">
    <h1 style="font-size: 3rem; font-weight: 800; text-shadow: 0 4px 12px rgba(0,0,0,0.6);">Experience Pure Sound</h1>
</div>
<h3 style="margin-bottom: 1.2rem;">Trending Audios</h3>
<div class="card-grid">
    {% for song in songs %}
    <div class="music-card" onclick="playSongEngine({{ song.id }}, '{{ song.title }}', '{{ song.artist.name }}', '{{ song.cover_url }}', '{{ song.audio_url }}')">
        <img src="{{ song.cover_url }}" alt="Artwork">
        <h5 style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{{ song.title }}</h5>
        <p style="font-size: 0.8rem; color: var(--text-muted);">{{ song.artist.name }}</p>
    </div>
    {% endfor %}
</div>
{% endblock %}
    ''',
    
    'search.html': '''
{% extends 'base.html' %}
{% block content %}
<input type="text" id="search-input" oninput="searchSongs(this.value)" placeholder="Search tracks..." style="width: 100%; background: var(--glass-bg); border: 1px solid var(--glass-border); padding: 1.2rem; border-radius: 50px; color: white; font-size: 1.1rem; outline: none; margin-bottom: 2rem;">
<div class="card-grid" id="search-results"></div>
<script>
    function searchSongs(query) {
        if(query.length < 2) { document.getElementById('search-results').innerHTML = ''; return; }
        fetch(`/api/search?q=${query}`).then(res => res.json()).then(data => {
            let html = '';
            data.songs.forEach(s => {
                html += `<div class="music-card" onclick="playSongEngine(${s.id}, '${s.title}', '${s.artist}', '${s.cover_url}', '${s.audio_url}')"><img src="${s.cover_url}"><h5>${s.title}</h5><p style="font-size:0.8rem; color:var(--text-muted);">${s.artist}</p></div>`;
            });
            document.getElementById('search-results').innerHTML = html;
        });
    }
</script>
{% endblock %}
    '''
}

# Bind templates dictionary to Flask App using DictLoader
app.jinja_loader = DictLoader(HTML_TEMPLATES)

          # --- FLASK ROUTES ---
@app.route('/')
def home():
    songs = Song.query.all()
    return app.jinja_env.get_template('home.html').render(songs=songs)

@app.route('/search')
def search():
    return app.jinja_env.get_template('search.html').render()

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    songs = Song.query.filter(Song.title.ilike(f'%{query}%')).limit(10).all()
    return jsonify({'songs': [s.to_dict() for s in songs]})

@app.route('/api/play/<int:song_id>', methods=['POST'])
def track_play(song_id):
    song = Song.query.get(song_id)
    if song:
        song.plays += 1
        db.session.commit()
    return jsonify({'success': True})

# --- DATA SEEDING & SETUP ---
def seed_demo_data():
    if Artist.query.first() is None:
        a1 = Artist(name="Lofi Dreamer", image_url="https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400", bio="Atmospheric sounds.")
        a2 = Artist(name="Cyber Synth", image_url="https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400", bio="Retro beats.")
        db.session.add_all([a1, a2])
        db.session.commit()

        s1 = Song(title="Midnight Coffee", artist_id=a1.id, album_name="Cozy Room", 
                  cover_url="https://images.unsplash.com/photo-1445116572660-236099ec97a0?w=400", 
                  audio_url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", category="Chill")
        s2 = Song(title="Neon Skyline", artist_id=a2.id, album_name="Grid Runner", 
                  cover_url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400", 
                  audio_url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3", category="Energy")
        s3 = Song(title="Deep Workspace", artist_id=a1.id, album_name="Cozy Room", 
                  cover_url="https://images.unsplash.com/photo-1487180142328-054b783fc471?w=400", 
                  audio_url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3", category="Focus")
        
        db.session.add_all([s1, s2, s3])
        db.session.commit()

with app.app_context():
    db.create_all()
    seed_demo_data()

# --- APP EXECUTION ---
if __name__ == '__main__':
    # Run application
    app.run(debug=True, port=5000)
  
