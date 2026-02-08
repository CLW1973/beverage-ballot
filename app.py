import streamlit as st
import requests

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- ROBUST SYNC SETUP ---
# Using a slightly different ID to ensure a fresh start
GAME_ID = "willis-savarese-bb-final-2024"
DB_URL = f"https://kvstore.com/api/v1/items/{GAME_ID}"

def get_data():
    try:
        r = requests.get(DB_URL, timeout=5)
        if r.status_code == 200:
            return r.json()['value']
    except:
        pass
    return {"Savarese": 0, "Willis": 0, "Active_Round": "No", "Drink1": 0, "Drink2": 0, "Host": "", "Location": ""}

def save_data(data):
    try:
        requests.post(DB_URL, json={"value": data}, timeout=5)
    except:
        st.error("Connection error! Data might not have saved.")

st.title("🍹 Beverage Ballot")

# --- REFRESH LOGIC ---
if st.button("🔄 Check for New Moves", use_container_width=True):
    st.rerun()

data = get_data()

# --- SCOREBOARD ---
col1, col2 = st.columns(2)
col1.metric("Team Savarese", f"{data['Savarese']} pts")
col2.metric("Team Willis", f"{data['Willis']} pts")
st.divider()

# --- DYNAMIC LABELS ---
# Define names based on who is playing
savarese_players = ["Ralph", "Trisha"]
willis_players = ["Charles", "Barbara"]

if data['Active_Round'] == "No":
    st.subheader("📢 Start New Round")
    loc = st.text_input("Where are you?", placeholder="Location Name")
    h_team = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    
    # Set labels based on the radio selection
    p1, p2 = (savarese_players) if h_team == "Team Savarese" else (willis_players)
    
    st.camera_input(f"Snap {h_team}'s Menu")
    
    c1, c2 = st.columns(2)
    d1 = c1.number_input(f"{p1}'s Drink #", value=0, step=1)
    d2 = c2.number_input(f"{p2}'s Drink #", value=0, step=1)
    
    if st.button("🚀 Alert Other Team", use_container_width=True):
        data.update({
            "Active_Round": "Yes", 
            "Host": h_team, 
            "Drink1": d1, 
            "Drink2": d2, 
            "Location": loc
        })
        save_data(data)
        st.success("Round sent! Tell the other team to hit Refresh.")
        st.rerun()

else:
    # A round is active! Determine who is guessing
    guesser = "Team Willis" if data['Host'] == "Team Savarese" else "Team Savarese"
    hosting_players = savarese_players if data['Host'] == "Team Savarese" else willis_players
    
    st.subheader(f"🎯 {guesser}: Your Turn!")
    st.info(f"**{data['Host']}** is at **{data['Location']}**. Guess what they ordered!")
    
    st.write(f"What did **{hosting_players[0]}** and **{hosting_players[1]}** order?")
    
    # --- SCORING ---
    num_right = st.slider("Total CORRECT (out of 4 guesses)", 0, 4, 0)
    num_wrong = 4 - num_right
    round_swing = num_right - num_wrong
    
    if num_right == 4: award = "🍺 FULL PINT! (+4)"
    elif num_right >= 2: award = "🍻 HALF FULL"
    else: award = "💧 EMPTY PINT"

    st.markdown(f"### Result: {award}")
    
    if st.button(f"Confirm {round_swing} pts for {guesser}", use_container_width=True):
        data[guesser] += round_swing
        data['Active_Round'] = "No"
        save_data(data)
        if round_swing > 0: st.balloons()
        st.rerun()

st.divider()
if st.button("Reset All Scores"):
    save_data({"Savarese": 0, "Willis": 0, "Active_Round": "No", "Drink1": 0, "Drink2": 0, "Host": "", "Location": ""})
    st.rerun()
