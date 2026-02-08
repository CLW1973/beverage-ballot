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

# --- LOAD LIVE DATA ---
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

# Member mapping
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
            update_db({"Active": "Yes", "Host": host_choice, "H1": int(d1), "H2": int(d2), "Loc": loc, "URL": p_url, "LastResult": ""})
            st.rerun()
    else:
        st.info(f"Waiting for **{host_choice}** to start...")

else:
    # Set targets based on who is hosting
    target_names = sav_members if host_team == "Team Savarese" else wil_members
    guesser_team = "Team Willis" if host_team == "Team Savarese" else "Team Savarese"

    if st.session_state.my_team == host_team:
        st.header("⏳ Waiting for Guessers")
        st.info(f"Waiting for {guesser_team} to guess your drinks.")
        if data.get('URL'): st.image(data.get('URL'))
        if st.button("🔄 Check Results"): st.rerun()

    else:
        st.header(f"🎯 {guesser_team}: Guess!")
        if data.get('URL'): st.image(data.get('URL'))
        
        with st.form("guess_form"):
            st.write(f"Location: **{data.get('Loc')}**")
            
            # PLAYER A Section
            st.subheader("Player A")
            c1, c2 = st.columns(2)
            g1a = c1.number_input(f"Guess 1 for {target_names[0]}", step=1, value=0)
            g1b = c2.number_input(f"Guess 2 for {target_names[1]}", step=1, value=0)
            
            # PLAYER B Section
            st.subheader("Player B")
            c3, c4 = st.columns(2)
            g2a = c3.number_input(f"Guess 1 for {target_names[0]}", step=1, value=0)
            g2b = c4.number_input(f"Guess 2 for {target_names[1]}", step=1, value=0)
            
            if st.form_submit_button("✅ SUBMIT GUESSES", use_container_width=True):
                fresh = load_game_state()
                ans1, ans2 = int(fresh.get('H1', 0)), int(fresh.get('H2', 0))
                
                correct, slots = 0, 0
                # Check Player A's performance
                if g1a > 0 or g1b > 0:
                    slots += 2
                    if g1a == ans1: correct += 1
                    if g1b == ans2: correct += 1 # Cross-check for Player B's drink
                
                # Check Player B's performance
                if g2a > 0 or g2b > 0:
                    slots += 2
                    if g2a == ans1: correct += 1
                    if g2b == ans2: correct += 1

                if slots == 0:
                    st.error("Please enter a guess!")
                else:
                    pct = correct / slots
                    if pct == 1.0: lbl, pts = "🏆 Full Pint!", (4 if slots == 4 else 2)
                    elif pct >= 0.75: lbl, pts = "🍺 Almost Full", 2
                    elif pct == 0.5: lbl, pts = "🌗 Half Pint", 0
                    elif pct >= 0.25: lbl, pts = "💧 Low Tide", -2
                    else: lbl, pts = "💀 Empty Pint", (-4 if slots == 4 else -2)
