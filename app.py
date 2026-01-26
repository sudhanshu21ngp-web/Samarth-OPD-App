import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import io

# --- 1. CONFIG & AI FAILOVER ---
API_KEY = "AIzaSyB94LyTAcWiKmOohM1wDOYgrtZeyvO9USY"
genai.configure(api_key=API_KEY)
TRY = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-pro", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]

def get_ai_analysis(mode, p_info, symptoms, history=""):
    prompt = f"Doctor Analysis Case: Age/Sex {p_info['age']}, Symptoms: {symptoms}. Mode: {mode}. Format: |DIAGNOSIS|...|REMEDY/RX|..."
    for m_name in MODELS:
        try:
            model = genai.GenerativeModel(m_name)
            response = model.generate_content(prompt)
            return response.text, m_name
        except: continue
    return "|DIAGNOSIS| Manual Review |REMEDY| Placebo |", "LOCAL_FAILOVER"

# --- 2. PDF ENGINE (RX-NAME-DATE) ---
def create_pdf(slip_content):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=(80*mm, 200*mm))
    p.setFont("Helvetica", 9)
    y = 190 * mm
    for line in slip_content.split('\n'):
        p.drawString(5*mm, y, line)
        y -= 5*mm
    p.showPage()
    p.save()
    return buffer.getvalue()

# --- 3. DATA & ANALYTICS PERSISTENCE ---
if 'db' not in st.session_state: st.session_state.db = []
if 'form_state' not in st.session_state: st.session_state.form_state = {}

# --- 4. BRANDING ---
CLINIC = "SHRI SWAMI SAMARTH HOMEOPATHIC CLINIC AND HOSPITAL"
DR_INFO = "DR. SUDHANSHU GUPTA (B.H.M.S., M.D., REG: 47553)"

st.set_page_config(page_title="Clinic Pro v11", layout="wide")

# --- 5. SIDEBAR: DATA, SEARCH & ANALYTICS ---
st.sidebar.title("🏥 Clinic Management")

# A. SEARCH & FOLLOW-UP
search = st.sidebar.text_input("🔍 Search Patient Name")
if search:
    res = [r for r in st.session_state.db if search.lower() in r['Name'].lower()]
    for r in reversed(res):
        if st.sidebar.button(f"📅 {r['Date']} - {r['Name']}", key=f"hist_{r['ID']}{r['Date']}"):
            st.session_state.form_state = r
    if st.sidebar.button("➕ START FOLLOW-UP"):
        last = res[-1]
        st.session_state.form_state = {"ID": last['ID'], "Name": last['Name'], "Age": last['Age'], "Old_S": last['Symptoms']}

st.sidebar.divider()

# B. IMPORT / EXPORT (NO OMISSION)
st.sidebar.subheader("💾 Data Security")
if st.session_state.db:
    csv = pd.DataFrame(st.session_state.db).to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📥 Export Clinic DB", csv, f"Clinic_Backup_{datetime.now().strftime('%d%m%Y')}.csv")

uploaded_file = st.sidebar.file_uploader("📤 Import Clinic DB", type="csv")
if uploaded_file:
    st.session_state.db = pd.read_csv(uploaded_file).to_dict('records')
    st.sidebar.success("Database Loaded!")

# --- 6. MAIN INTERFACE ---
tab_opd, tab_stats = st.tabs(["📋 Consultation", "📊 Clinical Analytics"])

with tab_opd:
    st.header("Patient Consultation")
    c1, c2, c3 = st.columns(3)
    p_id = c1.text_input("ID", value=st.session_state.form_state.get("ID", f"A{len(st.session_state.db)+1}"))
    p_name = c2.text_input("Name", value=st.session_state.form_state.get("Name", ""))
    p_age = c3.text_input("Age/Sex", value=st.session_state.form_state.get("Age", ""))

    if "Old_S" in st.session_state.form_state:
        st.warning(f"📌 LAST COMPLAINTS: {st.session_state.form_state['Old_S']}")

    p_symp = st.text_area("Present Symptoms", value="")
    mode = st.radio("Mode", ["Homeopathic", "Allopathic"], horizontal=True)

    if st.button("🧠 AI ANALYSIS (Multi-Model)"):
        with st.spinner("Cycling through Gemini 2.0/1.5 failover..."):
            ans, model_used = get_ai_analysis(mode, {"age": p_age}, p_symp)
            st.session_state['current_rx'] = ans
            st.toast(f"Analyzed using {model_used}")

    st.divider()
    # EDITABLE BOX
    f_rx = st.text_area("Final Prescription (Editable)", value=st.session_state.get('current_rx', ""), height=200)
    f_diag = st.text_input("Diagnosis", value=f_rx.split("|DIAGNOSIS|")[-1].split("|")[0] if "|DIAGNOSIS|" in f_rx else "")

    if st.button("💾 SAVE & PRINT PDF"):
        timestamp = datetime.now().strftime("%d%m%Y")
        fname = f"RX-{p_name.replace(' ','').upper()}-{timestamp}.pdf"
        
        # Log to Database
        st.session_state.db.append({
            "ID": p_id, "Name": p_name, "Age": p_age, "Symptoms": p_symp, 
            "Diagnosis": f_diag, "Rx": f_rx, "Date": datetime.now().strftime("%Y-%m-%d")
        })
        
        # PDF Content
        content = f"{CLINIC}\n{DR_INFO}\n" + "="*20 + f"\nID: {p_id} | {p_name}\nDx: {f_diag}\n" + "-"*20 + f"\nRx:\n{f_rx}\n" + "="*20
        pdf_data = create_pdf(content)
        st.download_button(f"📥 Download {fname}", data=pdf_data, file_name=fname)

with tab_stats:
    st.header("Clinic Statistics")
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        st.subheader("Top Diagnoses")
        st.bar_chart(df['Diagnosis'].value_counts())
        st.subheader("Recent Visits")
        st.table(df[['Date', 'ID', 'Name', 'Diagnosis']].tail(10))
    else:
        st.info("No data available for analytics yet.")