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
        return ""

def load_game_state():
    try:
        # Force a fresh fetch by adding a unique query parameter
        url = f"{get_db_url()}?nocache={time.time()}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200 and r.json():
            return r.json()
    except:
        pass
    return {"Savarese": 0, "Willis": 0, "Active": "No", "H1": 0, "H2": 0, "Host": "", "Loc": "", "URL": "", "LastResult": ""}

def save_game_state(new_data):
    try:
        # We fetch the absolute latest data from the server first
        current_cloud_data = load_game_state()
        # Merge the new round data into the cloud data (preserves scores)
        current_cloud_data.update(new_data)
        
        r = requests.put(get_db_url(), json=current_cloud_data, timeout=10)
        return r.status_code == 200
    except:
        return False

# --- IDENTITY & SESSION ---
if 'my_team' not in st.session_state:
    st.session_state.my_team = None

if st.session_state.my_team is None:
    st.title("🍹 Beverage Ballot")
    c1, c2 = st.columns(2)
    if c1.button("Team Savarese", use_container_width=True):
        st.session_state.my_team = "Team Savarese"
        st.rerun()
    if c2.button("Team Willis", use_container_width=True):
        st.session_state.my_team = "Team Willis"
        st.rerun()
    st.stop()

# LOAD DATA
data = load_game_state()

st.title("🍹 Beverage Ballot")
st.caption(f"Team: **{st.session_state.my_team}**")

if st.button("🔄 FORCE SYNC ALL PHONES", type="primary", use_container_width=True):
    st.rerun()

# --- THE SCOREBOARD (The Source of Truth) ---
sav_score = int(data.get('Savarese', 0))
wil_score = int(data.get('Willis', 0))

col_s, col_w = st.columns(2)
col_s.metric("Team Savarese", f"{sav_score} pts")
col_w.metric("Team Willis", f"{wil_score} pts")
st.divider()

sav_names = ["Ralph", "Trisha"]
wil_names = ["Charles", "Barbara"]

# --- ROUND LOGIC ---
if str(data.get('Active')) != "Yes":
    if data.get('LastResult'):
        st.success(f"{data['LastResult']}")

    st.header("📢 Start a New Round")
    host_choice = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    
    if st.session_state.my_team == host_choice:
        loc = st.text_input("Location?")
        img = st.camera_input("Snap a Photo")
        h_ppl = sav_names if host_choice == "Team Savarese" else wil_names
        ca, cb = st.columns(2)
        d1 = ca.number_input(f"{h_ppl[0]}'s #", step=1, value=0)
        d2 = cb.number_input(f"{h_ppl[1]}'s #", step=1, value=0)
        
        if st.button("🚀 SEND ROUND", use_container_width=True):
            with st.spinner("Uploading..."):
                p_url = ""
                if img:
                    up_url = f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/image/upload"
                    r_img = requests.post(up_url, data={"upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET']}, files={"file": img})
                    p_url = r_img.json().get("secure_url", "")
                
                # ONLY update round details, do NOT touch Savarese/Willis scores here
                round_update = {
                    "Active": "Yes", "Host": host_choice, "H1": int(d1), "H2": int(d2),
                    "Loc": loc, "URL": p_url, "LastResult": ""
                }
                if save_game_state(round_update):
                    st.rerun()
    else:
        st.info(f"Waiting for **{host_choice}**...")

else:
    # --- GUESSING SCREEN ---
    h_team = data.get('Host')
    g_team = "Team Willis" if h_team == "Team Savarese" else "Team Savarese"
    h_names = sav_names if h_team == "Team Savarese" else wil_names
    
    st.header(f"🎯 {g_team}: Guessing Time!")
    st.info(f"📍 {h_team} is at {data.get('Loc')}")
    if data.get('URL'): st.image(data['URL'])
    
    if st.session_state.my_team == g_team:
        with st.form("guess_form"):
            c1, c2 = st.columns(2)
            ga1 = c1.number_input(f"Guess {h_names[0]}", step=1, value=0)
            ga2 = c2.number_input(f"Guess {h_names[1]}", step=1, value=0)
            c3, c4 = st.columns(2)
            gb1 = c3.number_input(f"Guess {h_names[0]} (B)", step=1, value=0)
            gb2 = c4.number_input(f"Guess {h_names[1]} (B)", step=1, value=0)
            
            if st.form_submit_button("✅ SUBMIT GUESSES", use_container_width=True):
                # Reload to get freshest answers and scores
                fresh = load_game_state()
                ans1, ans2 = int(fresh.get('H1', 0)), int(fresh.get('H2', 0))
                correct = sum([ga1==ans1, ga2==ans2, gb1==ans1, gb2==ans2])
                
                # Scoring Logic
                if correct == 4: label, pts = "🏆 Full Pint!", 4
                elif correct == 3: label, pts = "🍺 Almost Full", 2
                elif correct == 2: label, pts = "🌗 Half Pint", 0
                elif correct == 1: label, pts = "💧 Low Tide", -2
                else: label, pts = "💀 Empty Pint", -4
                
                # Update Score CUMULATIVELY
                new_total = int(fresh.get(g_team, 0)) + pts
                
                final_update = {
                    g_team: new_total,
                    "Active": "No",
                    "LastResult": f"{label}! {g_team} got {correct}/4 correct ({pts} pts). Answers: {ans1} & {ans2}"
                }
                if save_game_state(final_update):
                    if pts >= 0: st.balloons()
                    st.rerun()
    else:
        st.warning(f"Waiting for {g_team} to guess...")

# --- FOOTER ---
st.divider()
if st.button("🚪 Switch Team / Logout"):
    st.session_state.my_team = None
    st.rerun()

if st.sidebar.button("🚨 RESET ALL DATA"):
    save_game_state({"Savarese": 0, "Willis": 0, "Active": "No", "H1": 0, "H2": 0, "Host": "", "Loc": "", "URL": "", "LastResult": ""})
    st.rerun()
