import streamlit as st
import requests
import time

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- INSTANT DATABASE (No Setup Required) ---
# This uses a public storage bin specifically for your game
GAME_URL = "https://jsonbin.org/willis-savarese-game-2024"

def get_data():
    try:
        r = requests.get(GAME_URL, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {"Savarese": 0, "Willis": 0, "Active_Round": "No", "Hidden1": 0, "Hidden2": 0, "Host": "", "Location": "", "PhotoURL": ""}

def save_data(data):
    try:
        requests.post(GAME_URL, json=data, timeout=5)
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
        st.error("Cloudinary Error: Check your Secrets!")
        return None

data = get_data()

st.title("🍹 Beverage Ballot")

# --- SIDEBAR RULES ---
with st.sidebar:
    st.header("📖 Instructions")
    st.write("**Scoring:**")
    st.write("✅ Each Correct: +1")
    st.write("❌ Each Wrong: -1")
    st.write("**Awards:**")
    st.success("🍺 4/4: Full Pint")
    st.warning("🍻 2/3: Half Full")
    st.error("💧 0/1: Empty Pint")
    if st.button("Reset Game"):
        save_data({"Savarese": 0, "Willis": 0, "Active_Round": "No", "Hidden1": 0, "Hidden2": 0, "Host": "", "Location": "", "PhotoURL": ""})
        st.rerun()

# Refresh Button
if st.button("🔄 Check for Moves", use_container_width=True):
    st.rerun()

# --- SCOREBOARD ---
c1, c2 = st.columns(2)
c1.metric("Team Savarese", f"{data.get('Savarese')} pts")
c2.metric("Team Willis", f"{data.get('Willis')} pts")
st.divider()

savarese_players = ["Ralph", "Trisha"]
willis_players = ["Charles", "Barbara"]

if data.get('Active_Round') == "No":
    st.subheader("📢 Start Round")
    loc = st.text_input("Location?")
    h_team = st.radio("Ordering Team:", ["Team Savarese", "Team Willis"], horizontal=True)
    
    img = st.camera_input("Snap Menu")
    
    p1, p2 = (savarese_players) if h_team == "Team Savarese" else (willis_players)
    col_a, col_b = st.columns(2)
    d1 = col_a.number_input(f"{p1}'s Drink #", value=0)
    d2 = col_b.number_input(f"{p2}'s Drink #", value=0)
    
    if st.button("🚀 Send to Other Team", use_container_width=True):
        with st.spinner("Uploading..."):
            p_url = upload_image(img) if img else ""
            data.update({
                "Active_Round": "Yes", "Host": h_team,
                "Hidden1": d1, "Hidden2": d2, "Location": loc, "PhotoURL": p_url
            })
            if save_data(data):
                st.success("Live! Other team must refresh.")
                st.rerun()

else:
    # --- GUESSING SCREEN ---
    guesser = "Team Willis" if data['Host'] == "Team Savarese" else "Team Savarese"
    host_p = savarese_players if data['Host'] == "Team Savarese" else willis_players
    
    st.subheader(f"🎯 {guesser}: Your Guess!")
    st.info(f"📍 {data['Host']} is at {data['Location']}")
    
    if data.get('PhotoURL'):
        st.image(data['PhotoURL'])
    
    st.write("2 guesses per person (4 total):")
    g1 = st.number_input(f"Guess A ({host_p[0]})", key="g1")
    g2 = st.number_input(f"Guess B ({host_p[1]})", key="g2")
    g3 = st.number_input(f"Guess C ({host_p[0]})", key="g3")
    g4 = st.number_input(f"Guess D ({host_p[1]})", key="g4")

    if st.button("Submit Results", use_container_width=True):
        correct = sum([g1==data['Hidden1'], g2==data['Hidden2'], g3==data['Hidden1'], g4==data['Hidden2']])
        swing = correct - (4 - correct)
        
        # Display Result
        if correct == 4: st.success("🍺 FULL PINT!")
        elif correct >= 2: st.warning("🍻 HALF FULL")
        else: st.error("💧 EMPTY PINT")
        
        data[guesser] += swing
        data["Active_Round"] = "No"
        save_data(data)
        if swing > 0: st.balloons()
        time.sleep(2)
        st.rerun()
