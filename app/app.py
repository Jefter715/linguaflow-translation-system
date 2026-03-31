import os

import streamlit as st
import requests
import boto3
import json
import uuid
import time
import pandas as pd
import io
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LinguaFlow – AI Translator",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* ── Root variables ── */
:root {
    --primary:   #FF6B35;
    --secondary: #004E89;
    --accent:    #FFD166;
    --success:   #06D6A0;
    --bg:        #0D0D0D;
    --surface:   #1A1A2E;
    --surface2:  #16213E;
    --text:      #F0EBF4;
    --muted:     #8B8FA8;
    --border:    rgba(255,107,53,0.25);
}

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg);
    color: var(--text);
}

.main { background: var(--bg); }
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D0D0D 0%, #1A1A2E 100%);
    border-right: 1px solid var(--border);
}

/* ── Hero banner ── */
.hero {
    background: linear-gradient(135deg, #FF6B35 0%, #004E89 60%, #0D0D0D 100%);
    border-radius: 20px;
    padding: 2.5rem 2rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: "🌍";
    position: absolute; right: 2rem; top: 1rem;
    font-size: 6rem; opacity: 0.15;
}
.hero h1 {
    font-family: 'Syne', sans-serif;
    font-size: 2.8rem; font-weight: 800;
    color: #fff; margin: 0 0 0.3rem;
    text-shadow: 0 2px 20px rgba(0,0,0,0.4);
}
.hero p { color: rgba(255,255,255,0.8); font-size: 1.05rem; margin: 0; }

/* ── Cards ── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.card-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem; font-weight: 700;
    color: var(--primary); margin-bottom: 0.8rem;
}

/* ── Result box ── */
.result-box {
    background: linear-gradient(135deg, rgba(6,214,160,0.08), rgba(0,78,137,0.15));
    border: 1px solid rgba(6,214,160,0.35);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    font-size: 1.25rem;
    color: #000;
    margin-top: 0.5rem;
    min-height: 60px;
}

/* ── History item ── */
.hist-item {
    background: var(--surface2);
    border-left: 3px solid var(--primary);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.6rem;
    font-size: 0.9rem;
}
.hist-meta { color: var(--muted); font-size: 0.78rem; margin-bottom: 0.2rem; }

/* ── Badge ── */
.lang-badge {
    display: inline-block;
    background: rgba(255,107,53,0.15);
    border: 1px solid var(--primary);
    color: var(--primary);
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 0.8rem; font-weight: 500;
}

/* ── Streamlit widget overrides ── */
.stTextArea textarea {
    background: #111827 !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
}
.stSelectbox > div > div {
    background: #111827 !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
}
.stButton > button {
    background: linear-gradient(135deg, var(--primary), #e8541f) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.6rem 2rem !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
    box-shadow: 0 4px 20px rgba(255,107,53,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(255,107,53,0.5) !important;
}
.stFileUploader {
    background: #111827 !important;
    border: 2px dashed var(--border) !important;
    border-radius: 12px !important;
}
div[data-testid="stMetricValue"] { color: var(--primary) !important; font-family: 'Syne', sans-serif !important; }
.stTabs [data-baseweb="tab"] { font-family: 'Syne', sans-serif !important; font-weight: 700 !important; }
.stTabs [aria-selected="true"] { color: var(--primary) !important; border-bottom-color: var(--primary) !important; }
</style>
""", unsafe_allow_html=True)

# ── Config (edit these) ───────────────────────────────────────────────────────
API_URL = "https://fqogfpikjj.execute-api.us-east-1.amazonaws.com/prod/translate"
SQS_QUEUE_URL = None
AWS_REGION    = "us-east-1"

# ── Supported languages ───────────────────────────────────────────────────────
LANGUAGES = {
    "English": "en", "Spanish": "es", "French": "fr", "German": "de",
    "Italian": "it", "Portuguese": "pt", "Dutch": "nl", "Russian": "ru",
    "Chinese (Simplified)": "zh", "Japanese": "ja", "Korean": "ko",
    "Arabic": "ar", "Hindi": "hi", "Turkish": "tr", "Polish": "pl",
    "Swedish": "sv", "Danish": "da", "Finnish": "fi", "Norwegian": "no",
    "Swahili": "sw", "Hausa": "ha", "Yoruba": "yo", "Amharic": "am",
    "Hebrew": "he", "Thai": "th", "Vietnamese": "vi", "Indonesian": "id",
}

def check_api_health():
    try:
        r = requests.post(API_URL, json={
            "text": "test",
            "source_lang": "en",
            "target_lang": "fr"
        }, timeout=5)
        return r.status_code == 200
    except:
        return False
# ── Session state ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []

# ── Helpers ───────────────────────────────────────────────────────────────────
def translate_text(text, source_lang, target_lang):
    """Call API Gateway → Lambda → AWS Translate."""
    payload = {"text": text, "source_lang": source_lang, "target_lang": target_lang}
    try:
        r = requests.post(API_URL, json=payload, timeout=15)
        data = r.json()
        if r.status_code == 200:
            return data.get("translated", ""), None
        return None, data.get("error", "Unknown error")
    except Exception as e:
        return None, str(e)

def send_to_sqs(messages: list):
    """Send a batch of translation jobs to SQS (future feature)."""
    if not SQS_QUEUE_URL:
        raise Exception("SQS is currently disabled (future feature).")

    sqs = boto3.client("sqs", region_name=AWS_REGION)
    entries = []

    for i, msg in enumerate(messages):
        entries.append({
            "Id": str(i),
            "MessageBody": json.dumps(msg),
            "MessageGroupId": "batch",
            "MessageDeduplicationId": str(uuid.uuid4()),
        })

    for chunk in [entries[i:i+10] for i in range(0, len(entries), 10)]:
        sqs.send_message_batch(QueueUrl=SQS_QUEUE_URL, Entries=chunk)
def add_to_history(original, translated, src, tgt):
    st.session_state.history.insert(0, {
        "original": original, "translated": translated,
        "src": src, "tgt": tgt,
        "time": datetime.now().strftime("%H:%M:%S"),
    })
    if len(st.session_state.history) > 50:
        st.session_state.history = st.session_state.history[:50]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1rem 0 1.5rem;'>
        <div style='font-family:Syne,sans-serif; font-size:1.6rem; font-weight:800; color:#FF6B35;'>🌐 LinguaFlow</div>
        <div style='color:#8B8FA8; font-size:0.85rem;'>Powered by AWS Translate</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🌍 Language Pair")
    src_name = st.selectbox("Source language", list(LANGUAGES.keys()), index=0)
    tgt_name = st.selectbox("Target language", list(LANGUAGES.keys()), index=1)
    src_code  = LANGUAGES[src_name]
    tgt_code  = LANGUAGES[tgt_name]

    st.markdown("---")
    st.markdown(f"""
    <div style='color:#8B8FA8; font-size:0.82rem; line-height:1.6;'>
    <b style='color:#FF6B35;'>Selected pair</b><br>
    <span class='lang-badge'>{src_name}</span> → <span class='lang-badge'>{tgt_name}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""
    <div style='color:#8B8FA8; font-size:0.78rem;'>
    📊 <b>History:</b> {len(st.session_state.history)} translations<br>
    🔗 <b>Region:</b> {AWS_REGION}
    </div>
    """, unsafe_allow_html=True)

    if st.button("🗑️ Clear History"):
        st.session_state.history = []
        st.rerun()
        
    api_status = check_api_health()
    status_color = "#06D6A0" if api_status else "#FF4B4B"
    status_text = "Online" if api_status else "Offline"

    st.markdown(f"""
    <div style='margin-top:1rem; font-size:0.8rem; color:#8B8FA8;'>
    🔌 API Status:
    <span style='color:{status_color}; font-weight:600;'>{status_text}</span>
    </div>
    """, unsafe_allow_html=True)

# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class='hero'>
    <h1>LinguaFlow Translator</h1>
    <p>Instant AI-powered translations via AWS Translate · Single text & batch file support</p>
</div>
""", unsafe_allow_html=True)

# Stats row
c1, c2, c3 = st.columns(3)
c1.metric("Translations Today", len(st.session_state.history))
c2.metric("Source Language", src_name)
c3.metric("Target Language", tgt_name)

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["✏️  Single Translation", "📂  Batch Upload", "🕘  History"])

# ─── TAB 1: Single translation ────────────────────────────────────────────────
with tab1:
    col_l, col_r = st.columns(2, gap="large")

    with col_l:
        st.markdown("<div class='card-title'>📝 Input Text</div>", unsafe_allow_html=True)
        input_text = st.text_area(
            label="input", label_visibility="collapsed",
            placeholder=f"Type or paste text in {src_name}…",
            height=200, key="single_input"
        )
        char_count = len(input_text)
        st.caption(f"{char_count} characters")

        translate_btn = st.button("🚀 Translate", use_container_width=True)

    with col_r:
        st.markdown("<div class='card-title'>✨ Translation</div>", unsafe_allow_html=True)
        if translate_btn:
            if not input_text.strip():
                st.warning("Please enter some text to translate.")
            elif src_code == tgt_code:
                st.warning("Source and target languages must be different.")
            else:
                with st.spinner("Translating…"):
                    result, error = translate_text(input_text.strip(), src_code, tgt_code)
                if error:
                    st.error(f"❌ {error}")
                else:
                    st.markdown(f"<div class='result-box'>{result}</div>", unsafe_allow_html=True)
                    add_to_history(input_text.strip(), result, src_name, tgt_name)
                    st.success("✅ Translation complete!")

                    # Download single result
                    dl = f"Original ({src_name}):\n{input_text.strip()}\n\nTranslation ({tgt_name}):\n{result}"
                    st.download_button(
                        "⬇️ Download Result", data=dl,
                        file_name="translation.txt", mime="text/plain"
                    )
        else:
            st.markdown("<div class='result-box' style='color:#8B8FA8; font-style:italic;'>Translation will appear here…</div>", unsafe_allow_html=True)

# ─── TAB 2: Batch upload ──────────────────────────────────────────────────────
with tab2:
    st.markdown("<div class='card-title'>📂 Upload a CSV or TXT file for batch translation</div>", unsafe_allow_html=True)

    st.info("""
    **CSV format:** must have a column named `text` (other columns are preserved).  
    **TXT format:** one sentence / paragraph per line.
    """)

    uploaded = st.file_uploader("Choose file", type=["csv", "txt"], key="batch_file")

    if uploaded:
        file_type = uploaded.name.split(".")[-1].lower()

        if file_type == "csv":
            df = pd.read_csv(uploaded)
            if "text" not in df.columns:
                st.error("❌ CSV must have a column named `text`.")
            else:
                st.markdown(f"**Preview** ({len(df)} rows)")
                st.dataframe(df.head(10), use_container_width=True)

                col_a, col_b = st.columns(2)
                with col_a:
                    mode = st.radio("Processing mode", ["Direct API (recommended)", "SQS Queue (Coming soon)"], key="csv_mode")
                with col_b:
                    st.markdown(f"<br><span style='color:#8B8FA8;'>Rows to translate: <b style='color:#FF6B35;'>{len(df)}</b></span>", unsafe_allow_html=True)
                if mode.strip() == "SQS Queue (Coming soon)":
                    st.info("""
                        🚧 **SQS Batch Processing (Coming Soon)**

                        This mode represents an asynchronous architecture using:
                        - Amazon SQS (queue)
                        - AWS Lambda (worker)
                        - Scalable batch processing

                        It is currently disabled in this demo to keep the system lightweight.
                        Future updates will enable this feature for large-scale translations!
                    """)
                if st.button("⚡ Start Batch Translation", use_container_width=True):
                    if mode == "SQS Queue (Coming soon)":
                        messages = [
                            {"text": row["text"], "source_lang": src_code, "target_lang": tgt_code, "row_id": i}
                            for i, row in df.iterrows()
                        ]
                        with st.spinner(f"Sending {len(messages)} jobs to SQS…"):
                            try:
                                send_to_sqs(messages)
                                st.success(f"✅ {len(messages)} jobs sent to SQS queue! Your Lambda will process them asynchronously.")
                            except Exception as e:
                                st.error(f"SQS error: {e}")
                    else:
                        results = []
                        progress = st.progress(0, text="Translating…")
                        for i, row in df.iterrows():
                            translated, err = translate_text(str(row["text"]), src_code, tgt_code)
                            results.append(translated if not err else f"ERROR: {err}")
                            progress.progress((i + 1) / len(df), text=f"Translating row {i+1}/{len(df)}…")
                            time.sleep(0.05)  # gentle rate limiting

                        df["translated"] = results
                        progress.empty()
                        st.success("✅ Batch translation complete!")
                        st.dataframe(df, use_container_width=True)

                        csv_out = df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            "⬇️ Download Translated CSV", data=csv_out,
                            file_name=f"translated_{uploaded.name}", mime="text/csv"
                        )

        elif file_type == "txt":
            lines = [l.strip() for l in uploaded.read().decode("utf-8").splitlines() if l.strip()]
            st.markdown(f"**{len(lines)} lines detected**")
            st.text_area("Preview", "\n".join(lines[:10]) + ("\n…" if len(lines) > 10 else ""), height=150, disabled=True)

            mode_txt = st.radio("Processing mode", ["Direct API", "SQS Queue (Coming soon)"], key="txt_mode")

            if st.button("⚡ Translate File", use_container_width=True):
                if mode_txt == "SQS Queue":
                    st.info("🚧 SQS-based async processing will be enabled in future versions.")
                    messages = [{"text": l, "source_lang": src_code, "target_lang": tgt_code} for l in lines]
                    with st.spinner("Sending to SQS…"):
                        try:
                            send_to_sqs(messages)
                            st.success(f"✅ {len(messages)} lines sent to SQS queue!")
                        except Exception as e:
                            st.error(f"SQS error: {e}")
                else:
                    translated_lines = []
                    progress = st.progress(0)
                    for i, line in enumerate(lines):
                        t, err = translate_text(line, src_code, tgt_code)
                        translated_lines.append(t if not err else f"[ERROR] {err}")
                        progress.progress((i + 1) / len(lines))
                        time.sleep(0.05)
                    progress.empty()
                    output = "\n".join(translated_lines)
                    st.text_area("Translated Output", output, height=200)
                    st.download_button(
                        "⬇️ Download Translated TXT", data=output.encode("utf-8"),
                        file_name=f"translated_{uploaded.name}", mime="text/plain"
                    )

# ─── TAB 3: History ───────────────────────────────────────────────────────────
with tab3:
    if not st.session_state.history:
        st.markdown("<div style='text-align:center; color:#8B8FA8; padding: 3rem;'>No translations yet. Start translating!</div>", unsafe_allow_html=True)
    else:
        # Download full history
        hist_df = pd.DataFrame(st.session_state.history)
        st.download_button(
            "⬇️ Download History (CSV)",
            data=hist_df.to_csv(index=False).encode("utf-8"),
            file_name="translation_history.csv", mime="text/csv"
        )
        st.markdown("---")
        for item in st.session_state.history:
            st.markdown(f"""
            <div class='hist-item'>
                <div class='hist-meta'>🕘 {item['time']} &nbsp;|&nbsp; <span class='lang-badge'>{item['src']}</span> → <span class='lang-badge'>{item['tgt']}</span></div>
                <div><b>Original:</b> {item['original'][:120]}{'…' if len(item['original'])>120 else ''}</div>
                <div style='color:#06D6A0;'><b>Translated:</b> {item['translated'][:120]}{'…' if len(item['translated'])>120 else ''}</div>
            </div>
            """, unsafe_allow_html=True)
