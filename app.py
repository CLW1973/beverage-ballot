import streamlit as st
import requests
import time

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- NO-FAIL SYNC SETUP ---
# We use a unique ID for your specific game
GAME_ID = "willis_savarese_2024_final_v1"
DB_URL = f"https://kvstore.com/api/v1/items/{GAME_ID}"

def get_data():
    try:
        r = requests.get(DB_URL, timeout=5)
        if r.status_code == 200:
            return r.json()['value']
    except:
        pass
    return {"Savarese": 0, "Willis": 0, "Active_Round": "No", "Hidden1": 0, "Hidden2": 0, "Host": "", "Location": "", "PhotoURL": ""}

def save_data(payload):
    try:
        requests.post(DB_URL, json={"value": payload}, timeout=5)
        return True
    except:
        return False

# --- PHOTO UPLOAD ---
def upload_image(image_file):
    try:
        url = f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/image/upload"
        files = {"file": image_file}
        payload = {"upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET']}
        response = requests.post(url, files=files, data=payload)
        return response.json().get("secure_url")
    except:
        return None

# Load State
data = get_data()

st.title("🍹 Beverage Ballot")

# Sidebar Rules with your specific players
with st.sidebar:
    st.header("👥 The Players")
    st.write("**Team Savarese:** Ralph & Trisha")
    st.write("**Team Willis:** Charles & Barbara")
    st.divider()
    st.write("**Scoring:**")
    st.write("✅ Right: +1 | ❌ Wrong: -1")
    if st.button("Reset All Scores"):
        save_data({"Savarese": 0, "Willis": 0, "Active_Round": "No", "Hidden1": 0, "Hidden2": 0, "Host": "", "Location": "", "PhotoURL": ""})
        st.rerun()

# --- SCOREBOARD ---
c1, c2 = st.columns(2)
c1.metric("Team Savarese", f"{data['Savarese']} pts")
c2.metric("Team Willis", f"{data['Willis']} pts")

if st.button("🔄 Check for Move", use_container_width=True):
    st.rerun()

st.divider()

# --- GAME LOGIC ---
if data['Active_Round'] == "No":
    st.subheader("📢 Start a Round")
    h_team = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    loc = st.text_input("Location Name")
    
    img = st.camera_input("Snap the Menu/Drinks")
    
    p1, p2 = ("Ralph", "Trisha") if h_team == "Team Savarese" else ("Charles", "Barbara")
    col_a, col_b = st.columns(2)
    d1 = col_a.number_input(f"{p1}'s Drink #", value=0)
    d2 = col_b.number_input(f"{p2}'s Drink #", value=0)
    
    if st.button("🚀 Send Round", use_container_width=True):
        with st.spinner("Syncing..."):
            p_url = upload_image(img) if img else ""
            data.update({
                "Active_Round": "Yes", "Host": h_team,
                "Hidden1": d1, "Hidden2": d2, "Location": loc, "PhotoURL": p_url
            })
            save_data(data)
            st.rerun()

else:
    # ROUND IS ACTIVE - Team sees this screen
    guesser = "Team Willis" if data['Host'] == "Team Savarese" else "Team Savarese"
    host_p = ["Ralph", "Trisha"] if data['Host'] == "Team Savarese" else ["Charles", "Barbara"]
    
    st.subheader(f"🎯 {guesser}: Your Turn!")
    st.info(f"📍 {data['Host']} is at {data['Location']}")
    
    if data['PhotoURL']:
        st.image(data['PhotoURL'])
    
    st.write("Each player enters their guess:")
    g1 = st.number_input(f"Player 1: {host_p[0]}'s Drink", key="g1")
    g2 = st.number_input(f"Player 1: {host_p[1]}'s Drink", key="g2")
    g3 = st.number_input(f"Player 2: {host_p[0]}'s Drink", key="g3")
    g4 = st.number_input(f"Player 2: {host_p[1]}'s Drink", key="g4")

    if st.button("Submit Final Guesses", use_container_width=True):
        # Math
        correct = sum([g1==data['Hidden1'], g2==data['Hidden2'], g3==data['Hidden1'], g4==data['Hidden2']])
        swing = correct - (4 - correct)
        
        # Award Display
        if correct == 4: st.success("🍺 FULL PINT! (+4)")
        elif correct >= 2: st.warning("🍻 HALF FULL (+0)")
        else: st.error("💧 EMPTY PINT (- points)")
        
        # Update Scores and Close
        data[guesser] += swing
        data["Active_Round"] = "No"
        save_data(data)
        if swing > 0: st.balloons()
        time.sleep(2)
        st.rerun()
