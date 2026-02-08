import streamlit as st
import requests

st.set_page_config(page_title="Beverage Ballot", page_icon="🍹")

# --- INSTANT SYNC SETUP ---
GAME_ID = "willis-savarese-bb-2024"
DB_URL = f"https://kvstore.com/api/v1/items/{GAME_ID}"

def get_data():
    try:
        r = requests.get(DB_URL)
        if r.status_code == 200:
            return r.json()['value']
    except:
        pass
    return {"Savarese": 0, "Willis": 0, "Active_Round": "No", "Drink1": 0, "Drink2": 0, "Host": "", "Location": ""}

def save_data(data):
    requests.post(DB_URL, json={"value": data})

# --- APP UI ---
st.title("🍹 The Beverage Ballot")

if st.button("🔄 Check for New Moves", use_container_width=True):
    st.rerun()

with st.expander("📖 Official Rules"):
    st.markdown("""
    **Example Round:**
    * **Ralph** (Team Savarese) orders: Drink #2 and Drink #4.
    * **Charles** (Team Willis) guesses: #1 and #1. -> **Result:** Score 0 (Empty Pint).
    * **Barbara** (Team Willis) guesses: #2 and #4. -> **Result:** Score 2 (Full Pint).
    
    **The Awards:**
    * 🎯 **2 Correct:** Full Pint (+2 Points)
    * 🍺 **1 Correct:** Half Full Award (+0 Points, but bragging rights!)
    * 💧 **0 Correct:** Empty Pint (+0 Points)
    """)

data = get_data()

# --- SCOREBOARD ---
col1, col2 = st.columns(2)
col1.metric("Team Savarese", f"{data['Savarese']} Pints")
col2.metric("Team Willis", f"{data['Willis']} Pints")
st.divider()

# --- GAMEPLAY ---
if data['Active_Round'] == "No":
    st.subheader("📢 Start New Round")
    loc = st.text_input("Where are you?", placeholder="e.g. The Rusty Bucket")
    h_team = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    
    st.camera_input("Snap the Menu/Drinks")
    
    c1, c2 = st.columns(2)
    d1 = c1.number_input("Ralph's Drink #", value=0, step=1)
    d2 = c2.number_input("Trisha's Drink #", value=0, step=1)
    
    if st.button("🚀 Alert Other Team", use_container_width=True):
        data['Active_Round'] = "Yes"
        data['Host'] = h_team
        data['Drink1'] = d1
        data['Drink2'] = d2
        data['Location'] = loc
        save_data(data)
        st.success("Round sent! Tell them to hit 'Refresh'.")
        st.rerun()
else:
    guesser = "Team Willis" if data['Host'] == "Team Savarese" else "Team Savarese"
    st.subheader(f"🎯 {guesser}: Your Turn!")
    st.info(f"**{data['Host']}** is at **{data['Location']}**. What did they order?")
    
    g1 = st.number_input("Guess Ralph's Drink", value=0, step=1)
    g2 = st.number_input("Guess Trisha's Drink", value=0, step=1)
    
    if st.button("Submit Guesses", use_container_width=True):
        correct_count = 0
        if g1 == data['Drink1']: correct_count += 1
        if g2 == data['Drink2']: correct_count += 1
        
        # LOGIC: Only 2 correct gets points. 1 correct is just an award.
        if correct_count == 2:
            data[guesser] += 2
            st.balloons()
            st.success("🎯 PERFECT! Full Pint (+2 Points)")
        elif correct_count == 1:
            st.warning("🍺 1 Correct! You get the 'Half Full' Award (0 points).")
        else:
            st.error("💧 0 Correct. Empty Pint!")
            
        data['Active_Round'] = "No"
        save_data(data)
        # We don't rerun immediately so they can see their result message
        if st.button("Finish Turn"):
            st.rerun()

st.divider()
if st.button("Reset All Scores"):
    save_data({"Savarese": 0, "Willis": 0, "Active_Round": "No", "Drink1": 0, "Drink2": 0, "Host": "", "Location": ""})
    st.rerun()
