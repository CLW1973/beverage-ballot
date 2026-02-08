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

st.title("🍹 Beverage Ballot")

if st.button("🔄 Check for New Moves", use_container_width=True):
    st.rerun()

# --- UPDATED INSTRUCTIONS ---
with st.expander("📖 Official Plus/Minus Rules"):
    st.markdown("""
    **Scoring Logic (4 Total Guesses per Round):**
    * ✅ Each Correct: **+1 Point**
    * ❌ Each Wrong: **-1 Point**
    * 📈 **Swing Range:** -4 to +4 Points
    
    **Pint Awards:**
    * 🎯 **100% Right (4/4):** FULL PINT
    * 🍺 **50-75% Right (2-3/4):** HALF FULL
    * 💧 **0-25% Right (0-1/4):** EMPTY PINT
    """)

data = get_data()

# --- SCOREBOARD ---
col1, col2 = st.columns(2)
col1.metric("Team Savarese", f"{data['Savarese']} pts")
col2.metric("Team Willis", f"{data['Willis']} pts")
st.divider()

if data['Active_Round'] == "No":
    st.subheader("📢 Start New Round")
    loc = st.text_input("Where are you?", placeholder="Location Name")
    h_team = st.radio("Who is ordering?", ["Team Savarese", "Team Willis"], horizontal=True)
    
    st.camera_input("Snap the Menu")
    
    c1, c2 = st.columns(2)
    d1 = c1.number_input("Ralph's Drink #", value=0, step=1)
    d2 = c2.number_input("Trisha's Drink #", value=0, step=1)
    
    if st.button("🚀 Alert Other Team", use_container_width=True):
        data.update({"Active_Round": "Yes", "Host": h_team, "Drink1": d1, "Drink2": d2, "Location": loc})
        save_data(data)
        st.success("Round sent! Other team: Hit 'Check for New Moves'.")
        st.rerun()
else:
    guesser = "Team Willis" if data['Host'] == "Team Savarese" else "Team Savarese"
    st.subheader(f"🎯 {guesser}: Your Turn!")
    st.info(f"**{data['Host']}** is at **{data['Location']}**. Tally your guesses!")
    
    # --- AUTOMATED SCORING ENGINE ---
    num_right = st.slider("Total CORRECT (out of 4 guesses)", 0, 4, 0)
    num_wrong = 4 - num_right
    round_swing = num_right - num_wrong
    
    if num_right == 4:
        award = "🍺 FULL PINT! (+4)"
        status = "success"
    elif num_right >= 2:
        award = "🍻 HALF FULL"
        status = "warning"
    else:
        award = "💧 EMPTY PINT"
        status = "error"

    st.markdown(f"### Result: {award}")
    st.write(f"Points: {num_right} Right minus {num_wrong} Wrong = **{round_swing}**")

    if status == "success": st.success("Perfect Round!")
    elif status == "warning": st.warning("Not bad!")
    else: st.error("Ouch, rough round.")

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
