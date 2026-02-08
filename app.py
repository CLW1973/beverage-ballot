import streamlit as st
import requests
import time
import json

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- CLOUDINARY UTILS ---
def get_cloudinary_url(filename):
    return f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/raw/upload"

def save_game_state(data):
    try:
        url = get_cloudinary_url("game_state.json")
        # Convert dict to string then bytes
        json_data = json.dumps(data)
        payload = {
            "upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET'],
            "public_id": "willis_savarese_game_state",
            "resource_type": "raw"
        }
        files = {"file": ("game_state.json", json_data)}
        r = requests.post(url, data=payload, files=files)
        return r.status_code == 200
    except:
        return False

def load_game_state():
    try:
        # Fetch the raw JSON file from your Cloudinary
        url = f"https://res.cloudinary.com/{st.secrets['CLOUDINARY_CLOUD_NAME']}/raw/upload/willis_savarese_game_state.json"
        # Adding a timestamp to bypass cache
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

# Initial Load
if 'game_data' not in st.session_state:
    st.session_state.game_data = load_game_state()

st.title("🍹 Beverage Ballot")

# --- REFRESH BUTTON (Team Willis must use this) ---
if st.button("🔄 REFRESH / SYNC GAME", type="primary", use_container_width=True):
    st.session_state.game_data = load_game_state()
    st.rerun()

data = st.session_state.game_data

# --- SCOREBOARD ---
c1, c2 = st.columns(2)
c1.metric("Team Savarese", f"{data.get('Savarese', 0)} pts")
c2.metric("Team Willis", f"{data.get('Willis', 0)} pts")
st.divider()

savarese_players = ["Ralph", "Trisha"]
willis_players = ["Charles", "Barbara"]

# --- APP LOGIC ---
if data.get('Active_Round') == "No":
    st.header("📢 Start a Round")
    h_team = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    loc = st.text_input("Where are you?")
    img = st.camera_input("Snap the Menu/Drinks")
    
    p_names = savarese_players if h_team == "Team Savarese" else willis_players
    col_a, col_b = st.columns(2)
    d1 = col_a.number_input(f"{p_names[0]}'s #", value=0, step=1)
    d2 = col_b.number_input(f"{p_names[1]}'s #", value=0, step=1)
    
    if st.button("🚀 SEND ROUND", use_container_width=True):
        with st.spinner("Syncing to Cloud..."):
            photo_url = upload_image(img) if img else ""
            data.update({
                "Active_Round": "Yes", "Host": h_team,
                "Hidden1": d1, "Hidden2": d2, "Location": loc, "PhotoURL": photo_url
            })
            if save_game_state(data):
                st.success("Round sent! Tell the others to Refresh.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Error saving to Cloudinary. Check your Secrets.")

else:
    # --- GUESSING SCREEN ---
    guesser = "Team Willis" if data['Host'] == "Team Savarese" else "Team Savarese"
    host_p = savarese_players if data['Host'] == "Team Savarese" else willis_players
    
    st.header(f"🎯 {guesser}: Your Turn!")
    st.info(f"📍 {data['Host']} is at {data['Location']}")
    
    if data.get('PhotoURL'):
        st.image(data['PhotoURL'])
    
    st.write("Each person enters 2 guesses:")
    g1 = st.number_input(f"Guess A for {host_p[0]}", key="g1")
    g2 = st.number_input(f"Guess B for {host_p[1]}", key="g2")
    g3 = st.number_input(f"Guess C for {host_p[0]}", key="g3")
    g4 = st.number_input(f"Guess D for {host_p[1]}", key="g4")

    if st.button("✅ SUBMIT FINAL GUESSES", use_container_width=True):
        correct = sum([g1 == data['Hidden1'], g2 == data['Hidden2'], g3 == data['Hidden1'], g4 == data['Hidden2']])
        swing = correct - (4 - correct)
        
        data[guesser] += swing
        data['Active_Round'] = "No"
        
        if save_game_state(data):
            st.write(f"Correct numbers: {data['Hidden1']} & {data['Hidden2']}")
            if swing > 0: st.balloons()
            time.sleep(3)
            st.rerun()

st.divider()
if st.button("🚨 Reset All Data"):
    save_game_state({"Savarese": 0, "Willis": 0, "Active_Round": "No", "Hidden1": 0, "Hidden2": 0, "Host": "", "Location": "", "PhotoURL": ""})
    st.rerun()
