
import streamlit as st
import pickle
import pandas as pd
import emoji
from collections import Counter
from google_auth_oauthlib.flow import Flow
import googleapiclient.discovery
st.set_page_config(page_title="moodmix 🎧", page_icon="🎧", layout="centered")

import pickle
import pandas as pd
from difflib import get_close_matches

df = pickle.load(open('songs.pkl', 'rb'))

def find_song_mood(song_title, threshold=0.6):
    choices = df['Track'].tolist()
    matches = get_close_matches(song_title, choices, n=1, cutoff=threshold)
    if matches:
        matched_track = matches[0]
        result = df[df['Track'] == matched_track].iloc[0]
        return {'matched_title': result['Track'], 'artist': result['Artist'], 'mood': result['mood']}
    return None

def analyze_mood_history(song_list):
    results = []
    for song in song_list:
        match = find_song_mood(song)
        if match:
            results.append(match)
    if not results:
        return None, None
    mood_df = pd.DataFrame(results)
    mood_counts = mood_df['mood'].value_counts()
    return mood_df, mood_counts

# OAuth Setup
import requests

def exchange_code_for_token(code):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": st.secrets["google_oauth"]["client_id"],
        "client_secret": st.secrets["google_oauth"]["client_secret"],
        "redirect_uri": st.secrets["google_oauth"]["redirect_uri"],
        "grant_type": "authorization_code"
    }
    response = requests.post(token_url, data=data)
    return response.json()

def get_auth_url():
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": st.secrets["google_oauth"]["client_id"],
        "redirect_uri": st.secrets["google_oauth"]["redirect_uri"],
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/youtube.readonly",
        "access_type": "offline",
        "prompt": "consent"
    }
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{base_url}?{query_string}"

# Check if we're returning from Google's login
query_params = st.query_params

if "code" in query_params and "credentials" not in st.session_state:
    token_response = exchange_code_for_token(query_params["code"])
    if "access_token" in token_response:
        st.session_state["credentials"] = token_response
        st.query_params.clear()
        st.rerun()
    else:
        st.error(f"Login failed: {token_response}")

# Login button
st.markdown("---")
if "credentials" not in st.session_state:
    auth_url = get_auth_url()
    st.markdown(f"[🔗 Connect YouTube Account]({auth_url})")
else:
    st.success("✅ YouTube Connected!")

#new code here 
def get_liked_videos(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet",
        "myRating": "like",
        "maxResults": 50
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()

if "credentials" in st.session_state:
    st.markdown("---")
    if st.button("📊 Analyze My YouTube Mood History"):
        access_token = st.session_state["credentials"]["access_token"]
        liked_videos = get_liked_videos(access_token)
        
        if "items" in liked_videos:
            video_titles = [item["snippet"]["title"] for item in liked_videos["items"]]
            st.write(f"Found {len(video_titles)} liked videos")
            
            mood_df, mood_counts = analyze_mood_history(video_titles)
            
            if mood_df is not None:
                st.subheader("Your YouTube Mood Breakdown 📊")
                st.bar_chart(mood_counts)
                st.dataframe(mood_df)
            else:
                st.warning("Couldn't match any songs to our database")
        else:
            st.error(f"Couldn't fetch videos: {liked_videos}")

# ---------- STYLING ----------
st.markdown("""
    <style>
    .stApp {
        background-color: #0a0a0a;
        color: #ffffff;
        font-family: -apple-system, "Helvetica Neue", sans-serif;
    }
    
    .hero-section {
        background: linear-gradient(180deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.9) 100%), 
                    linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 60px 24px 40px 24px;
        border-radius: 0px;
        margin: -16px -16px 24px -16px;
    }
    
    .hero-label {
        display: inline-block;
        background: #000000;
        padding: 6px 14px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
    }
    
    .hero-title {
        font-size: 36px;
        font-weight: 800;
        color: #ffffff;
        line-height: 1.1;
        letter-spacing: -0.5px;
    }
    
    .section-label {
        font-size: 12px;
        font-weight: 700;
        color: #6a6a6a;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin: 32px 0 16px 0;
    }
    
    .genre-pill {
        display: inline-block;
        background: transparent;
        border: 1px solid #333333;
        padding: 8px 18px;
        border-radius: 500px;
        font-size: 13px;
        font-weight: 600;
        color: #ffffff;
        margin: 4px 6px 4px 0;
    }
    
    .list-row {
        display: flex;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #1a1a1a;
    }
    
    .list-title {
        font-size: 15px;
        font-weight: 700;
        color: #ffffff;
    }
    
    .list-subtitle {
        font-size: 13px;
        color: #7a7a7a;
        margin-top: 2px;
    }
    
    .list-score {
        color: #1ed760;
        font-size: 13px;
        font-weight: 700;
        margin-left: auto;
    }
    
    div.stButton > button {
        background: #ffffff;
        color: #000000;
        font-weight: 700;
        border-radius: 500px;
        border: none;
        padding: 14px 0px;
        font-size: 14px;
        width: 100%;
        text-transform: none;
    }
    
    div.stButton > button:hover {
        background: #e0e0e0;
    }
    
    .stSelectbox > div > div {
        background-color: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 6px;
    }
    </style>
""", unsafe_allow_html=True)

if "credentials" not in st.session_state:
    auth_url = get_auth_url()
    st.markdown(f"""
        <a href="{auth_url}" style="text-decoration: none;">
            <div style="background: #ffffff; color: #000000; font-weight: 700; 
                        border-radius: 500px; padding: 14px 32px; text-align: center;
                        display: inline-block; font-size: 14px;">
                Connect YouTube Account
            </div>
        </a>
    """, unsafe_allow_html=True)
else:
    st.success("✅ YouTube Connected!")
    
# Hero section
st.markdown("""
    <div class="hero-section">
        <div class="hero-label">MOOD ENGINE</div>
        <div class="hero-title">moodmix</div>
    </div>
""", unsafe_allow_html=True)


# ---------- LOAD DATA ----------
df = pickle.load(open('songs.pkl', 'rb'))

#new code 
from difflib import get_close_matches

def find_song_mood(song_title, threshold=0.6):
    choices = df['Track'].tolist()
    matches = get_close_matches(song_title, choices, n=1, cutoff=threshold)
    
    if matches:
        matched_track = matches[0]
        result = df[df['Track'] == matched_track].iloc[0]
        return {
            'matched_title': result['Track'],
            'artist': result['Artist'],
            'mood': result['mood']
        }
    return None

def analyze_mood_history(song_list):
    results = []
    for song in song_list:
        match = find_song_mood(song)
        if match:
            results.append(match)
    
    if not results:
        return None, None
    
    mood_df = pd.DataFrame(results)
    mood_counts = mood_df['mood'].value_counts()
    
    return mood_df, mood_counts

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
        <div class="list-row">
            <div style="flex: 1;">
                <div class="list-title">{row['Track']}</div>
                <div class="list-subtitle">{row['Artist']} · {row['Genre']}</div>
            </div>
            <div class="list-score">🔥 {row['Popularity']}</div>
        </div>
    """, unsafe_allow_html=True)
    else:
        st.warning("pick a mood or drop some emojis first fr")
