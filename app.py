import streamlit as st
import time
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(
    page_title="TDResQ - לוח בקרה",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling and RTL
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700&display=swap');
    
    html, body, [class*="st-"] {
        font-family: 'Rubik', sans-serif;
    }
    
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* Make the app RTL */
    body {
        direction: rtl;
    }
    
    /* Center the title */
    h1 {
        text-align: center;
        color: #4ecdc4;
        font-weight: 700;
    }
    
    .stMarkdown p {
        text-align: center;
    }
    
    /* Style for metric labels */
    .st-emotion-cache-1g8s24k {
        font-size: 1.1rem;
        color: #aab8c2;
        text-align: center;
    }
    
    /* Style for metric values */
    .st-emotion-cache-1s60f5k {
        font-size: 2rem;
        font-weight: 600;
        color: #ffffff;
        text-align: center;
    }
    
    /* Custom button styling */
    div.stButton > button:first-child {
        background-color: #4ecdc4;
        color: #ffffff;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover {
        background-color: #44a08d;
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(78, 205, 196, 0.2);
    }
    
    div.stButton > button:focus {
        background-color: #44a08d;
        box-shadow: 0 10px 20px rgba(78, 205, 196, 0.2);
        border-color: #4ecdc4;
        color: #ffffff;
    }
    
    /* This targets the container of the buttons and applies danger style to the last one */
    .st-emotion-cache-17k55r0 .stButton:last-of-type button {
         background-color: #ff6b6b;
    }
    .st-emotion-cache-17k55r0 .stButton:last-of-type button:hover {
         background-color: #ff5252;
         box-shadow: 0 10px 20px rgba(255, 107, 107, 0.2);
    }

</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'system_status' not in st.session_state:
    st.session_state.system_status = "idle"  # idle, scanning, selection, locating, located
if 'scan_progress' not in st.session_state:
    st.session_state.scan_progress = 0
if 'location_progress' not in st.session_state:
    st.session_state.location_progress = 0
if 'scan_phase' not in st.session_state:
    st.session_state.scan_phase = "מוכן"
if 'network' not in st.session_state:
    st.session_state.network = '4G'
if 'battery' not in st.session_state:
    st.session_state.battery = 100
if 'log' not in st.session_state:
    st.session_state.log = ["[מערכת] אתחול... כל המערכות תקינות."]
if 'location_found' not in st.session_state:
    st.session_state.location_found = None
if 'last_battery_warning' not in st.session_state:
    st.session_state.last_battery_warning = 101
if 'detected_imsis' not in st.session_state:
    st.session_state.detected_imsis = []
if 'selected_imsi' not in st.session_state:
    st.session_state.selected_imsi = None
if 'df_signal' not in st.session_state:
    st.session_state.df_signal = 0

def add_log(message):
    time_str = time.strftime("%H:%M:%S")
    st.session_state.log.insert(0, f"[{time_str}] {message}")
    if len(st.session_state.log) > 20: # Keep log size manageable
        st.session_state.log.pop()

# --- HEADER ---
st.title("TDResQ - מערכת איתור נעדרים")
st.markdown("<p class='subtitle'>דשבורד מגיבים ראשונים - טכנולוגיית BTS מתקדמת לאיתור ואימות</p>", unsafe_allow_html=True)
st.markdown("---")

# --- MAIN DASHBOARD ---
col1, col2 = st.columns((1, 2))

with col1:
    st.header("לוח בקרה")
    
    # --- Control Buttons ---
    action_in_progress = st.session_state.system_status in ["scanning", "locating"]
    scan_button_text = "⏹️ הפסק פעולה" if action_in_progress else "🔍 התחל סריקה חדשה"
    
    if st.button(scan_button_text):
        if action_in_progress:
            st.session_state.system_status = "idle"
            add_log("⏹️ הפעולה הופסקה ידנית.")
        else:  # Was idle, located, or selection
            st.session_state.system_status = "scanning"
            add_log("🔍 סריקה חדשה החלה.")
            # Reset states for a new scan
            st.session_state.location_found = None
            st.session_state.scan_progress = 0
            st.session_state.location_progress = 0
            st.session_state.scan_phase = "מאתחל סריקה..."
            st.session_state.detected_imsis = []
            st.session_state.selected_imsi = None
            
    if st.button(f"📶 החלף רשת (נוכחית: {st.session_state.network})", disabled=(st.session_state.system_status != 'idle')):
        st.session_state.network = '2G' if st.session_state.network == '4G' else '4G'
        add_log(f"🔄 רשת הוחלפה ל-{st.session_state.network}")
    
    if st.button("🛑 עצירת חירום"):
        st.session_state.system_status = "idle"
        st.session_state.scan_progress = 0
        st.session_state.location_progress = 0
        st.session_state.detected_imsis = []
        st.session_state.selected_imsi = None
        st.session_state.df_signal = 0
        add_log("🚨 התקבלה פקודת עצירת חירום! כל הפעולות הופסקו.")
        st.error("עצירת חירום הופעלה!")

    # --- IMSI Selection ---
    if st.session_state.system_status == 'selection':
        st.markdown("---")
        st.subheader("בחירת יעד לאיתור")
        if not st.session_state.detected_imsis:
            st.warning("לא זוהו מכשירים בסריקה.")
        else:
            st.session_state.selected_imsi = st.selectbox(
                "בחר IMSI למעקב DF:",
                options=st.session_state.detected_imsis,
                index=0
            )
            if st.button("📍 אתר IMSI נבחר"):
                if st.session_state.selected_imsi:
                    st.session_state.system_status = "locating"
                    st.session_state.location_progress = 0
                    st.session_state.network = '2G'
                    add_log("🔄 רשת הועברה ל-2G לצורך איתור DF.")
                    add_log(f"📞 מבצע 'שיחה שקטה' ל-IMSI: {st.session_state.selected_imsi}")
                else:
                    st.error("יש לבחור IMSI תחילה.")

    # --- Status Metrics ---
    st.markdown("---")
    st.subheader("מדדי מערכת")
    
    m1, m2 = st.columns(2)
    with m1:
        st.metric(label="🔋 רמת סוללה", value=f"{int(st.session_state.battery)}%")
        st.progress(st.session_state.battery / 100.0)
        
    with m2:
        signal = np.random.randint(70, 100) if st.session_state.system_status != 'idle' else 0
        st.metric(label="📶 עוצמת אות", value=f"{signal}%")
        st.progress(signal / 100.0)

    st.subheader("התקדמות הפעולה")
    if st.session_state.system_status == 'scanning':
        st.progress(st.session_state.scan_progress / 100.0)
        st.info(f"**שלב:** {st.session_state.scan_phase}")
    elif st.session_state.system_status == 'locating':
        st.progress(st.session_state.location_progress / 100.0)
        st.info(f"**שלב:** {st.session_state.scan_phase}")
        
        # DF Signal Strength
        st.subheader("🔊 אות εντοπισμού (DF)")
        st.metric(label="עוצמת ציפצוף", value=f"{st.session_state.df_signal}%")
        st.progress(st.session_state.df_signal / 100.0)

    elif st.session_state.system_status == 'selection':
        st.success(f"**מצב:** {st.session_state.scan_phase}. נא לבחור יעד.")
    elif st.session_state.system_status == 'located':
        st.success(f"**מצב:** {st.session_state.scan_phase}!")
    else: # idle
        st.info("**מצב מערכת:** מוכנה לפעולה")
    
with col2:
    st.header("תוצאות ומיקום")

    # IMSI display
    imsi_container = st.container(height=250)
    with imsi_container:
        st.subheader("מכשירים שזוהו (IMSI)")
        if not st.session_state.detected_imsis:
            st.info("ממתין לתוצאות סריקה...")
        else:
            imsi_df = pd.DataFrame({'IMSI': st.session_state.detected_imsis})
            st.dataframe(imsi_df, use_container_width=True, hide_index=True)

    # Map display
    st.markdown("---")
    st.subheader("מפת איתור")
    if st.session_state.location_found is not None:
        st.map(st.session_state.location_found, zoom=15)
        lat = st.session_state.location_found['latitude'].iloc[0]
        lon = st.session_state.location_found['longitude'].iloc[0]
        st.success(f"📍 נעדר אותר במיקום: {lat:.5f}, {lon:.5f}")
    else:
        # Default map location (e.g., center of Israel)
        map_data = pd.DataFrame({'latitude': [31.7683], 'longitude': [35.2137]})
        st.map(map_data, zoom=7)
        if st.session_state.system_status not in ['locating', 'located']:
             st.info("המפה תתעדכן עם איתור המיקום")

    # Status log
    st.markdown("---")
    st.subheader("יומן אירועים")
    log_container = st.container(height=250)
    with log_container:
        log_html = ""
        for entry in st.session_state.log:
            color = "white"
            if "חירום" in entry or "ERROR" in entry:
                color = "#ff6b6b" # red
            elif "אותר" in entry or "מיקום" in entry:
                color = "#4ecdc4" # green/cyan
            elif "אזהרה" in entry:
                color = "#ffd700" # yellow
            log_html += f'<p style="color:{color}; margin-bottom: 0.2rem; font-family: \'Courier New\', monospace; text-align: left; direction: ltr;">{entry}</p>'
        st.markdown(f"<div dir='rtl'>{log_html}</div>", unsafe_allow_html=True)


# --- ADDITIONAL INFO ---
st.markdown("---")
with st.expander("📝 מפרט טכני", expanded=False):
    st.markdown("""
    | תכונה | ערך |
    |---|---|
    | **תדר פעולה** | 900 MHz |
    | **הספק שידור** | 2-5 וואט |
    | **זמן פעולה** | 4-8 שעות רציפות |
    | **טכנולוגיה** | OCTASIC BTS-3500 |
    | **תמיכה** | 2G/4G Dual Mode |
    | **משקל** | < 2 ק"ג |
    """, unsafe_allow_html=True)

with st.expander("✨ תכונות עיקריות", expanded=False):
    st.markdown("""
    - **שידור דור 4 לאיתור:** מערכת איתור מתקדמת המבוססת על רשת סלולרית דור 4, מאפשרת איתור מדויק ומהיר.
    - **תדר שקט דור 2:** אימות מנויים באמצעות DF (Direction Finding) על תדר דור 2 שקט.
    - **עיצוב נייד:** מערכת קומפקטית המתאימה לתיק גב, קלה לנשיאה ופריסה מהירה בשטח.
    - **סוללות ארוכות טווח:** מאפשרת פעולה רציפה של 4-8 שעות.
    """)

# --- SIMULATION LOGIC ---
action_in_progress = st.session_state.system_status in ['scanning', 'locating']

if action_in_progress:
    # Battery drain
    drain_rate = 1 if st.session_state.system_status == 'locating' else 0.5
    if st.session_state.battery > 0:
        st.session_state.battery -= drain_rate
    else:
        st.session_state.battery = 0
        st.session_state.system_status = "idle"
        add_log("ERROR: סוללה התרוקנה! המערכת כובתה.")
        st.error("הסוללה אזלה!")

# 1. Scanning phase
if st.session_state.system_status == 'scanning':
    st.session_state.scan_progress += 4  # Progress increment
    
    # Generate IMSIs at intervals
    current_progress_marker = st.session_state.scan_progress // 20
    if len(st.session_state.detected_imsis) < current_progress_marker and len(st.session_state.detected_imsis) < 5:
        operator_code = np.random.choice(['01', '05', '06'])
        subscriber_part = ''.join([str(np.random.randint(0, 10)) for _ in range(9)])
        new_imsi = f"425{operator_code}{subscriber_part}"
        st.session_state.detected_imsis.append(new_imsi)
        add_log(f"📶 זוהה IMSI חדש: {new_imsi}")

    # Update phase description
    if st.session_state.scan_progress <= 40:
        st.session_state.scan_phase = "סורק תדרי 4G לאיתור ראשוני"
    elif st.session_state.scan_progress <= 80:
        st.session_state.scan_phase = "מנתח שידורים וזיהוי IMSI"
    else:
        st.session_state.scan_phase = "מסיים סריקה ואיסוף נתונים"

    if st.session_state.scan_progress >= 100:
        st.session_state.scan_progress = 100
        st.session_state.system_status = "selection"
        add_log("✅ סריקה הושלמה. נא לבחור IMSI לאיתור.")
        st.session_state.scan_phase = "הסריקה הושלמה"

    time.sleep(0.5)
    st.rerun()

# 2. Locating phase
if st.session_state.system_status == 'locating':
    st.session_state.location_progress += 10

    # Update location phase description
    if st.session_state.location_progress <= 20:
        st.session_state.scan_phase = f"מאזין לאות DF מ-{st.session_state.selected_imsi}"
        st.session_state.df_signal = np.random.randint(10, 30)
    elif st.session_state.location_progress <= 70:
        st.session_state.scan_phase = "האות מתחזק... (ציפצופים מהירים)"
        st.session_state.df_signal = np.random.randint(30, 80)
    else:
        st.session_state.scan_phase = "אות חזק מאוד! ננעל על המיקום"
        st.session_state.df_signal = np.random.randint(80, 100)

    if st.session_state.location_progress >= 100:
        st.session_state.location_progress = 100
        st.session_state.df_signal = 100
        lat, lon = 31.7683 + (np.random.randn() * 0.01), 35.2137 + (np.random.randn() * 0.01)
        st.session_state.location_found = pd.DataFrame({'latitude': [lat], 'longitude': [lon]})
        add_log(f"✅ מיקום מזוהה עבור {st.session_state.selected_imsi}: {lat:.5f}, {lon:.5f}")
        st.session_state.system_status = "located"
        st.session_state.scan_phase = "המיקום אותר"

    time.sleep(0.5)
    st.rerun()


if st.session_state.battery < 20 and st.session_state.battery < st.session_state.last_battery_warning:
    add_log("🔋 אזהרה: רמת סוללה נמוכה!")
    st.session_state.last_battery_warning = st.session_state.battery - 5 # Remind every 5% 