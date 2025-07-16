import streamlit as st
import pandas as pd
from datetime import date
import re

st.set_page_config(page_title="BudgetWise", layout="centered")
st.title("🧾 BudgetWise")
st.markdown("Track your purchases and reflect on how they make you feel.")

# --- Initialize session state ---
if 'log' not in st.session_state:
    st.session_state.log = []

if 'temp_item' not in st.session_state:
    st.session_state.temp_item = None

if 'temp_date' not in st.session_state:
    st.session_state.temp_date = None

if 'temp_amount' not in st.session_state:
    st.session_state.temp_amount = None

# --- Category Mapping ---
CATEGORY_MAP = {
    "playstation": "games", "xbox": "games", "nintendo": "games", "game": "games",
    "burger": "food", "pizza": "food", "restaurant": "food", "groceries": "food", "snack": "food",
    "tv": "electronics", "laptop": "electronics", "headphones": "electronics", "phone": "electronics",
    "chair": "furniture", "desk": "furniture", "sofa": "furniture", "couch": "furniture", "table": "furniture",
    "pen": "stationery", "notebook": "stationery", "eraser": "stationery", "marker": "stationery"
}

FEELING_COLORS = {
    "positive": "green",
    "neutral": "yellow",
    "negative": "red"
}

def get_sentiment(feeling):
    feeling = feeling.lower()
    if any(word in feeling for word in ["good", "great", "amazing", "happy", "love"]):
        return "positive"
    elif any(word in feeling for word in ["bad", "terrible", "regret", "horrible", "awful"]):
        return "negative"
    else:
        return "neutral"

def extract_category(item):
    item = item.lower()
    for key, category in CATEGORY_MAP.items():
        if key in item:
            return category
    return "other"

# --- Input Handling ---
st.subheader("🖊️ Tell me about a recent purchase:")

with st.form(key="log_form"):
    user_input = st.text_input(" ", placeholder="e.g., I bought a pen for $2", key="purchase_input")
    submitted = st.form_submit_button("Log it")

if submitted:
    match = re.search(r"bought a (.*?) for (\$?\d+)", user_input, re.IGNORECASE)
    if match:
        item = match.group(1).strip()
        amount = float(match.group(2).replace("$", ""))
        st.session_state.temp_item = item
        st.session_state.temp_amount = amount
        st.session_state.temp_date = date.today()
    elif re.match(r"^\$?\d+(\.\d{1,2})?$", user_input.strip()) and st.session_state.temp_item:
        st.session_state.temp_amount = float(user_input.replace("$", ""))
    elif st.session_state.temp_item and st.session_state.temp_amount:
        feeling = user_input
        sentiment = get_sentiment(feeling)
        st.session_state.log.append({
            "date": st.session_state.temp_date,
            "item": st.session_state.temp_item,
            "amount": st.session_state.temp_amount,
            "feeling": feeling,
            "sentiment": sentiment
        })
        st.success("✅ Purchase logged!")
        st.session_state.temp_item = None
        st.session_state.temp_amount = None
        st.session_state.temp_date = None
    else:
        st.error("❌ Couldn't understand the item. Please use the format: 'I bought a [thing] for [amount]'")

# --- Calendar View ---
st.subheader("📅 Purchase Calendar")

if st.session_state.log:
    log_df = pd.DataFrame(st.session_state.log)
    log_df['date'] = pd.to_datetime(log_df['date'])

    for i, row in log_df.iterrows():
        color = FEELING_COLORS.get(row['sentiment'], 'yellow')
        delete_button = st.button("❌", key=f"delete_{i}")
        st.markdown(f"<span style='color:{color};font-weight:bold'>{row['date'].date()}</span> — {row['item']} — ${row['amount']} — _{row['feeling']}_", unsafe_allow_html=True)
        if delete_button:
            st.session_state.log.pop(i)
            st.experimental_rerun()
else:
    st.info("No purchases logged yet.")

# --- Suggestion Engine ---
if st.session_state.log:
    category_summary = {}
    for entry in st.session_state.log:
        cat = extract_category(entry['item'])
        if cat == "other":
            continue
        category_summary[cat] = category_summary.get(cat, 0) + entry['amount']

    if category_summary:
        highest = max(category_summary.items(), key=lambda x: x[1])
        st.markdown("💡 **What should I cut back on?**")
        st.info(f"You spent the most on **{highest[0]}** (${highest[1]:.2f}) — consider reviewing those purchases.")
