import streamlit as st
import requests
import time
import json
import random

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- CLOUDINARY SYNC ---
def save_game_state(data):
    try:
        # We use the 'upload' endpoint for raw files
        url = f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/raw/upload"
        json_data = json.dumps(data)
        payload = {
            "upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET'],
            "public_id": "willis_savarese_game_state",
            "resource_type": "raw",
            "overwrite": "true", # String "true" for Cloudinary API
            "invalidate": "true"  # Forces the CDN to dump old cached versions
        }
        files = {"file": ("game_state.json", json_data)}
        r = requests.post(url, data=payload, files=files, timeout=10)
        return r.status_code == 200
    except Exception as e:
        st.error(f"Save Error: {e}")
        return False

def load_game_state():
    try:
        # Cache busting with a random number to ensure we get the FRESH file
        cb = random.randint(1, 999999)
        url = f"https://res.cloudinary.com/{st.secrets['CLOUDINARY_CLOUD_NAME']}/raw/upload/willis_savarese_game_state.json"
        r = requests.get(f"{url}?cb={cb}", timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {"Savarese": 0, "Willis": 0, "Active_Round": "No", "Hidden1": 0, "Hidden2": 0, "Host": "", "Location": "", "PhotoURL": ""}

# --- APP START ---
if 'game_data' not in st.session_state:
    st.session_state.game_data = load_game_state()
    st.session_state.last_sync = time.strftime("%H:%M:%S")

st.title("🍹 Beverage Ballot")

# --- SYNC BUTTON ---
if st.button("🔄 SYNC & REFRESH", type="primary", use_container_width=True):
    st.session_state.game_data = load_game_state()
    st.session_state.last_sync = time.strftime("%H:%M:%S")
    st.rerun()

data = st.session_state.game_data
st.caption(f"Last Sync: {st.session_state.last_sync}")

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
    loc = st.text_input("Location?")
    img = st.camera_input("Snap the Menu")
    
    p_names = sav_names if h_team == "Team Savarese" else wil_names
    col_a, col_b = st.columns(2)
    d1 = col_a.number_input(f"{p_names[0]}'s Drink #", value=0, step=1)
    d2 = col_b.number_input(f"{p_names[1]}'s Drink #", value=0, step=1)
    
    if st.button("🚀 SEND ROUND", use_container_width=True):
        if d1 == 0 and d2 == 0:
            st.warning("Please enter drink numbers first!")
        else:
            with st.spinner("Pushing to Cloud..."):
                # Handle photo upload
                p_url = ""
                if img:
                    up_url = f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/image/upload"
                    r_img = requests.post(up_url, data={"upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET']}, files={"file": img})
                    p_url = r_img.json().get("secure_url", "")

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
                    st.success("SUCCESS! Round is live.")
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
    
    # Use form to prevent mid-typing refreshes
    with st.form("guess_form"):
        st.write("Enter whole numbers for guesses:")
        c1, c2 = st.columns(2)
        ga1 = c1.number_input(f"Guess A {host_names[0]}", value=0, step=1)
        ga2 = c2.number_input(f"Guess A {host_names[1]}", value=0, step=1)
        
        c3, c4 = st.columns(2)
        gb1 = c3.number_input(f"Guess B {host_names[0]}", value=0, step=1)
        gb2 = c4.number_input(f"Guess B {host_names[1]}", value=0, step=1)
        
        if st.form_submit_button("✅ SUBMIT FINAL GUESSES", use_container_width=True):
            # Calculation
            correct = sum([ga1 == data['Hidden1'], ga2 == data['Hidden2'], gb1 == data['Hidden1'], gb2 == data['Hidden2']])
            swing = correct - (4 - correct)
            
            # Update fresh state
            current = load_game_state()
            current[guesser_team] += swing
            current['Active_Round'] = "No"
            current['Location'] = ""
            current['PhotoURL'] = ""
            
            if save_game_state(current):
                st.success(f"Answers: {data['Hidden1']} & {data['Hidden2']}")
                if swing > 0: st.balloons()
                time.sleep(3)
                st.session_state.game_data = current
                st.rerun()

st.divider()
if st.sidebar.button("🚨 Emergency Reset"):
    save_game_state({"Savarese": 0, "Willis": 0, "Active_Round": "No", "Hidden1": 0, "Hidden2": 0, "Host": "", "Location": "", "PhotoURL": ""})
    st.rerun()
