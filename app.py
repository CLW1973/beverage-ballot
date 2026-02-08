import streamlit as st
import requests
import time

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- DATABASE SETUP ---
# I've changed the ID again to ensure a 100% clean slate
GAME_ID = "willis-savarese-v10-sync"
DB_URL = f"https://kvstore.com/api/v1/items/{GAME_ID}"

def get_data():
    try:
        r = requests.get(DB_URL, timeout=5)
        if r.status_code == 200:
            return r.json()['value']
    except:
        pass
    return {"Savarese": 0, "Willis": 0, "Active_Round": "No", "Hidden1": 0, "Hidden2": 0, "Host": "", "Location": "", "PhotoURL": ""}

def save_data(new_data):
    try:
        # We fetch current scores first so we don't accidentally reset them to 0
        current = get_data()
        new_data["Savarese"] = current.get("Savarese", 0)
        new_data["Willis"] = current.get("Willis", 0)
        requests.post(DB_URL, json={"value": new_data}, timeout=5)
        return True
    except:
        return False

# --- CLOUDINARY UPLOAD ---
def upload_image(image_file):
    try:
        url = f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/image/upload"
        files = {"file": image_file}
        payload = {"upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET']}
        response = requests.post(url, files=files, data=payload)
        return response.json().get("secure_url")
    except:
        return None

# Load the latest data
data = get_data()

st.title("🍹 Beverage Ballot")

# --- MANUAL REFRESH ---
if st.button("🔄 Refresh Game State", use_container_width=True):
    st.rerun()

# --- SCOREBOARD ---
c1, c2 = st.columns(2)
c1.metric("Team Savarese", f"{data.get('Savarese', 0)} pts")
c2.metric("Team Willis", f"{data.get('Willis', 0)} pts")
st.divider()

savarese_players = ["Ralph", "Trisha"]
willis_players = ["Charles", "Barbara"]

# --- ROUND LOGIC ---
if data.get('Active_Round') == "No":
    st.subheader("📢 Start New Round")
    loc = st.text_input("Where are you?")
    h_team = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    
    img_file = st.camera_input("Snap the Menu/Drinks")
    
    p1, p2 = (savarese_players) if h_team == "Team Savarese" else (willis_players)
    col_a, col_b = st.columns(2)
    d1 = col_a.number_input(f"{p1}'s Drink #", value=0)
    d2 = col_b.number_input(f"{p2}'s Drink #", value=0)
    
    if st.button("🚀 Alert Other Team", use_container_width=True):
        with st.spinner("Syncing..."):
            p_url = upload_image(img_file) if img_file else ""
            success = save_data({
                "Active_Round": "Yes",
                "Host": h_team,
                "Hidden1": d1,
                "Hidden2": d2,
                "Location": loc,
                "PhotoURL": p_url
            })
            if success:
                st.success("Sent! Other team must hit 'Refresh'.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Failed to sync. Try again.")

else:
    # --- GUESSING SCREEN ---
    guesser_team = "Team Willis" if data['Host'] == "Team Savarese" else "Team Savarese"
    host_players = savarese_players if data['Host'] == "Team Savarese" else willis_players
    
    st.subheader(f"🎯 {guesser_team}: Guessing Time!")
    st.info(f"**{data['Host']}** is at **{data['Location']}**")
    
    if data.get('PhotoURL'):
        st.image(data['PhotoURL'])
    
    st.write(f"Enter 4 total guesses (2 per person):")
    g1 = st.number_input(f"Guess 1: {host_players[0]}", key="g1")
    g2 = st.number_input(f"Guess 2: {host_players[1]}", key="g2")
    g3 = st.number_input(f"Guess 3: {host_players[0]}", key="g3")
    g4 = st.number_input(f"Guess 4: {host_players[1]}", key="g4")

    if st.button("Submit Guesses", use_container_width=True):
        # Math: +1 for right, -1 for wrong
        correct = sum([g1 == data['Hidden1'], g2 == data['Hidden2'], g3 == data['Hidden1'], g4 == data['Hidden2']])
        swing = correct - (4 - correct)
        
        # Awards
        if correct == 4: st.balloons()
        
        # Save Score & End Round
        new_scores = get_data() # Get latest scores before adding
        new_scores[guesser_team] += swing
        new_scores["Active_Round"] = "No"
        requests.post(DB_URL, json={"value": new_scores})
        st.rerun()

# --- DEBUG & RESET ---
st.divider()
with st.expander("🛠️ Admin Tools"):
    st.write("Current Database State:", data)
    if st.button("Reset Everything"):
        requests.post(DB_URL, json={"value": {"Savarese": 0, "Willis": 0, "Active_Round": "No", "Hidden1": 0, "Hidden2": 0, "Host": "", "Location": "", "PhotoURL": ""}})
        st.rerun()
