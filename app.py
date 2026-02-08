import streamlit as st
import requests
import time
import json

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
        url = f"https://res.cloudinary.com/{st.secrets['CLOUDINARY_CLOUD_NAME']}/raw/upload/willis_savarese_game_state.json"
        r = requests.get(f"{url}?t={time.time()}")
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

# Sync state
data = load_game_state()

st.title("🍹 Beverage Ballot")

# --- REFRESH ---
if st.button("🔄 REFRESH / SYNC GAME", type="primary", use_container_width=True):
    st.rerun()

# --- SCOREBOARD ---
c1, c2 = st.columns(2)
c1.metric("Team Savarese", f"{data.get('Savarese', 0)} pts")
c2.metric("Team Willis", f"{data.get('Willis', 0)} pts")
st.divider()

sav_names = ["Ralph", "Trisha"]
wil_names = ["Charles", "Barbara"]

if data.get('Active_Round') == "No":
    st.header("📢 Start a Round")
    h_team = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    loc = st.text_input("Where are you?")
    img = st.camera_input("Snap the Menu/Drinks")
    
    # Ordering names
    p_names = sav_names if h_team == "Team Savarese" else wil_names
    col_a, col_b = st.columns(2)
    d1 = col_a.number_input(f"{p_names[0]}'s Drink #", value=0, step=1)
    d2 = col_b.number_input(f"{p_names[1]}'s Drink #", value=0, step=1)
    
    if st.button("🚀 SEND ROUND", use_container_width=True):
        with st.spinner("Syncing..."):
            p_url = upload_image(img) if img else ""
            data.update({
                "Active_Round": "Yes", "Host": h_team,
                "Hidden1": int(d1), "Hidden2": int(d2), "Location": loc, "PhotoURL": p_url
            })
            if save_game_state(data):
                st.success("Round sent! Tell the others to Refresh.")
                time.sleep(1)
                st.rerun()

else:
    # --- GUESSING SCREEN ---
    guesser_team = "Team Willis" if data['Host'] == "Team Savarese" else "Team Savarese"
    host_names = sav_names if data['Host'] == "Team Savarese" else wil_names
    guesser_names = wil_names if guesser_team == "Team Willis" else sav_names
    
    st.header(f"🎯 {guesser_team}: Your Turn!")
    st.info(f"📍 {data['Host']} is at {data['Location']}")
    
    if data.get('PhotoURL'):
        st.image(data['PhotoURL'])
    
    st.write("Enter whole numbers for guesses:")
    
    # Custom Labels as requested
    col1, col2 = st.columns(2)
    g1 = col1.number_input(f"Guess A {host_names[0]}", value=0, step=1, key="g1")
    g2 = col2.number_input(f"Guess A {host_names[1]}", value=0, step=1, key="g2")
    
    col3, col4 = st.columns(2)
    g3 = col3.number_input(f"Guess B {host_names[0]}", value=0, step=1, key="g3")
    g4 = col4.number_input(f"Guess B {host_names[1]}", value=0, step=1, key="g4")

    if st.button("✅ SUBMIT FINAL GUESSES", use_container_width=True):
        # Math: Compare guesses to Hidden1 (Ralph/Charles) and Hidden2 (Trisha/Barbara)
        correct = 0
        if g1 == data['Hidden1']: correct += 1
        if g2 == data['Hidden2']: correct += 1
        if g3 == data['Hidden1']: correct += 1
        if g4 == data['Hidden2']: correct += 1
        
        # Scoring logic: +1 for right, -1 for wrong (4 total guesses)
        swing = correct - (4 - correct)
        
        # Update scores
        current_data = load_game_state() # Fresh pull to ensure scores are right
        current_data[guesser_team] += swing
        current_data['Active_Round'] = "No"
        
        if save_game_state(current_data):
            st.success(f"Correct numbers: {data['Hidden1']} & {data['Hidden2']}")
            if swing > 0: st.balloons()
            time.sleep(3)
            st.rerun()

st.divider()
if st.sidebar.button("🚨 Reset Scores"):
    save_game_state({"Savarese": 0, "Willis": 0, "Active_Round": "No", "Hidden1": 0, "Hidden2": 0, "Host": "", "Location": "", "PhotoURL": ""})
    st.rerun()
