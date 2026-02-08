import streamlit as st
import requests
import time
import json
import random

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- CLOUDINARY SYNC ---
def save_game_state(data):
    try:
        url = f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/raw/upload"
        json_data = json.dumps(data)
        payload = {
            "upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET'],
            "public_id": "willis_savarese_game_state",
            "resource_type": "raw",
            "overwrite": True
        }
        files = {"file": ("game_state.json", json_data)}
        r = requests.post(url, data=payload, files=files)
        return r.status_code == 200
    except:
        return False

def load_game_state():
    try:
        # The '?cb=' part forces the phone to get the NEWEST data, not the cached old data
        cb = random.randint(1, 999999)
        url = f"https://res.cloudinary.com/{st.secrets['CLOUDINARY_CLOUD_NAME']}/raw/upload/willis_savarese_game_state.json"
        r = requests.get(f"{url}?cb={cb}", timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {"Savarese": 0, "Willis": 0, "Active_Round": "No", "Hidden1": 0, "Hidden2": 0, "Host": "", "Location": "", "PhotoURL": ""}

def upload_image(image_file):
    try:
        url = f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/image/upload"
        files = {"file": image_file}
        payload = {"upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET']}
        r = requests.post(url, files=files, data=payload)
        return r.json().get("secure_url")
    except:
        return None

# Load state once per rerun
if 'game_data' not in st.session_state or st.sidebar.button("🔄 Force Global Sync"):
    st.session_state.game_data = load_game_state()

data = st.session_state.game_data

st.title("🍹 Beverage Ballot")

# Scoreboard
c1, c2 = st.columns(2)
c1.metric("Team Savarese", f"{data.get('Savarese', 0)} pts")
c2.metric("Team Willis", f"{data.get('Willis', 0)} pts")
st.divider()

sav_names = ["Ralph", "Trisha"]
wil_names = ["Charles", "Barbara"]

# --- ROUND LOGIC ---
if data.get('Active_Round') == "No":
    st.header("📢 Start a Round")
    h_team = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    loc = st.text_input("Where are you?")
    img = st.camera_input("Snap the Menu/Drinks")
    
    p_names = sav_names if h_team == "Team Savarese" else wil_names
    col_a, col_b = st.columns(2)
    d1 = col_a.number_input(f"{p_names[0]}'s Drink #", value=0, step=1)
    d2 = col_b.number_input(f"{p_names[1]}'s Drink #", value=0, step=1)
    
    if st.button("🚀 SEND ROUND", use_container_width=True):
        with st.spinner("Uploading New Data..."):
            p_url = upload_image(img) if img else ""
            new_round = {
                "Savarese": data.get('Savarese', 0),
                "Willis": data.get('Willis', 0),
                "Active_Round": "Yes",
                "Host": h_team,
                "Hidden1": int(d1),
                "Hidden2": int(d2),
                "Location": loc,
                "PhotoURL": p_url
            }
            if save_game_state(new_round):
                st.session_state.game_data = new_round
                st.success("Round LIVE!")
                time.sleep(1)
                st.rerun()

else:
    # --- GUESSING SCREEN ---
    guesser_team = "Team Willis" if data['Host'] == "Team Savarese" else "Team Savarese"
    host_names = sav_names if data['Host'] == "Team Savarese" else wil_names
    
    st.header(f"🎯 {guesser_team}: Guessing Time")
    st.info(f"📍 {data['Host']} is at {data['Location']}")
    
    if data.get('PhotoURL'):
        st.image(data['PhotoURL'])
    
    # We use a FORM so the app doesn't refresh until you hit the final button
    with st.form("guess_form"):
        st.write("Enter whole numbers for guesses:")
        col1, col2 = st.columns(2)
        g1 = col1.number_input(f"Guess A {host_names[0]}", value=0, step=1)
        g2 = col2.number_input(f"Guess A {host_names[1]}", value=0, step=1)
        
        col3, col4 = st.columns(2)
        g3 = col3.number_input(f"Guess B {host_names[0]}", value=0, step=1)
        g4 = col4.number_input(f"Guess B {host_names[1]}", value=0, step=1)
        
        submitted = st.form_submit_button("✅ SUBMIT FINAL GUESSES", use_container_width=True)
        
        if submitted:
            correct = sum([g1 == data['Hidden1'], g2 == data['Hidden2'], g3 == data['Hidden1'], g4 == data['Hidden2']])
            swing = correct - (4 - correct)
            
            # Update fresh scores
            latest = load_game_state()
            latest[guesser_team] += swing
            latest['Active_Round'] = "No"
            # Clear location/photo for the next round
            latest['Location'] = ""
            latest['PhotoURL'] = ""
            
            if save_game_state(latest):
                st.success(f"Correct: {data['Hidden1']} & {data['Hidden2']}. Points: {swing}")
                if swing > 0: st.balloons()
                time.sleep(3)
                st.rerun()

st.divider()
if st.sidebar.button("🚨 Reset Everything"):
    save_game_state({"Savarese": 0, "Willis": 0, "Active_Round": "No", "Hidden1": 0, "Hidden2": 0, "Host": "", "Location": "", "PhotoURL": ""})
    st.rerun()
