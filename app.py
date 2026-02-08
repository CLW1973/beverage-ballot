import streamlit as st
import requests
import json
import time

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- FIREBASE ENGINE ---
def get_db_url():
    try:
        config = json.loads(st.secrets['FIREBASE_CONFIG'])
        project_id = config['projectId']
        return f"https://{project_id}-default-rtdb.firebaseio.com/game.json"
    except:
        st.error("Firebase Config missing from Secrets!")
        return ""

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

if st.button("🔄 REFRESH / SYNC", type="primary", use_container_width=True):
    st.rerun()

# Scoreboard - Ensuring we always have a number to display
s_score = data.get('Savarese', 0)
w_score = data.get('Willis', 0)
c1, c2 = st.columns(2)
c1.metric("Savarese", f"{s_score}")
c2.metric("Willis", f"{w_score}")
st.divider()

sav_names = ["Ralph", "Trisha"]
wil_names = ["Charles", "Barbara"]

# --- APP NAVIGATION ---
if str(data.get('Active')) != "Yes":
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
                
                # Setup new round
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
    host_team = data.get('Host', 'Team Savarese')
    guesser_team = "Team Willis" if host_team == "Team Savarese" else "Team Savarese"
    host_names = sav_names if host_team == "Team Savarese" else wil_names
    
    st.header(f"🎯 {guesser_team}'s Turn")
    st.info(f"📍 {host_team} is at {data.get('Loc', 'Unknown')}")
    if data.get('URL'): st.image(data['URL'])
    
    if st.session_state.my_team == guesser_team:
        with st.form("guesses"):
            st.write("Enter your guesses:")
            c1, c2 = st.columns(2)
            ga1 = c1.number_input(f"Guess A {host_names[0]}", step=1, value=0)
            ga2 = c2.number_input(f"Guess A {host_names[1]}", step=1, value=0)
            c3, c4 = st.columns(2)
            gb1 = c3.number_input(f"Guess B {host_names[0]}", step=1, value=0)
            gb2 = c4.number_input(f"Guess B {host_names[1]}", value=0, step=1)
            
            if st.form_submit_button("✅ SUBMIT GUESSES", use_container_width=True):
                # Calculate correct answers
                ans1 = int(data.get('H1', 0))
                ans2 = int(data.get('H2', 0))
                correct = sum([ga1==ans1, ga2==ans2, gb1==ans1, gb2==ans2])
                pts = correct - (4 - correct)
                
                # Fetch fresh scores from database to be safe
                latest = load_game_state()
                current_score = latest.get(guesser_team, 0)
                
                latest[guesser_team] = current_score + pts
                latest['Active'] = "No"
                latest['LastResult'] = f"{guesser_team} got {correct}/4 correct! ({pts} pts). Answers were: {ans1} & {ans2}"
                
                if save_game_state(latest):
                    st.balloons()
                    st.rerun()
    else:
        st.warning(f"Waiting for {guesser_team} to guess...")
        st.write("The screen will update once they submit!")

# --- FOOTER ---
st.divider()
if st.button("🚪 Switch Team / Logout"):
    st.session_state.my_team = None
    st.rerun()

if st.sidebar.button("🚨 Reset All Data"):
    save_game_state({"Savarese": 0, "Willis": 0, "Active": "No", "H1": 0, "H2": 0, "Host": "", "Loc": "", "URL": "", "LastResult": ""})
    st.rerun()
