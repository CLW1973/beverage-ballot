import streamlit as st
import requests
import time

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- REFRESH DATABASE LOGIC ---
# Using a unique ID to clear any old stuck data
GAME_ID = "willis-savarese-v9-final"
DB_URL = f"https://kvstore.com/api/v1/items/{GAME_ID}"

def get_data():
    try:
        r = requests.get(DB_URL, timeout=5)
        if r.status_code == 200:
            return r.json()['value']
    except:
        pass
    # Initial clean state
    return {"Savarese": 0, "Willis": 0, "Active_Round": "No", "Hidden1": 0, "Hidden2": 0, "Host": "", "Location": "", "PhotoURL": ""}

def save_data(data):
    try:
        requests.post(DB_URL, json={"value": data}, timeout=5)
    except:
        st.error("Database Connection Failed!")

# --- CLOUDINARY UPLOAD ---
def upload_image(image_file):
    try:
        url = f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/image/upload"
        files = {"file": image_file}
        payload = {"upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET']}
        response = requests.post(url, files=files, data=payload)
        return response.json().get("secure_url")
    except:
        st.error("Photo Upload Failed! Check your Cloudinary Secrets.")
        return None

# Load the latest data
data = get_data()

st.title("🍹 Beverage Ballot")

# --- LIVE STATUS BAR ---
if data['Active_Round'] == "Yes":
    st.success(f"🔴 ROUND ACTIVE: {data['Host']} is at {data['Location']}")
else:
    st.info("⚪ Waiting for a team to start...")

if st.button("🔄 Check for New Moves", use_container_width=True):
    st.rerun()

# --- SCOREBOARD ---
c1, c2 = st.columns(2)
c1.metric("Team Savarese", f"{data['Savarese']} pts")
c2.metric("Team Willis", f"{data['Willis']} pts")
st.divider()

savarese_players = ["Ralph", "Trisha"]
willis_players = ["Charles", "Barbara"]

# --- GAME LOGIC ---
if data['Active_Round'] == "No":
    st.subheader("📢 Start New Round")
    loc = st.text_input("Where are you?", placeholder="e.g. The Rusty Bucket")
    h_team = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    
    img_file = st.camera_input("Take Photo of Menu/Drinks")
    
    # Names of the people ordering
    p1, p2 = (savarese_players) if h_team == "Team Savarese" else (willis_players)
    
    col_a, col_b = st.columns(2)
    d1 = col_a.number_input(f"{p1}'s Drink #", value=0, step=1)
    d2 = col_b.number_input(f"{p2}'s Drink #", value=0, step=1)
    
    if st.button("🚀 Alert Other Team", use_container_width=True):
        with st.spinner("Uploading and Alerting..."):
            photo_url = upload_image(img_file) if img_file else ""
            
            # Pack the data to send
            updated_data = {
                "Savarese": data['Savarese'],
                "Willis": data['Willis'],
                "Active_Round": "Yes",
                "Host": h_team,
                "Hidden1": d1,
                "Hidden2": d2,
                "Location": loc,
                "PhotoURL": photo_url
            }
            save_data(updated_data)
            st.success("Round LIVE! Tell the others to refresh.")
            time.sleep(1)
            st.rerun()

else:
    # A ROUND IS ACTIVE - This is what Team Willis should see
    guesser_team = "Team Willis" if data['Host'] == "Team Savarese" else "Team Savarese"
    host_players = savarese_players if data['Host'] == "Team Savarese" else willis_players
    
    st.subheader(f"🎯 {guesser_team}: Make Your Guesses!")
    
    if data['PhotoURL']:
        st.image(data['PhotoURL'], caption=f"The menu at {data['Location']}")
    else:
        st.warning(f"No photo uploaded, but they are at {data['Location']}")
    
    st.write(f"Enter 2 guesses for each player (4 total):")
    g1 = st.number_input(f"Guess 1: {host_players[0]}'s Drink", key="g1")
    g2 = st.number_input(f"Guess 2: {host_players[1]}'s Drink", key="g2")
    g3 = st.number_input(f"Guess 3: {host_players[0]}'s Drink", key="g3")
    g4 = st.number_input(f"Guess 4: {host_players[1]}'s Drink", key="g4")

    if st.button("Submit Final Guesses", use_container_width=True):
        # Comparison logic
        correct = 0
        if g1 == data['Hidden1']: correct += 1
        if g2 == data['Hidden2']: correct += 1
        if g3 == data['Hidden1']: correct += 1
        if g4 == data['Hidden2']: correct += 1
        
        swing = correct - (4 - correct)
        
        # Update and Close Round
        data[guesser_team] += swing
        data['Active_Round'] = "No"
        save_data(data)
        
        st.write(f"Correct drinks were: {data['Hidden1']} and {data['Hidden2']}")
        if swing > 0: st.balloons()
        st.rerun()

st.divider()
if st.button("Reset Scores & Game"):
    save_data({"Savarese": 0, "Willis": 0, "Active_Round": "No", "Hidden1": 0, "Hidden2": 0, "Host": "", "Location": "", "PhotoURL": ""})
    st.rerun()
