import streamlit as st
import requests
import time

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- DATABASE (Public & Fast) ---
# Using a fresh, unique key to avoid conflicts
DB_KEY = "willis_savarese_final_v12"
DB_URL = f"https://kvstore.com/api/v1/items/{DB_KEY}"

def get_data():
    try:
        r = requests.get(DB_URL, timeout=5)
        if r.status_code == 200:
            return r.json()['value']
    except Exception as e:
        st.sidebar.error(f"Sync Error: {e}")
    return {"Savarese": 0, "Willis": 0, "Active_Round": "No", "Hidden1": 0, "Hidden2": 0, "Host": "", "Location": "", "PhotoURL": ""}

def save_data(payload):
    try:
        r = requests.post(DB_URL, json={"value": payload}, timeout=5)
        if r.status_code == 200 or r.status_code == 201:
            return True
        else:
            st.error(f"Database rejected save: {r.status_code}")
            return False
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        return False

# --- PHOTO UPLOAD ---
def upload_image(image_file):
    try:
        # Check if secrets exist
        if "CLOUDINARY_CLOUD_NAME" not in st.secrets:
            st.error("Secrets not found in Streamlit Dashboard!")
            return None
            
        url = f"https://api.cloudinary.com/v1_1/{st.secrets['CLOUDINARY_CLOUD_NAME']}/image/upload"
        files = {"file": image_file}
        payload = {"upload_preset": st.secrets['CLOUDINARY_UPLOAD_PRESET']}
        response = requests.post(url, files=files, data=payload)
        return response.json().get("secure_url")
    except Exception as e:
        st.error(f"Photo Upload Failed: {e}")
        return None

# Load State
data = get_data()

st.title("🍹 Beverage Ballot")

# Sidebar for Resetting
with st.sidebar:
    if st.button("🚨 Emergency Reset Game"):
        save_data({"Savarese": 0, "Willis": 0, "Active_Round": "No", "Hidden1": 0, "Hidden2": 0, "Host": "", "Location": "", "PhotoURL": ""})
        st.rerun()

# Scoreboard
c1, c2 = st.columns(2)
c1.metric("Team Savarese", f"{data.get('Savarese', 0)} pts")
c2.metric("Team Willis", f"{data.get('Willis', 0)} pts")

# The Refresh Button (Crucial for Team Willis)
if st.button("🔄 REFRESH / CHECK FOR MOVE", type="primary", use_container_width=True):
    st.rerun()

st.divider()

# --- THE LOGIC ---
if data.get('Active_Round') == "No":
    st.header("📢 Start a Round")
    h_team = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    loc = st.text_input("Where are you?", placeholder="Bar Name...")
    
    img = st.camera_input("Take photo of the menu/drinks")
    
    p_names = ("Ralph", "Trisha") if h_team == "Team Savarese" else ("Charles", "Barbara")
    col_a, col_b = st.columns(2)
    d1 = col_a.number_input(f"{p_names[0]}'s #", value=0, step=1)
    d2 = col_b.number_input(f"{p_names[1]}'s #", value=0, step=1)
    
    if st.button("🚀 SEND ROUND", use_container_width=True):
        if d1 == 0 and d2 == 0:
            st.warning("Enter drink numbers before sending!")
        else:
            with st.spinner("Uploading and Syncing..."):
                p_url = upload_image(img) if img else ""
                
                # Prepare data
                new_state = {
                    "Savarese": data.get('Savarese', 0),
                    "Willis": data.get('Willis', 0),
                    "Active_Round": "Yes",
                    "Host": h_team,
                    "Hidden1": d1,
                    "Hidden2": d2,
                    "Location": loc,
                    "PhotoURL": p_url
                }
                
                if save_data(new_state):
                    st.success("SUCCESS! Database updated.")
                    time.sleep(1)
                    st.rerun()

else:
    # A ROUND IS ACTIVE
    guesser_team = "Team Willis" if data['Host'] == "Team Savarese" else "Team Savarese"
    host_p = ["Ralph", "Trisha"] if data['Host'] == "Team Savarese" else ["Charles", "Barbara"]
    
    st.header(f"🎯 {guesser_team}: GUESS!")
    st.info(f"{data['Host']} is at {data['Location']}")
    
    if data.get('PhotoURL'):
        st.image(data['PhotoURL'], caption="Study the photo!")
    
    st.write("Enter 2 guesses for each person:")
    g1 = st.number_input(f"Guess 1 for {host_p[0]}", key="g1")
    g2 = st.number_input(f"Guess 2 for {host_p[1]}", key="g2")
    g3 = st.number_input(f"Guess 3 for {host_p[0]}", key="g3")
    g4 = st.number_input(f"Guess 4 for {host_p[1]}", key="g4")

    if st.button("✅ SUBMIT FINAL GUESSES", use_container_width=True):
        # Calculate
        correct = sum([g1 == data['Hidden1'], g2 == data['Hidden2'], g3 == data['Hidden1'], g4 == data['Hidden2']])
        swing = correct - (4 - correct)
        
        # Update Scores
        data[guesser_team] += swing
        data['Active_Round'] = "No"
        
        if save_data(data):
            st.write(f"Correct numbers were {data['Hidden1']} and {data['Hidden2']}")
            if swing > 0: st.balloons()
            time.sleep(3)
            st.rerun()
