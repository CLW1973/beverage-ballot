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
        # PATCH is the key to cumulative scores - it doesn't overwrite other data
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

# Load Data
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

if st.button("🔄 REFRESH / SYNC", type="primary", use_container_width=True):
    st.rerun()
st.divider()

# Define Team Members
sav_members = ["Ralph", "Trisha"]
wil_members = ["Charles", "Barbara"]

# --- ROUND LOGIC ---
if str(data.get('Active')) != "Yes":
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
                "Active": "Yes", "Host": host_choice, "H1": int(d1), "H2": int(d2),
                "Loc": loc, "URL": p_url, "LastResult": ""
            })
            st.rerun()
    else:
        st.info(f"Waiting for **{host_choice}** to start...")

else:
    # --- GUESSING SCREEN ---
    h_team = data.get('Host')
    g_team = "Team Willis" if h_team == "Team Savarese" else "Team Savarese"
    h_names = sav_members if h_team == "Team Savarese" else wil_members
    
    st.header(f"🎯 {g_team}: Your Turn")
    if data.get('URL'): st.image(data['URL'])
    
    with st.form("guess_form"):
        st.write("Each player gets 2 guesses. Leave 0 if a player is away.")
        
        st.subheader(f"Player: {h_names[0]}")
        c1, c2 = st.columns(2)
        g1_a = c1.number_input(f"{h_names[0]} Guess 1", step=1, value=0)
        g1_b = c2.number_input(f"{h_names[0]} Guess 2", step=1, value=0)
        
        st.subheader(f"Player: {h_names[1]}")
        c3, c4 = st.columns(2)
        g2_a = c3.number_input(f"{h_names[1]} Guess 1", step=1, value=0)
        g2_b = c4.number_input(f"{h_names[1]} Guess 2", step=1, value=0)
        
        if st.form_submit_button("✅ SUBMIT GUESSES", use_container_width=True):
            fresh = load_game_state()
            ans1, ans2 = int(fresh.get('H1', 0)), int(fresh.get('H2', 0))
            
            correct = 0
            slots_active = 0
            
            # Score Person 1
            if g1_a > 0 or g1_b > 0:
                slots_active += 2
                if g1_a == ans1: correct += 1
                if g1_b == ans1: correct += 1
                
            # Score Person 2
            if g2_a > 0 or g2_b > 0:
                slots_active += 2
                if g2_a == ans2: correct += 1
                if g2_b == ans2: correct += 1

            if slots_active == 0:
                st.error("Please enter at least one guess!")
            else:
                pct = correct / slots_active
                is_full_team = (slots_active == 4)
                
                # Scoring Matrix
                if pct == 1.0: 
                    label, pts = "🏆 Full Pint!", (4 if is_full_team else 2)
                elif pct >= 0.75: 
                    label, pts = "🍺 Almost Full", 2
                elif pct == 0.5: 
                    label, pts = "🌗 Half Pint", 0
                elif pct >= 0.25: 
                    label, pts = "💧 Low Tide", -2
                else: 
                    label, pts = "💀 Empty Pint", (-4 if is_full_team else -2)
                
                # CUMULATIVE UPDATE
                current_total = int(fresh.get(g_team, 0))
                update_db({
                    g_team: current_total + pts,
                    "Active": "No",
                    "LastResult": f"{label} ({correct}/{slots_active} correct). {pts} pts added to {g_team}!"
                })
                if pts >= 0: st.balloons()
                st.rerun()

# --- FOOTER ---
st.divider()
if st.sidebar.button("🚨 RESET ALL SCORES"):
    update_db({"Savarese": 0, "Willis": 0, "Active": "No", "LastResult": "Game Reset!"})
    st.rerun()
