import streamlit as st
import requests
import time
import json

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- DATABASE LOGIC ---
def save_game_state(data):
    try:
        url = f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/raw/upload"
        payload = {
            "upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET'],
            "public_id": "willis_savarese_state_v3",
            "resource_type": "raw",
            "overwrite": "true",
            "invalidate": "true" 
        }
        files = {"file": ("state.json", json.dumps(data))}
        r = requests.post(url, data=payload, files=files, timeout=10)
        return r.status_code == 200
    except:
        return False

def load_game_state():
    try:
        # Timestamp prevents the phone from showing "old" data
        url = f"https://res.cloudinary.com/{st.secrets['CLOUDINARY_CLOUD_NAME']}/raw/upload/willis_savarese_state_v3.json?t={int(time.time())}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {"Savarese": 0, "Willis": 0, "Active": "No", "H1": 0, "H2": 0, "Host": "Team Savarese", "Loc": "", "URL": ""}

# Load current state
if 'data' not in st.session_state:
    st.session_state.data = load_game_state()

data = st.session_state.data

st.title("🍹 Beverage Ballot")

# --- SYNC BUTTON ---
if st.button("🔄 REFRESH / SYNC", type="primary", use_container_width=True):
    st.session_state.data = load_game_state()
    st.rerun()

# Scoreboard
c1, c2 = st.columns(2)
c1.metric("Team Savarese", f"{data.get('Savarese', 0)} pts")
c2.metric("Team Willis", f"{data.get('Willis', 0)} pts")
st.divider()

sav_names = ["Ralph", "Trisha"]
wil_names = ["Charles", "Barbara"]

# --- AUTOMATIC UI SWITCH ---
if data.get('Active') == "No":
    st.header("📢 Start a Round")
    host_choice = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    loc = st.text_input("Location Name")
    img = st.camera_input("Snap the Menu")
    
    p_names = sav_names if host_choice == "Team Savarese" else wil_names
    col_a, col_b = st.columns(2)
    d1 = col_a.number_input(f"{p_names[0]}'s #", value=0, step=1)
    d2 = col_b.number_input(f"{p_names[1]}'s #", value=0, step=1)
    
    if st.button("🚀 SEND ROUND", use_container_width=True):
        if d1 == 0 and d2 == 0:
            st.error("Enter drink numbers first!")
        else:
            with st.spinner("Uploading..."):
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
    # --- GUESSING SCREEN (The Automatic Switch) ---
    guesser = "Team Willis" if data['Host'] == "Team Savarese" else "Team Savarese"
    h_names = sav_names if data['Host'] == "Team Savarese" else wil_names
    
    st.header(f"🎯 {guesser}: Your Turn!")
    st.info(f"📍 {data['Host']} is at {data['Loc']}")
    
    if data.get('URL'):
        st.image(f"{data['URL']}?t={time.time()}")
    
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
            
            # Final update
            latest = load_game_state()
            latest[guesser] += swing
            latest['Active'] = "No"
            latest['Loc'] = ""
            latest['URL'] = ""
            
            if save_game_state(latest):
                st.session_state.data = latest
                if swing > 0: st.balloons()
                st.rerun()

st.sidebar.divider()
if st.sidebar.button("🚨 Reset Scores"):
    save_game_state({"Savarese": 0, "Willis": 0, "Active": "No", "H1": 0, "H2": 0, "Host": "Team Savarese", "Loc": "", "URL": ""})
    st.rerun()
