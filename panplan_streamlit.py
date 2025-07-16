import streamlit as st
import pandas as pd
import re
from datetime import datetime

# Set up
st.set_page_config(page_title="Budget + Emotion Chatbot", layout="centered")
st.title("🧠 Budget + Emotion Chatbot")

DATA_FILE = "purchase_log.csv"

# Load or create dataset
try:
    df = pd.read_csv(DATA_FILE)
except FileNotFoundError:
    df = pd.DataFrame(columns=["timestamp", "item", "amount", "sentiment"])
    df.to_csv(DATA_FILE, index=False)

# --- Utilities ---
def extract_purchase_info(text):
    pattern = r"bought a[n]* ([\w\s]+)(?: for (\$?\d+[kK]?))?"
    match = re.search(pattern, text.lower())
    if not match:
        return None, None
    item = match.group(1).strip()
    amount = match.group(2)
    if amount:
        amount = amount.replace('$', '')
        amount = float(amount.replace('k', '')) * 1000 if 'k' in amount else float(amount)
    else:
        amount = None
    return item, amount

def classify_feeling(feeling):
    bad = {'regret', 'sad', 'angry', 'anxious', 'bad', 'guilty', 'meh', 'tired'}
    good = {'happy', 'excited', 'relieved', 'good', 'satisfied'}
    if any(b in feeling.lower() for b in bad):
        return 'bad'
    elif any(g in feeling.lower() for g in good):
        return 'good'
    else:
        return 'neutral'

def log_purchase(item, amount, sentiment):
    timestamp = datetime.now().isoformat(timespec="seconds")
    mood = classify_feeling(sentiment)
    entry = pd.DataFrame([{
        "timestamp": timestamp,
        "item": item,
        "amount": amount,
        "sentiment": mood
    }])
    updated = pd.concat([pd.read_csv(DATA_FILE), entry], ignore_index=True)
    updated.to_csv(DATA_FILE, index=False)

# --- Chatbot Interaction ---
with st.form("purchase_form"):
    user_input = st.text_input("💬 Tell me what you bought", placeholder="I bought a chair for 50")
    submitted = st.form_submit_button("Submit")
    if submitted and user_input:
        item, amount = extract_purchase_info(user_input)
        if item and amount:
            st.session_state["pending"] = {"item": item, "amount": amount}
        elif item:
            st.session_state["pending"] = {"item": item, "amount": None}
        else:
            st.error("I couldn't understand. Try: I bought a laptop for 900")

# Ask for missing amount
if "pending" in st.session_state and st.session_state["pending"].get("amount") is None:
    with st.form("amount_form"):
        amount_input = st.number_input(f"How much did you spend on the {st.session_state['pending']['item']}?", min_value=0.0)
        submit_amount = st.form_submit_button("Next")
        if submit_amount:
            st.session_state["pending"]["amount"] = amount_input

# Ask how the user feels
if "pending" in st.session_state and st.session_state["pending"].get("amount") is not None:
    with st.form("emotion_form"):
        feeling = st.text_input("How did that purchase make you feel?")
        log_it = st.form_submit_button("Log it")
        if log_it:
            log_purchase(
                st.session_state["pending"]["item"],
                st.session_state["pending"]["amount"],
                feeling
            )
            st.success("✅ Purchase logged!")
            del st.session_state["pending"]

# --- Calendar View ---
st.subheader("📅 Purchase Calendar")

df = pd.read_csv(DATA_FILE)
if df.empty:
    st.info("No purchases recorded yet.")
else:
    for _, row in df.sort_values("timestamp", ascending=False).iterrows():
        color = {
            "good": "green",
            "neutral": "yellow",
            "bad": "red"
        }.get(row["sentiment"], "gray")
        st.markdown(
            f"<div style='border-left: 10px solid {color}; padding: 10px; margin-bottom: 5px;'>"
            f"<b>{row['timestamp'][:10]}</b> — {row['item']} — ${int(row['amount'])} — "
            f"<i>{row['sentiment']}</i>"
            f"</div>",
            unsafe_allow_html=True
        )

# --- Recommendation Button ---
if not df.empty:
    if st.button("💡 What should I cut back on?"):
        summary = df.groupby("item").agg({"amount": "sum", "sentiment": lambda x: x.mode()[0]})
        bad_spend = summary[summary["sentiment"] == "bad"].sort_values("amount", ascending=False)
        if bad_spend.empty:
            st.success("🎉 Nothing costly and negative to cut back on!")
        else:
            st.warning("Consider cutting back on: " + ", ".join(bad_spend.index))
