
import streamlit as st
import pickle
import pandas as pd
import emoji
from collections import Counter
from google_auth_oauthlib.flow import Flow
import googleapiclient.discovery
st.set_page_config(page_title="moodmix 🎧", page_icon="🎧", layout="centered")


# OAuth Setup
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

def get_flow():
    client_config = {
        "web": {
            "client_id": st.secrets["google_oauth"]["client_id"],
            "client_secret": st.secrets["google_oauth"]["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [st.secrets["google_oauth"]["redirect_uri"]]
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=st.secrets["google_oauth"]["redirect_uri"]
    )
    return flow

# Check if we're returning from Google's login
query_params = st.query_params

if "code" in query_params and "credentials" not in st.session_state:
    flow = get_flow()
    flow.fetch_token(code=query_params["code"])
    st.session_state["credentials"] = flow.credentials
    st.query_params.clear()
    st.rerun()

# Login button
st.markdown("---")
if "credentials" not in st.session_state:
    flow = get_flow()
    auth_url, _ = flow.authorization_url(prompt='consent')
    st.markdown(f"[🔗 Connect YouTube Account]({auth_url})")
else:
    st.success("✅ YouTube Connected!")


# ---------- STYLING ----------
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(180deg, #0a0a0a 0%, #1a0b2e 100%);
        color: white;
    }
    .big-title {
        font-size: 42px;
        font-weight: 900;
        background: linear-gradient(90deg, #1DB954, #00d4ff, #ff00e5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .subtitle {
        color: #a0a0a0;
        font-size: 15px;
        margin-bottom: 25px;
    }
    .song-card {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(10px);
        padding: 18px;
        border-radius: 16px;
        margin-bottom: 14px;
        border: 1px solid rgba(255,255,255,0.1);
        transition: 0.3s;
    }
    .song-title {
        font-size: 19px;
        font-weight: 800;
        color: white;
    }
    .song-artist {
        font-size: 14px;
        color: #b3b3b3;
        margin-top: 2px;
    }
    .song-meta {
        font-size: 12px;
        color: #1DB954;
        margin-top: 6px;
        font-weight: 600;
    }
    .mood-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        background: linear-gradient(90deg, #1DB954, #00d4ff);
        color: black;
        font-weight: 700;
        font-size: 13px;
        margin-top: 10px;
    }
    div.stButton > button {
        background: linear-gradient(90deg, #1DB954, #00d4ff);
        color: black;
        font-weight: 800;
        border-radius: 30px;
        border: none;
        padding: 12px 0px;
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- LOAD DATA ----------
df = pickle.load(open('songs.pkl', 'rb'))

# ---------- HEADER ----------
st.markdown('<div class="big-title">moodmix 🎧</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">no cap, this actually gets your vibe fr fr</div>', unsafe_allow_html=True)

# ---------- MODE SELECTOR ----------
mode = st.radio("pick ur vibe check method 👇", ["🎭 Mood Select", "✨ Emoji Vibes"], horizontal=True)

final_mood = None

# ---------- MODE 1: DROPDOWN ----------
if mode == "🎭 Mood Select":
    moods = ['Happy/Hype', 'Chill/Content', 'Neutral/Focused', 'Angry/Intense', 'Sad/Melancholic']
    mood_emojis = {
        'Happy/Hype': '🔥',
        'Chill/Content': '😌',
        'Neutral/Focused': '🎯',
        'Angry/Intense': '⚡',
        'Sad/Melancholic': '🌧️'
    }
    selected_mood = st.selectbox("how u feeling rn?", moods, format_func=lambda x: f"{mood_emojis[x]} {x}")
    final_mood = selected_mood

# ---------- MODE 2: EMOJI PICKER ----------
else:
    st.write("drop ur emoji combo, we'll figure out the vibe 👇")
    emoji_input = st.text_input("type ur emojis here", placeholder="🔥😤💀 or 😢🌧️ or whatever ur feeling")
    
    if emoji_input:
        def emoji_to_mood(text):
            demojized = emoji.demojize(text)
            happy_words = ['smiling', 'joy', 'laugh', 'sun', 'star', 'heart', 'fire', 'party', 'grin']
            sad_words = ['crying', 'sad', 'rain', 'broken', 'tear', 'down', 'pensive']
            energy_words = ['fire', 'lightning', 'muscle', 'runner', 'dancer', 'party', 'skull']
            calm_words = ['sleep', 'moon', 'relax', 'leaf', 'zzz']
            
            valence = sum(1 for w in happy_words if w in demojized) - sum(1 for w in sad_words if w in demojized)
            energy = sum(1 for w in energy_words if w in demojized) - sum(1 for w in calm_words if w in demojized)
            
            if valence >= 1 and energy >= 1:
                return 'Happy/Hype'
            elif valence >= 1 and energy < 1:
                return 'Chill/Content'
            elif valence < 0 and energy >= 1:
                return 'Angry/Intense'
            elif valence < 0 and energy < 0:
                return 'Sad/Melancholic'
            else:
                return 'Neutral/Focused'
        
        final_mood = emoji_to_mood(emoji_input)
        st.markdown(f'<div class="mood-badge">detected: {final_mood} ✨</div>', unsafe_allow_html=True)

# ---------- GENRE FILTER ----------
genres = ['All'] + sorted(df['Genre'].unique().tolist())
selected_genre = st.selectbox("filter by genre (optional)", genres)

n_songs = st.slider("how many bangers u want?", 5, 20, 10)

# ---------- RECOMMEND BUTTON ----------
if st.button("🎶 run it back", use_container_width=True):
    if final_mood:
        filtered = df[df['mood'] == final_mood]
        
        if selected_genre != 'All':
            filtered = filtered[filtered['Genre'] == selected_genre]
        
        top_songs = filtered.sort_values(by='Popularity', ascending=False).head(n_songs)
        
        if len(top_songs) == 0:
            st.warning("no songs found bestie, try a different genre 💀")
        else:
            st.markdown("### your playlist rn 🎧")
            for _, row in top_songs.iterrows():
                st.markdown(f"""
                    <div class="song-card">
                        <div class="song-title">{row['Track']}</div>
                        <div class="song-artist">{row['Artist']}</div>
                        <div class="song-meta">{row['Genre']} • 🔥 {row['Popularity']}</div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("pick a mood or drop some emojis first fr")
