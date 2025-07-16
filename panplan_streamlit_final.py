import streamlit as st
import pandas as pd
import re
from datetime import datetime

st.set_page_config(page_title="PanPlan – Budget & Emotion Tracker", layout="centered")
st.title("🧠 PanPlan – Budget & Emotion Tracker")

DATA_FILE = "purchase_log.csv"

# Load or initialize data
try:
    df = pd.read_csv(DATA_FILE)
except FileNotFoundError:
    df = pd.DataFrame(columns=["timestamp", "item", "amount", "sentiment", "category"])
    df.to_csv(DATA_FILE, index=False)

# Keyword-based categorization
CATEGORY_KEYWORDS = {
    "games": ["playstation", "xbox", "game", "controller", "nintendo", "console"],
    "furniture": ["couch", "table", "chair", "sofa", "desk", "bed"],
    "electronics": ["phone", "laptop", "tv", "tablet", "monitor", "camera"],
    "food": ["pizza", "coffee", "burger", "groceries", "sandwich", "lunch", "dinner"],
    "clothing": ["shirt", "jeans", "jacket", "shoes", "sneakers", "dress"],
    "transportation": ["bus", "train", "uber", "taxi", "flight", "ticket"],
    "entertainment": ["movie", "netflix", "concert", "theater"],
    "education": ["course", "book", "notebook", "class", "lesson"],
}

NEGATIVE_WORDS = {"regret", "sad", "angry", "anxious", "bad", "guilty", "meh", "tired", "horrible", "awful", "waste", "terrible"}
POSITIVE_WORDS = {"happy", "excited", "relieved", "good", "satisfied", "proud"}

def extract_info(text):
    pattern = r"bought a[n]* ([\w\s]+?)(?: for (\$?\d+[kK]?))?$"
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

def classify_feeling(feel):
    f = feel.lower()
    if any(word in f for word in NEGATIVE_WORDS):
        return "bad"
    elif any(word in f for word in POSITIVE_WORDS):
        return "good"
    return "neutral"

def categorize(item):
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(word in item.lower() for word in keywords):
            return category
    return "other"

def log_entry(item, amount, sentiment):
    category = categorize(item)
    row = pd.DataFrame([{
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "item": item,
        "amount": amount,
        "sentiment": classify_feeling(sentiment),
        "category": category
    }])
    updated = pd.concat([pd.read_csv(DATA_FILE), row], ignore_index=True)
    updated.to_csv(DATA_FILE, index=False)

def delete_entry(timestamp):
    df = pd.read_csv(DATA_FILE)
    df = df[df["timestamp"] != timestamp]
    df.to_csv(DATA_FILE, index=False)

# Chat Flow
if "pending" not in st.session_state:
    st.session_state["pending"] = {}

with st.form("input_form"):
    user_input = st.text_input("💬 What did you buy?", placeholder="E.g. I bought a phone for 900")
    submitted = st.form_submit_button("Submit")
    if submitted and user_input:
        item, amount = extract_info(user_input)
        if item and amount:
            st.session_state["pending"] = {"item": item, "amount": amount}
        elif item:
            st.session_state["pending"] = {"item": item, "amount": None}
        else:
            st.error("⚠️ I didn't understand. Try: 'I bought a lamp for 30'")

if "pending" in st.session_state and st.session_state["pending"].get("item") and st.session_state["pending"].get("amount") is None:
    with st.form("ask_amount"):
        amt = st.number_input(f"How much did you spend on the {st.session_state['pending']['item']}?", min_value=0.0)
        amt_sub = st.form_submit_button("Next")
        if amt_sub:
            st.session_state["pending"]["amount"] = amt

if "pending" in st.session_state and all(k in st.session_state["pending"] for k in ("item", "amount")) and st.session_state["pending"]["amount"] is not None:
    with st.form("ask_feeling"):
        feel = st.text_input("How did that purchase make you feel?")
        done = st.form_submit_button("Log it")
        if done:
            log_entry(st.session_state["pending"]["item"], st.session_state["pending"]["amount"], feel)
            st.success("✅ Logged!")
            st.session_state["pending"] = {}

# Calendar View
st.subheader("📅 Spending Calendar")

df = pd.read_csv(DATA_FILE)
if df.empty:
    st.info("No purchases recorded yet.")
else:
    for _, row in df.sort_values("timestamp", ascending=False).iterrows():
        color = {"good": "#4CAF50", "neutral": "#FFEB3B", "bad": "#F44336"}.get(row["sentiment"], "#ccc")
        with st.container():
            cols = st.columns([0.9, 0.1])
            with cols[0]:
                st.markdown(
                    f"<div style='border-left: 8px solid {color}; padding-left: 10px;'>"
                    f"<b>{row['timestamp'][:10]}</b> — {row['item']} — ${int(row['amount'])} — <i>{row['sentiment']}</i>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with cols[1]:
                if st.button("❌", key=row['timestamp']):
                    delete_entry(row['timestamp'])
                    st.rerun()

# Cut back analysis
if not df.empty:
    st.subheader("💡 What to cut back on?")
    if st.button("Analyze"):
        grouped = df.groupby("category").agg(
            total_spend=pd.NamedAgg(column="amount", aggfunc="sum"),
            bad_count=pd.NamedAgg(column="sentiment", aggfunc=lambda x: (x == "bad").sum())
        )
        if grouped.empty or grouped["bad_count"].max() == 0:
            st.success("🎉 Nothing clearly negative to cut back on!")
        else:
            worst = grouped[grouped["bad_count"] > 0].sort_values("total_spend", ascending=False)
            category = worst.index[0]
            st.warning(f"Consider cutting back on **{category}**. You spent ${int(worst.iloc[0]['total_spend'])} and felt bad {int(worst.iloc[0]['bad_count'])} times.")

