import streamlit as st
import requests
import json
import time

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- FIREBASE ENGINE ---
def get_db_url():
    config = json.loads(st.secrets['FIREBASE_CONFIG'])
    project_id = config['projectId']
    return f"https://{project_id}-default-rtdb.firebaseio.com/game.json"

def save_game_state(data):
    try:
        r = requests.put(get_db_url(), json=data, timeout=10)
        return r.status_code == 200
    except:
        return False

def load_game_state():
    try:
        r = requests.get(get_db_url(), timeout=5)
        if r.status_code == 200 and r.json():
            return r.json()
    except:
        pass
    return {"Savarese": 0, "Willis": 0, "Active": "No", "H1": 0, "H2": 0, "Host": "", "Loc": "", "URL": "", "LastResult": ""}

# --- IDENTITY LOGIC ---
if 'my_team' not in st.session_state:
    st.session_state.my_team = None

if st.session_state.my_team is None:
    st.title("🍹 Beverage Ballot")
    st.subheader("Which team are you on?")
    c1, c2 = st.columns(2)
    if c1.button("Team Savarese", use_container_width=True):
        st.session_state.my_team = "Team Savarese"
        st.rerun()
    if c2.button("Team Willis", use_container_width=True):
        st.session_state.my_team = "Team Willis"
        st.rerun()
    st.stop()

# Load Data
data = load_game_state()

st.title("🍹 Beverage Ballot")
st.caption(f"Team: **{st.session_state.my_team}**")

# --- SYNC BUTTON ---
if st.button("🔄 REFRESH / SYNC", type="primary", use_container_width=True):
    st.rerun()

# Scoreboard
c1, c2 = st.columns(2)
c1.metric("Savarese", f"{data.get('Savarese', 0)}")
c2.metric("Willis", f"{data.get('Willis', 0)}")
st.divider()

sav_names = ["Ralph", "Trisha"]
wil_names = ["Charles", "Barbara"]

# --- APP NAVIGATION ---
if data.get('Active') == "No":
    # Show previous round outcome
    if data.get('LastResult'):
        st.success(f"🏁 {data['LastResult']}")

    st.header("📢 Start a Round")
    if st.session_state.my_team == "Team Savarese":
        loc = st.text_input("Where are you?")
        img = st.camera_input("Snapshot")
        col1, col2 = st.columns(2)
        d1 = col1.number_input(f"{sav_names[0]}'s #", step=1, value=0)
        d2 = col2.number_input(f"{sav_names[1]}'s #", step=1, value=0)
        
        if st.button("🚀 SEND ROUND", use_container_width=True):
            with st.spinner("Broadcasting..."):
                p_url = ""
                if img:
                    up_url = f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/image/upload"
                    r_img = requests.post(up_url, data={"upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET']}, files={"file": img})
                    p_url = r_img.json().get("secure_url", "")
                
                data.update({
                    "Active": "Yes", "Host": "Team Savarese", "H1": int(d1), "H2": int(d2),
                    "Loc": loc, "URL": p_url, "LastResult": ""
                })
                if save_game_state(data):
                    st.rerun()
    else:
        st.info("Waiting for Team Savarese to order drinks...")

else:
    # --- GUESSING SCREEN ---
    guesser = "Team Willis" if data['Host'] == "Team Savarese" else "Team Savarese"
    h_names = sav_names if data['Host'] == "Team Savarese" else wil_names
    
    st.header(f"🎯 {guesser}'s Turn")
    st.info(f"📍 {data['Host']} is at {data['Loc']}")
    if data.get('URL'): st.image(data['URL'])
    
    if st.session_state.my_team == guesser:
        with st.form("guesses"):
            st.write("Enter your guesses:")
            c1, c2 = st.columns(2)
            ga1 = c1.number_input(f"Guess A {h_names[0]}", step=1, value=0)
            ga2 = c2.number_input(f"Guess A {h_names[1]}", step=1, value=0)
            c3, c4 = st.columns(2)
            gb1 = c3.number_input(f"Guess B {h_names[0]}", step=1, value=0)
            gb2 = c4.number_input(f"Guess B {h_names[1]}", step=1, value=0)
            
            if st.form_submit_button("✅ SUBMIT GUESSES", use_container_width=True):
                # Calculate correct answers
                correct = sum([ga1==data['H1'], ga2==data['H2'], gb1==data['H1'], gb2==data['H2']])
                pts = correct - (4 - correct)
                
                # Update Score and Reset
                data[guesser] += pts
                data['Active'] = "No"
                data['LastResult'] = f"{guesser} got {correct}/4 correct! ({pts} pts). Answers: {data['H1']} & {data['H2']}"
                
                if save_game_state(data):
                    st.rerun()
    else:
        st.warning(f"Waiting for {guesser} to guess...")
        st.write("You are 'view-only' until the guesses are in.")

# --- FOOTER ---
st.divider()
if st.button("🚪 Switch Team / Logout"):
    st.session_state.my_team = None
    st.rerun()

if st.sidebar.button("🚨 Reset All Data"):
    save_game_state({"Savarese": 0, "Willis": 0, "Active": "No", "H1": 0, "H2": 0, "Host": "", "Loc": "", "URL": "", "LastResult": ""})
    st.rerun()
