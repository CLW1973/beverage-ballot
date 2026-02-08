import streamlit as st
import requests
import time
import json
import random

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- CORE SETTINGS ---
# Using a brand new ID to bypass all previous errors/cache
FILE_ID = "game_brain_v100"

def save_game_state(data):
    try:
        url = f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/raw/upload"
        payload = {
            "upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET'],
            "public_id": FILE_ID,
            "resource_type": "raw",
            "overwrite": "true",
            "invalidate": "true" 
        }
        # Prepare the file
        files = {"file": (f"{FILE_ID}.json", json.dumps(data))}
        r = requests.post(url, data=payload, files=files, timeout=10)
        
        if r.status_code == 200:
            return True
        else:
            st.error(f"Cloudinary Rejected Save (Code {r.status_code}). Check if preset is 'Unsigned'.")
            return False
    except Exception as e:
        st.error(f"Technical Error: {e}")
        return False

def load_game_state():
    try:
        cb = int(time.time())
        url = f"https://res.cloudinary.com/{st.secrets['CLOUDINARY_CLOUD_NAME']}/raw/upload/{FILE_ID}.json?cb={cb}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    # Default state if no file exists yet
    return {"Savarese": 0, "Willis": 0, "Active": "No", "H1": 0, "H2": 0, "Host": "Team Savarese", "Loc": "", "URL": ""}

# Sync session state
if 'data' not in st.session_state:
    st.session_state.data = load_game_state()

data = st.session_state.data

st.title("🍹 Beverage Ballot")

# --- REFRESH BUTTON ---
if st.button("🔄 REFRESH / SYNC", type="primary", use_container_width=True):
    st.session_state.data = load_game_state()
    st.rerun()

# --- SCOREBOARD ---
c1, c2 = st.columns(2)
c1.metric("Team Savarese", f"{data.get('Savarese', 0)} pts")
c2.metric("Team Willis", f"{data.get('Willis', 0)} pts")
st.divider()

sav_names = ["Ralph", "Trisha"]
wil_names = ["Charles", "Barbara"]

# --- APP NAVIGATION ---
if str(data.get('Active')) != "Yes":
    # SCREEN: START ROUND
    st.header("📢 Start a Round")
    host_choice = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    loc = st.text_input("Location Name")
    img = st.camera_input("Snap the Menu/Drinks")
    
    p_names = sav_names if host_choice == "Team Savarese" else wil_names
    col_a, col_b = st.columns(2)
    d1 = col_a.number_input(f"{p_names[0]}'s Drink #", value=0, step=1)
    d2 = col_b.number_input(f"{p_names[1]}'s Drink #", value=0, step=1)
    
    if st.button("🚀 SEND ROUND", use_container_width=True):
        if d1 == 0 and d2 == 0:
            st.warning("Enter drink numbers before sending!")
        else:
            with st.spinner("Pushing to Cloud..."):
                p_url = ""
                if img:
                    up_url = f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/image/upload"
                    r_img = requests.post(up_url, data={"upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET']}, files={"file": img})
                    p_url = r_img.json().get("secure_url", "")

                new_state = {
                    "Savarese": data.get('Savarese', 0),
                    "Willis": data.get('Willis', 0),
                    "Active": "Yes",
                    "Host": host_choice,
                    "H1": int(d1), "H2": int(d2),
                    "Loc": loc, "URL": p_url
                }
                
                if save_game_state(new_state):
                    st.session_state.data = new_state
                    st.rerun()

else:
    # SCREEN: GUESSING
    guesser = "Team Willis" if data['Host'] == "Team Savarese" else "Team Savarese"
    h_names = sav_names if data['Host'] == "Team Savarese" else wil_names
    
    st.header(f"🎯 {guesser}: Your Turn!")
    st.info(f"📍 {data['Host']} is at {data['Loc']}")
    
    if data.get('URL'):
        st.image(f"{data['URL']}?cb={int(time.time())}")
    
    with st.form("guess_form"):
        st.write("Enter whole numbers for guesses:")
        c1, c2 = st.columns(2)
        ga1 = c1.number_input(f"Guess A {h_names[0]}", value=0, step=1)
        ga2 = c2.number_input(f"Guess A {h_names[1]}", value=0, step=1)
        
        c3, c4 = st.columns(2)
        gb1 = c3.number_input(f"Guess B {h_names[0]}", value=0, step=1)
        gb2 = c4.number_input(f"Guess B {h_names[1]}", value=0, step=1)
        
        if st.form_submit_button("✅ SUBMIT FINAL GUESSES", use_container_width=True):
            correct = sum([ga1 == data['H1'], ga2 == data['H2'], gb1 == data['H1'], gb2 == data['H2']])
            swing = correct - (4 - correct)
            
            # Pull fresh data to avoid overwriting scores
            latest = load_game_state()
            latest[guesser] = latest.get(guesser, 0) + swing
            latest['Active'] = "No"
            latest['Loc'] = ""
            latest['URL'] = ""
            
            if save_game_state(latest):
                st.session_state.data = latest
                if swing > 0: st.balloons()
                st.rerun()

# --- SIDEBAR TOOLS ---
with st.sidebar:
    st.divider()
    if st.button("🚨 Reset Scores to 0"):
        reset_state = {"Savarese": 0, "Willis": 0, "Active": "No", "H1": 0, "H2": 0, "Host": "Team Savarese", "Loc": "", "URL": ""}
        save_game_state(reset_state)
        st.session_state.data = reset_state
        st.rerun()
