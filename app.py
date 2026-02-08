import streamlit as st
import requests, json, time

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

# --- LOGIN ---
if 'my_team' not in st.session_state: st.session_state.my_team = None
if st.session_state.my_team is None:
    st.title("🍹 Beverage Ballot")
    c1, c2 = st.columns(2)
    if c1.button("Team Savarese"): st.session_state.my_team = "Team Savarese"; st.rerun()
    if c2.button("Team Willis"): st.session_state.my_team = "Team Willis"; st.rerun()
    st.stop()

# --- LOAD DATA ---
data = load_game()
if not data: data = {"Savarese": 0, "Willis": 0, "Active": "No"}

st.title("🍹 Beverage Ballot")

# --- RESET BUTTON (PRIORITY #1) ---
# Placing this here ensures it loads even if the rest of the page errors out.
if st.button("🚨 RESET ALL SCORES", use_container_width=True):
    update_db({"Savarese": 0, "Willis": 0, "Active": "No", "LastResult": "Reset!"})
    st.rerun()

st.divider()

# --- SCOREBOARD ---
s_pts, w_pts = int(data.get('Savarese', 0)), int(data.get('Willis', 0))
sc1, sc2 = st.columns(2)
sc1.metric("Team Savarese", f"{s_pts} pts")
sc2.metric("Team Willis", f"{w_pts} pts")
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
        d1 = ca.number_input(f"{names[0]} #", 0)
        d2 = cb.number_input(f"{names[1]} #", 0)
        if st.button("🚀 SEND", use_container_width=True):
            url = ""
            if img:
                try:
                    r_i = requests.post(f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/image/upload", data={"upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET']}, files={"file": img})
                    url = r_i.json().get("secure_url", "")
                except: pass
            update_db({"Active": "Yes", "Host": h_choice, "H1": int(d1), "H2": int(d2), "Loc": loc, "URL": url, "LastResult": ""})
            st.rerun()
    else: st.info(f"Waiting for {h_choice} to start...")
else:
    t_names = sav_m if host_t == "Team Savarese" else wil_m
    g_team = "Team Willis" if host_t == "Team Savarese" else "Team Savarese"
    if st.session_state.my_team == host_t:
        st.info(f"Waiting for {g_team} to guess...")
        if data.get('URL'): st.image(data['URL'])
        if st.button("🔄 Check Result"): st.rerun()
    else:
        st.header(f"🎯 {g_team}: Guess!")
        if data.get('URL'): st.image(data['URL'])
        with st.form("g_form"):
            st.subheader("Player A")
            ca1, ca2 = st.columns(2)
            ga1 = ca1.number_input(f"A: {t_names[0]}", 0)
            ga2 = ca2.number_input(f"A: {t_names[1]}", 0)
            st.subheader("Player B")
            cb1, cb2 = st.columns(2)
            gb1 = cb1.number_input(f"B: {t_names[0]}", 0)
            gb2 = cb2.number_input(f"B: {t_names[1]}", 0)
            if st.form_submit_button("✅ SUBMIT"):
                fresh = load_game()
                ans1, ans2 = int(fresh.get('H1', 0)), int(fresh.get('H2', 0))
                cor, slots = 0, 0
                if (ga1 > 0 or ga2 > 0):
                    slots += 2
                    if ga1 == ans1: cor += 1
                    if ga2 == ans2: cor += 1
                if (gb1 > 0 or gb2 > 0):
                    slots += 2
                    if gb1 == ans1: cor += 1
                    if gb2 == ans2: cor += 1
                if slots > 0:
                    pct = cor / slots
                    if pct == 1.0: lbl, pts = "🏆 Full!", (4 if slots == 4 else 2)
                    elif pct >= 0.5: lbl, pts = "🌗 Half", 0
                    else: lbl, pts = "💀 Empty", (-4 if slots == 4 else -2)
                    cur_tot = int(fresh.get(g_team, 0))
                    update_db({g_team: cur_tot + pts, "Active": "No", "LastResult": f"{lbl}. {pts} pts added!"})
                    st.rerun()
