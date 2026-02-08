import streamlit as st
import requests
import json
import time

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- FIREBASE ENGINE ---
def get_db_url(path="game"):
    config = json.loads(st.secrets['FIREBASE_CONFIG'])
    return f"https://{config['projectId']}-default-rtdb.firebaseio.com/{path}.json"

def load_game_state():
    try:
        # Cache-busting prevents the phone from showing old scores
        r = requests.get(f"{get_db_url()}?cb={time.time()}", timeout=5)
        return r.json() if r.status_code == 200 else {}
    except:
        return {}

def update_db(payload):
    try:
        # PATCH updates only what we send, preserving the scoreboard
        requests.patch(get_db_url(), json=payload, timeout=10)
        return True
    except:
        return False

# --- IDENTITY & PERSISTENCE ---
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

# FORCE FRESH LOAD
data = load_game_state()
if not data:
    data = {"Savarese": 0, "Willis": 0, "Active": "No"}

st.title("🍹 Beverage Ballot")
st.caption(f"Logged in as: **{st.session_state.my_team}**")

# --- SCOREBOARD ---
s_pts = int(data.get('Savarese', 0))
w_pts = int(data.get('Willis', 0))
col_s, col_w = st.columns(2)
col_s.metric("Team Savarese", f"{s_pts} pts")
col_w.metric("Team Willis", f"{w_pts} pts")

if st.button("🔄 REFRESH SCORES", type="primary", use_container_width=True):
    st.rerun()
st.divider()

sav_members = ["Ralph", "Trisha"]
wil_members = ["Charles", "Barbara"]

# --- VIEW LOGIC ---
is_active = (str(data.get('Active')) == "Yes")
host_team = data.get('Host')

# SCENARIO A: NO ACTIVE ROUND
if not is_active:
    if data.get('LastResult'):
        st.success(data['LastResult'])

    st.header("📢 Start a Round")
    host_choice = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    
    if st.session_state.my_team == host_choice:
        loc = st.text_input("Location Name")
        img = st.camera_input("Snapshot")
        h_names = sav_members if host_choice == "Team Savarese" else wil_members
        
        ca, cb = st.columns(2)
        d1 = ca.number_input(f"{h_names[0]}'s #", step=1, value=0)
        d2 = cb.number_input(f"{h_names[1]}'s #", step=1, value=0)
        
        if st.button("🚀 SEND ROUND", use_container_width=True):
            p_url = ""
            if img:
                up_url = f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/image/upload"
                r_img = requests.post(up_url, data={"upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET']}, files={"file": img})
                p_url = r_img.json().get("secure_url", "")
            
            update_db({
                "Active": "Yes", 
                "Host": host_choice, 
                "H1": int(d1), 
                "H2": int(d2),
                "Loc": loc, 
                "URL": p_url, 
                "LastResult": ""
            })
            st.rerun()
    else:
        st.info(f"Waiting for **{host_choice}** to start the round...")

# SCENARIO B: ROUND IS ACTIVE
else:
    guesser_team = "Team Willis" if host_team == "Team Savarese" else "Team Savarese"
    h_names = sav_members if host_team == "Team Savarese" else wil_members

    # 1. HOST VIEW (The ones who sent the drinks)
    if st.session_state.my_team == host_team:
        st.header("⏳ Waiting for Guessers")
        st.info(f"Round sent from **{data.get('Loc')}**. Waiting for **{guesser_team}** to guess.")
        if data.get('URL'): 
            st.image(data.get('URL'), caption="Your drink photo")
        if st.button("🔄 Check for Results"): 
            st.rerun()

    # 2. GUESSER VIEW (The ones guessing)
    else:
        st.header(f"🎯 {guesser_team}: Guess!")
        if data.get('URL'): 
            st.image(data.get('URL'))
        st.write(f"📍 Location: **{data.get('Loc')}**")
        
        with st.form("guess_form"):
            st.markdown(f"### Player: {h_names[0]}")
            c1, c2 = st.columns(2)
            g1_a = c1.number_input(f"Guess 1 for {h_names[0]}", step=1, value=0, key="p1a")
            g1_b = c2.number_input(f"Guess 2 for {h_names[0]}", step=1, value=0, key="p1b")
            
            st.markdown(f"### Player: {h_names[1]}")
            c3, c4 = st.columns(2)
            g2_a = c3.number_input(f"Guess 1 for {h_names[1]}", step=1, value=0, key="p2a")
            g2_b = c4.number_input(f"Guess 2 for {h_names[1]}", step=1, value=0
