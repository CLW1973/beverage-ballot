import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- CONNECT TO YOUR SHEET ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    url = "https://docs.google.com/spreadsheets/d/15KCN_GqlcNdsotwEXwQkuQFMIEIlPKw5KORkHajzchg/edit?usp=sharing"
    return conn.read(spreadsheet=url, ttl=0) # ttl=0 means no caching, always fresh!

def update_data(df):
    url = "https://docs.google.com/spreadsheets/d/15KCN_GqlcNdsotwEXwQkuQFMIEIlPKw5KORkHajzchg/edit?usp=sharing"
    conn.update(spreadsheet=url, data=df)
    st.cache_data.clear()

# --- HEADER & REFRESH ---
st.title("🍹 The Beverage Ballot")

if st.button("🔄 Check for New Moves", use_container_width=True):
    st.rerun()

# --- INSTRUCTIONS ---
with st.expander("📖 How to Play"):
    st.markdown("""
    1. **The Order:** One team buys a round and enters the **Location** and the **Drink Numbers** from the menu.
    2. **The Alert:** Hit 'Alert Other Team'.
    3. **The Guess:** The other team hits 'Refresh' on their phone, sees the location, and guesses which drinks were ordered!
    4. **The Scoring:** * 🎯 **2 Correct:** Full Pint (+2)
        * 🍺 **1 Correct:** Half Pint (+1)
        * 💧 **0 Correct:** Just a Sip (+0)
    """)

df = get_data()
if df.empty:
    st.error("Sheet is empty! Make sure Row 1 has headers and Row 2 has 0s.")
    st.stop()

current = df.iloc[0]

# --- SCOREBOARD ---
col1, col2 = st.columns(2)
col1.metric("Team Savarese", f"{int(current['Savarese'])} Pints")
col2.metric("Team Willis", f"{int(current['Willis'])} Pints")

st.divider()

# --- GAMEPLAY ---
if current['Active_Round'] == "No":
    st.subheader("📢 Start New Round")
    location = st.text_input("Where are you?", placeholder="e.g. The Tipsy Turtle")
    h_team = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    
    st.camera_input("Snap the Menu (Optional)")
    
    c1, c2 = st.columns(2)
    d1 = c1.number_input("Drink #1", value=0, step=1)
    d2 = c2.number_input("Drink #2", value=0, step=1)
    
    if st.button("🚀 Alert Other Team", use_container_width=True):
        df.at[0, 'Active_Round'] = "Yes"
        df.at[0, 'Host'] = h_team
        df.at[0, 'Drink1'] = d1
        df.at[0, 'Drink2'] = d2
        df.at[0, 'Location'] = location
        update_data(df)
        st.success("Round sent! Willis/Savarese can now guess.")
        st.rerun()

else:
    guesser = "Team Willis" if current['Host'] == "Team Savarese" else "Team Savarese"
    st.subheader(f"🎯 {guesser}: Your Turn!")
    st.info(f"**{current['Host']}** is at **{current['Location']}**. What did they order?")
    
    g1 = st.number_input("Guess Drink #1", value=0, step=1)
    g2 = st.number_input("Guess Drink #2", value=0, step=1)
    
    if st.button("Submit Guesses", use_container_width=True):
        score = 0
        if g1 == current['Drink1']: score += 1
        if g2 == current['Drink2']: score += 1
        
        df.at[0, guesser] += score
        df.at[0, 'Active_Round'] = "No"
        update_data(df)
        if score > 0: st.balloons()
        st.rerun()

st.divider()
if st.button("Clear Scores / Reset Game"):
    df.at[0, 'Savarese'] = 0
    df.at[0, 'Willis'] = 0
    df.at[0, 'Active_Round'] = "No"
    update_data(df)
    st.rerun()
