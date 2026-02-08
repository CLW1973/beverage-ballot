import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- INSTANT SYNC SETUP (KVStore) ---
# This acts as our shared database without the Google Sheets headache
GAME_ID = "willis-savarese-bb-2024"
DB_URL = f"https://kvstore.com/api/v1/items/{GAME_ID}"

def get_data():
    try:
        r = requests.get(DB_URL)
        if r.status_code == 200:
            return r.json()['value']
        else:
            # Default starting state
            return {"Savarese": 0, "Willis": 0, "Active_Round": "No", "Drink1": 0, "Drink2": 0, "Host": "", "Location": ""}
    except:
        return {"Savarese": 0, "Willis": 0, "Active_Round": "No", "Drink1": 0, "Drink2": 0, "Host": "", "Location": ""}

def save_data(data):
    requests.post(DB_URL, json={"value": data})

# --- APP UI ---
st.title("🍹 The Beverage Ballot")

if st.button("🔄 Check for New Moves", use_container_width=True):
    st.rerun()

with st.expander("📖 How to Play"):
    st.write("1. One team buys, enters location and drink numbers.")
    st.write("2. Other team hits Refresh, then guesses.")
    st.write("3. 2 Correct = 2 Pints | 1 Correct = 1 Pint.")

data = get_data()

# --- SCOREBOARD ---
col1, col2 = st.columns(2)
col1.metric("Team Savarese", f"{data['Savarese']} Pints")
col2.metric("Team Willis", f"{data['Willis']} Pints")
st.divider()

# --- GAMEPLAY ---
if data['Active_Round'] == "No":
    st.subheader("📢 Start New Round")
    loc = st.text_input("Where are you?")
    h_team = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    
    c1, c2 = st.columns(2)
    d1 = c1.number_input("Drink #1", value=0, step=1)
    d2 = c2.number_input("Drink #2", value=0, step=1)
    
    if st.button("🚀 Alert Other Team", use_container_width=True):
        data['Active_Round'] = "Yes"
        data['Host'] = h_team
        data['Drink1'] = d1
        data['Drink2'] = d2
        data['Location'] = loc
        save_data(data)
        st.success("Round sent!")
        st.rerun()
else:
    guesser = "Team Willis" if data['Host'] == "Team Savarese" else "Team Savarese"
    st.subheader(f"🎯 {guesser}: Your Turn!")
    st.info(f"**{data['Host']}** is at **{data['Location']}**. Guess the drinks!")
    
    g1 = st.number_input("Guess Drink #1", value=0, step=1)
    g2 = st.number_input("Guess Drink #2", value=0, step=1)
    
    if st.button("Submit Guesses", use_container_width=True):
        score = 0
        if g1 == data['Drink1']: score += 1
        if g2 == data['Drink2']: score += 1
        
        data[guesser] += score
        data['Active_Round'] = "No"
        save_data(data)
        if score > 0: st.balloons()
        st.rerun()

st.divider()
if st.button("Clear Scores"):
    save_data({"Savarese": 0, "Willis": 0, "Active_Round": "No", "Drink1": 0, "Drink2": 0, "Host": "", "Location": ""})
    st.rerun()
