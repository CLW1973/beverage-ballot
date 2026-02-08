import streamlit as st
import requests
import json
import time

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

def get_db_url():
    c = json.loads(st.secrets['FIREBASE_CONFIG'])
    return f"https://{c['projectId']}-default-rtdb.firebaseio.com/game.json"

def load_game():
    try:
        r = requests.get(f"{get_db_url()}?cb={time.time()}", timeout=5)
        return r.json() if r.status_code == 200 else {}
    except: return {}

def update_db(p):
    try: requests.patch(get_db_url(), json=p, timeout=10)
    except: pass

if 'my_team' not in st.session_state: st.session_state.my_team = None

if st.session_state.my_team is None:
    st.title("🍹 Beverage Ballot")
    c1, c2 = st.columns(2)
    if c1.button("Team Savarese"): st.session_state.my_team = "Team Savarese"; st.rerun()
    if c2.button("Team Willis"): st.session_state.my_team = "Team Willis"; st.rerun()
    st.stop()

data = load_game()
if not data: data = {"Savarese": 0, "Willis": 0, "Active": "No"}

st.title("🍹 Beverage Ballot")
st.caption(f"Team: {st.session_state.my_team}")

# --- SCOREBOARD ---
s_pts, w_pts = int(data.get('Savarese', 0)), int(data.get('Willis', 0))
c1, c2 = st.columns(2)
c1.metric("Team Savarese", f"{s_pts} pts")
c2.metric("Team Willis", f"{w_pts} pts")
if st.button("🔄 REFRESH SCORES", use_container_width=True): st.rerun()
st.divider()

sav_m, wil_m = ["Ralph", "Trisha"], ["Charles", "Barbara"]
is_active, host_t = (str(data.get('Active')) == "Yes"), data.get('Host')

if not is_active:
    if data.get('LastResult'): st.success(data['LastResult'])
    st.header("📢 Start Round")
    h_choice = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    if st.session_state.my_team == h_choice:
        loc = st.text_input("Location")
        img = st.camera_input("Photo")
        names = sav_m if h_choice == "Team Savarese" else wil_m
        ca, cb = st.columns(2)
        d1, d2 = ca.number_input(f"{names[0]} #", 0), cb.number_input(f"{names[1]} #", 0)
        if st.button("🚀 SEND", use_container_width=True):
            url = ""
            if img:
                try:
                    r_i = requests.post(f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/image/upload", data={"upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET']}, files={"file": img})
                    url = r_i.json().get("secure_url", "")
                except: pass
            update_db({"Active": "Yes", "Host": h_choice, "H1": int(d1), "H2": int(d2), "Loc": loc, "URL": url, "LastResult": ""})
            st.rerun()
    else: st.info(f"Waiting for {h_choice}...")
else:
    t_names = sav_m if host_t == "Team Savarese" else wil_m
    g_team = "Team Willis" if host_t == "Team Savarese" else "Team Savarese"
    if st.session_state.my_team == host_t:
