import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Beverage Ballot", layout="centered")

# --- CONNECT TO YOUR SHEET ---
# This looks for the link you provided in the background
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    return conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/15KCN_GqlcNdsotwEXwQkuQFMIEIlPKw5KORkHajzchg/edit?usp=sharing", ttl=2)

def update_data(df):
    conn.update(spreadsheet="https://docs.google.com/spreadsheets/d/15KCN_GqlcNdsotwEXwQkuQFMIEIlPKw5KORkHajzchg/edit?usp=sharing", data=df)
    st.cache_data.clear()

# --- APP LOGIC ---
st.title("🍹 The Synced Beverage Ballot")
df = get_data()

# Ensure we have a row for scores
if df.empty:
    df = pd.DataFrame([{"Savarese": 0, "Willis": 0, "Active_Round": "No", "Photo": "", "Target1": 0.0, "Target2": 0.0, "Host": ""}])
    update_data(df)

current = df.iloc[0]

# --- SCOREBOARD ---
col1, col2 = st.columns(2)
col1.metric("Team Savarese", f"{int(current['Savarese'])} Pints")
col2.metric("Team Willis", f"{int(current['Willis'])} Pints")

st.divider()

# --- GAMEPLAY ---
if current['Active_Round'] == "No":
    st.subheader("📢 Start New Round")
    h_team = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    st.camera_input("Take a Photo (Appears for other team)")
    
    t1 = st.number_input("Enter Price/Calorie 1", value=0.0)
    t2 = st.number_input("Enter Price/Calorie 2", value=0.0)
    
    if st.button("🚀 Alert Other Team"):
        df.at[0, 'Active_Round'] = "Yes"
        df.at[0, 'Host'] = h_team
        df.at[0, 'Target1'] = t1
        df.at[0, 'Target2'] = t2
        update_data(df)
        st.success("Round started! The other team's app will update now.")
        st.rerun()

else:
    guesser = "Team Willis" if current['Host'] == "Team Savarese" else "Team Savarese"
    st.subheader(f"🎯 {guesser}: Your Turn!")
    st.info(f"{current['Host']} has posted a drink! Make your guesses.")
    
    g1 = st.number_input("Guess 1", value=0.0)
    g2 = st.number_input("Guess 2", value=0.0)
    
    if st.button("Submit Guesses"):
        # Simple scoring
        score = 0
        if abs(g1 - current['Target1']) < 0.1: score += 1
        if abs(g2 - current['Target2']) < 0.1: score += 1
        
        # Update Scoreboard
        df.at[0, guesser] += score
        df.at[0, 'Active_Round'] = "No"
        update_data(df)
        st.balloons()
        st.rerun()

if st.button("Reset Game"):
    df.at[0, 'Savarese'] = 0
    df.at[0, 'Willis'] = 0
    df.at[0, 'Active_Round'] = "No"
    update_data(df)
    st.rerun()
