import streamlit as st
import requests
import time
import json

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- SYNC ENGINE (Using a Public JSON Bin for Zero-Latency Sync) ---
# This is a public, open bin specifically for your game. 
BIN_ID = "willis_savarese_game_v1"
SYNC_URL = f"https://kvstore.com/api/v1/items/{BIN_ID}"

def save_game_state(data):
    try:
        r = requests.post(SYNC_URL, json={"value": data}, timeout=10)
        return r.status_code in [200, 201]
    except:
        return False

def load_game_state():
    try:
        r = requests.get(SYNC_URL, timeout=5)
        if r.status_code == 200:
            return r.json()['value']
    except:
        pass
    return {"Savarese": 0, "Willis": 0, "Active": "No", "H1": 0, "H2": 0, "Host": "Team Savarese", "Loc": "", "URL": ""}

# --- APP STARTUP ---
if 'data' not in st.session_state:
    st.session_state.data = load_game_state()

data = st.session_state.data

# --- TEAM IDENTITY ---
# This "Locks" the phone to a specific team
if 'my_team' not in st.session_state:
    st.sidebar.header("Who are you?")
    st.session_state.my_team = st.sidebar.radio("Select your team:", ["Team Savarese", "Team Willis"])

st.title("🍹 Beverage Ballot")
st.sidebar.info(f"Logged in as: **{st.session_state.my_team}**")

# --- GLOBAL SYNC ---
if st.button("🔄 REFRESH / SYNC GAME", type="primary", use_container_width=True):
    st.session_state.data = load_game_state()
    st.rerun()

# Scoreboard
c1, c2 = st.columns(2)
c1.metric("Team Savarese", f"{data.get('Savarese', 0)} pts")
c2.metric("Team Willis", f"{data.get('Willis', 0)} pts")
st.divider()

sav_names = ["Ralph", "Trisha"]
wil_names = ["Charles", "Barbara"]

# --- GAME LOGIC ---
if str(data.get('Active')) != "Yes":
    # SCREEN: START ROUND
    st.header("📢 Start a Round")
    
    # Check if it's your turn to host
    if st.session_state.my_team == "Team Savarese":
        st.write("Enter your order details below:")
        loc = st.text_input("Location Name")
        img = st.camera_input("Snap the Menu/Drinks")
        
        col_a, col_b = st.columns(2)
        d1 = col_a.number_input(f"{sav_names[0]}'s #", value=0, step=1)
        d2 = col_b.number_input(f"{sav_names[1]}'s #", value=0, step=1)
        
        if st.button("🚀 SEND ROUND", use_container_width=True):
            with st.spinner("Syncing..."):
                p_url = ""
                if img:
                    up_url = f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/image/upload"
                    r_img = requests.post(up_url, data={"upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET']}, files={"file": img})
                    p_url = r_img.json().get("secure_url", "")

                new_state = {
                    "Savarese": data.get('Savarese', 0), "Willis": data.get('Willis', 0),
                    "Active": "Yes", "Host": "Team Savarese", "H1": int(d1), "H2": int(d2),
                    "Loc": loc, "URL": p_url
                }
                if save_game_state(new_state):
                    st.session_state.data = new_state
                    st.rerun()
    else:
        st.warning("Waiting for Team Savarese to start the round...")
        st.info("Hit 'Refresh' if they have already sent it.")

else:
    # SCREEN: GUESSING
    guesser_team = "Team Willis" if data['Host'] == "Team Savarese" else "Team Savarese"
    host_names = sav_names if data['Host'] == "Team Savarese" else wil_names
    
    st.header(f"🎯 {guesser_team}: Guessing Time")
    st.info(f"📍 {data['Host']} is at {data['Loc']}")
    if data.get('URL'): st.image(data['URL'])
    
    # --- LOCK LOGIC ---
    if st.session_state.my_team == guesser_team:
        with st.form("guess_form"):
            st.write("Enter whole numbers for guesses:")
            c1, c2 = st.columns(2)
            ga1 = c1.number_input(f"Guess A {host_names[0]}", value=0, step=1)
            ga2 = c2.number_input(f"Guess A {host_names[1]}", value=0, step=1)
            c3, c4 = st.columns(2)
            gb1 = c3.number_input(f"Guess B {host_names[0]}", value=0, step=1)
            gb2 = c4.number_input(f"Guess B {host_names[1]}", value=0, step=1)
            
            if st.form_submit_button("✅ SUBMIT FINAL GUESSES", use_container_width=True):
                correct = sum([ga1==data['H1'], ga2==data['H2'], gb1==data['H1'], gb2==data['H2']])
                swing = correct - (4 - correct)
                latest = load_game_state()
                latest[guesser_team] = latest.get(guesser_team, 0) + swing
                latest['Active'] = "No"
                if save_game_state(latest):
                    st.session_state.data = latest
                    st.rerun()
    else:
        st.warning(f"Waiting for {guesser_team} to finish guessing...")
        st.info("You cannot enter guesses for your own round!")

if st.sidebar.button("🚨 Reset All Scores"):
    save_game_state({"Savarese": 0, "Willis": 0, "Active": "No", "H1": 0, "H2": 0, "Host": "Team Savarese", "Loc": "", "URL": ""})
    st.rerun()
