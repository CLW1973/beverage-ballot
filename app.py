import streamlit as st
import requests
import time
import json

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- NEW LOGIC: UNIQUE FILES ---
def save_game_state(data):
    try:
        # We create a unique name for every single save (e.g., game_171400)
        # This bypasses the 'Overwrite Not Allowed' error
        timestamp = int(time.time())
        unique_id = f"ballot_{timestamp}"
        
        url = f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/raw/upload"
        payload = {
            "upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET'],
            "public_id": unique_id,
            "resource_type": "raw",
            "tags": "beverage_ballot_update" # We tag it so we can find it later
        }
        
        files = {"file": json.dumps(data)}
        r = requests.post(url, data=payload, files=files, timeout=10)
        return r.status_code == 200
    except:
        return False

def load_game_state():
    try:
        # We ask Cloudinary for the most recent file with our tag
        search_url = f"https://res.cloudinary.com/{st.secrets['CLOUDINARY_CLOUD_NAME']}/raw/list/beverage_ballot_update.json"
        r_list = requests.get(f"{search_url}?t={time.time()}", timeout=5)
        
        if r_list.status_code == 200:
            # Sort by version/date and get the newest one
            resources = r_list.json().get('resources', [])
            if resources:
                latest = sorted(resources, key=lambda x: x['version'], reverse=True)[0]
                file_url = f"https://res.cloudinary.com/{st.secrets['CLOUDINARY_CLOUD_NAME']}/raw/upload/v{latest['version']}/{latest['public_id']}.json"
                r_data = requests.get(file_url)
                return r_data.json()
    except:
        pass
    return {"Savarese": 0, "Willis": 0, "Active": "No", "H1": 0, "H2": 0, "Host": "Team Savarese", "Loc": "", "URL": ""}

# Sync session
if 'data' not in st.session_state:
    st.session_state.data = load_game_state()

data = st.session_state.data

st.title("🍹 Beverage Ballot")

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

if str(data.get('Active')) != "Yes":
    st.header("📢 Start a Round")
    host_choice = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    loc = st.text_input("Location Name")
    img = st.camera_input("Snap the Menu/Drinks")
    
    p_names = sav_names if host_choice == "Team Savarese" else wil_names
    col_a, col_b = st.columns(2)
    d1 = col_a.number_input(f"{p_names[0]}'s #", value=0, step=1)
    d2 = col_b.number_input(f"{p_names[1]}'s #", value=0, step=1)
    
    if st.button("🚀 SEND ROUND", use_container_width=True):
        with st.spinner("Uploading..."):
            p_url = ""
            if img:
                up_url = f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/image/upload"
                r_img = requests.post(up_url, data={"upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET']}, files={"file": img})
                p_url = r_img.json().get("secure_url", "")

            new_state = {
                "Savarese": data.get('Savarese', 0), "Willis": data.get('Willis', 0),
                "Active": "Yes", "Host": host_choice, "H1": int(d1), "H2": int(d2),
                "Loc": loc, "URL": p_url
            }
            if save_game_state(new_state):
                st.session_state.data = new_state
                st.rerun()
else:
    guesser = "Team Willis" if data['Host'] == "Team Savarese" else "Team Savarese"
    h_names = sav_names if data['Host'] == "Team Savarese" else wil_names
    
    st.header(f"🎯 {guesser}: Your Turn!")
    st.info(f"📍 {data['Host']} is at {data['Loc']}")
    if data.get('URL'): st.image(data['URL'])
    
    with st.form("guess_form"):
        st.write("Enter guesses:")
        c1, c2 = st.columns(2)
        ga1 = c1.number_input(f"Guess A {h_names[0]}", value=0, step=1)
        ga2 = c2.number_input(f"Guess A {h_names[1]}", value=0, step=1)
        c3, c4 = st.columns(2)
        gb1 = c3.number_input(f"Guess B {h_names[0]}", value=0, step=1)
        gb2 = c4.number_input(f"Guess B {h_names[1]}", value=0, step=1)
        
        if st.form_submit_button("✅ SUBMIT FINAL GUESSES", use_container_width=True):
            correct = sum([ga1==data['H1'], ga2==data['H2'], gb1==data['H1'], gb2==data['H2']])
            swing = correct - (4 - correct)
            latest = load_game_state()
            latest[guesser] = latest.get(guesser, 0) + swing
            latest['Active'] = "No"
            if save_game_state(latest):
                st.session_state.data = latest
                if swing > 0: st.balloons()
                st.rerun()

if st.sidebar.button("🚨 Reset Scores"):
    save_game_state({"Savarese": 0, "Willis": 0, "Active": "No", "H1": 0, "H2": 0, "Host": "Team Savarese", "Loc": "", "URL": ""})
    st.rerun()
