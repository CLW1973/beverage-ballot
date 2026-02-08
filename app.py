import streamlit as st
import requests
import time
import json
import random

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- CLOUDINARY SYNC ENGINE ---
def save_game_state(data):
    try:
        url = f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/raw/upload"
        payload = {
            "upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET'],
            "public_id": "bb_game_state_v99", # New ID to start fresh
            "resource_type": "raw"
        }
        # We don't use 'overwrite' here to avoid the 400 error we saw earlier
        files = {"file": json.dumps(data)}
        r = requests.post(url, data=payload, files=files, timeout=10)
        return r.status_code == 200
    except:
        return False

def load_game_state():
    try:
        # We use a random number to FORCE the phone to get the newest file
        cb = random.randint(1, 999999)
        url = f"https://res.cloudinary.com/{st.secrets['CLOUDINARY_CLOUD_NAME']}/raw/upload/bb_game_state_v99.json?cb={cb}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {"Savarese": 0, "Willis": 0, "Active": "No", "H1": 0, "H2": 0, "Host": "", "Loc": "", "URL": ""}

# --- SESSION & TEAM FIX ---
if 'my_team' not in st.session_state:
    st.session_state.my_team = None

if st.session_state.my_team is None:
    st.title("🍹 Welcome to Beverage Ballot")
    st.subheader("Select your team to enter:")
    if st.button("I am Team Savarese"):
        st.session_state.my_team = "Team Savarese"
        st.rerun()
    if st.button("I am Team Willis"):
        st.session_state.my_team = "Team Willis"
        st.rerun()
    st.stop()

# Load Data
data = load_game_state()

# --- HEADER & REFRESH ---
st.title("🍹 Beverage Ballot")
st.caption(f"Logged in as: **{st.session_state.my_team}**")

if st.button("🔄 REFRESH / SYNC GAME", type="primary", use_container_width=True):
    st.rerun()

# Scoreboard
c1, c2 = st.columns(2)
c1.metric("Team Savarese", f"{data.get('Savarese', 0)} pts")
c2.metric("Team Willis", f"{data.get('Willis', 0)} pts")
st.divider()

sav_names = ["Ralph", "Trisha"]
wil_names = ["Charles", "Barbara"]

# --- ROUND LOGIC ---
if str(data.get('Active')) != "Yes":
    st.header("📢 Start a Round")
    
    # Only the team whose turn it is can see the inputs
    if st.session_state.my_team == "Team Savarese":
        loc = st.text_input("Location Name")
        img = st.camera_input("Snap the Menu")
        
        col_a, col_b = st.columns(2)
        d1 = col_a.number_input(f"{sav_names[0]}'s #", value=0, step=1)
        d2 = col_b.number_input(f"{sav_names[1]}'s #", value=0, step=1)
        
        if st.button("🚀 SEND ROUND", use_container_width=True):
            with st.spinner("Uploading..."):
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
                    st.success("Round LIVE! Tell Team Willis to Refresh.")
                    time.sleep(1)
                    st.rerun()
    else:
        st.info("Waiting for Team Savarese to start the round...")
        st.write("Hit the big **Refresh** button at the top every 30 seconds.")

else:
    # --- GUESSING SCREEN ---
    guesser_team = "Team Willis" if data['Host'] == "Team Savarese" else "Team Savarese"
    host_names = sav_names if data['Host'] == "Team Savarese" else wil_names
    
    st.header(f"🎯 {guesser_team}: Guessing Time")
    st.info(f"📍 {data['Host']} is at {data['Loc']}")
    if data.get('URL'): st.image(data['URL'])
    
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
                
                # Update scores
                data[guesser_team] += swing
                data['Active'] = "No"
                if save_game_state(data):
                    st.success("Guesses Submitted!")
                    time.sleep(2)
                    st.rerun()
    else:
        st.warning(f"Waiting for {guesser_team} to finish guessing...")

# --- FOOTER TOOLS ---
st.divider()
if st.button("🚪 Logout / Switch Team"):
    st.session_state.my_team = None
    st.rerun()

if st.sidebar.button("🚨 Reset All Scores"):
    save_game_state({"Savarese": 0, "Willis": 0, "Active": "No", "H1": 0, "H2": 0, "Host": "", "Loc": "", "URL": ""})
    st.rerun()
