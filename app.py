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
        r = requests.get(f"{get_db_url()}?cb={time.time()}", timeout=5)
        return r.json() if r.status_code == 200 else {}
    except:
        return {}

def update_db(payload):
    try:
        requests.patch(get_db_url(), json=payload, timeout=10)
        return True
    except:
        return False

# --- IDENTITY ---
if 'my_team' not in st.session_state:
    st.session_state.my_team = None

if st.session_state.my_team is None:
    st.title("🍹 Beverage Ballot")
    c1, c2 = st.columns(2)
    if c1.button("Team Savarese", use_container_width=True): 
        st.session_state.my_team = "Team Savarese"; st.rerun()
    if c2.button("Team Willis", use_container_width=True): 
        st.session_state.my_team = "Team Willis"; st.rerun()
    st.stop()

# --- LIVE SYNC ---
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

if st.button("🔄 REFRESH SCORES", use_container_width=True):
    st.rerun()
st.divider()

# Member Names
sav_members = ["Ralph", "Trisha"]
wil_members = ["Charles", "Barbara"]

# --- VIEW LOGIC ---
is_active = (str(data.get('Active')) == "Yes")
host_team = data.get('Host')

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
        d1 = ca.number_input(f"{h_names[0]}'s Drink #", step=1, value=0)
        d2 = cb.number_input(f"{h_names[1]}'s Drink #", step=1, value=0)
        
        if st.button("🚀 SEND ROUND", use_container_width=True):
            p_url = ""
            if img:
                try:
                    r_img = requests.post(f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/image/upload", 
                                         data={"upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET']}, 
                                         files={"file": img})
                    p_url = r_img.json().get("secure_url", "")
                except: p_url = ""
            update_db({"Active": "Yes", "Host": host_choice
