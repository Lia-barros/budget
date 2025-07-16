
import streamlit as st
import pandas as pd
import re
import datetime
import os

st.set_page_config(page_title="PanPlan", layout="centered")
st.title("🧠 PanPlan: Emotional Budget Chatbot")

DATA_FILE = "purchase_log.csv"

CATEGORY_KEYWORDS = {
    "food": ["burger", "pizza", "coffee", "meal", "lunch", "dinner"],
    "electronics": ["phone", "laptop", "tablet", "headphones", "tv", "camera"],
    "furniture": ["couch", "sofa", "table", "chair", "desk", "bed"],
    "games": ["game", "playstation", "xbox", "nintendo", "controller"],
    "education": ["book", "pen", "pencil", "notebook", "course", "class"],
    "clothing": ["shirt", "pants", "dress", "shoes", "jacket"],
    "transport": ["uber", "bus", "train", "ticket", "flight"],
    "beauty": ["makeup", "lipstick", "skincare", "cream", "lotion"],
    "health": ["medicine", "vitamin", "hospital", "pharmacy"],
    "pet care": ["dog food", "cat litter", "pet toy", "vet"],
    "home supplies": ["toilet paper", "detergent", "cleaner", "mop", "broom"]
}

FEELING_MAP = {
    "great": "positive", "good": "positive", "happy": "positive", "satisfied": "positive", "amazing": "positive",
    "okay": "neutral", "meh": "neutral", "neutral": "neutral", "fine": "neutral",
    "bad": "negative", "horrible": "negative", "sad": "negative", "guilty": "negative", "regret": "negative"
}

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["date", "item", "amount", "feeling", "category"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def classify_category(item_name):
    item = item_name.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in item for kw in keywords):
            return category
    return "other"

def map_feeling(feeling_text):
    for key, val in FEELING_MAP.items():
        if key in feeling_text.lower():
            return val
    return "neutral"

def parse_purchase(text):
    item_match = re.search(r"bought a[n]* (.*?) for", text.lower())
    amount_match = re.search(r"\$?(\d+(\.\d+)?)(k)?", text.lower())
    if item_match:
        item = item_match.group(1)
    else:
        item = None
    if amount_match:
        amount = float(amount_match.group(1))
        if amount_match.group(3):  # 'k' was used
            amount *= 1000
    else:
        amount = None
    return item, amount

data = load_data()

with st.form("log_form"):
    input_text = st.text_input("📝 Tell me about a recent purchase:")
    submitted = st.form_submit_button("Log it")

    if submitted:
        item, amount = parse_purchase(input_text)
        if not item:
            st.error("Couldn't understand the item. Please use the format: 'I bought a [thing] for [amount]'")
        elif not amount:
            st.warning("How much did it cost?")
        else:
            feeling = st.text_input("How did that purchase make you feel?")
            feeling_category = map_feeling(feeling)
            category = classify_category(item)
            new_row = {
                "date": datetime.date.today().isoformat(),
                "item": item,
                "amount": amount,
                "feeling": feeling_category,
                "category": category
            }
            data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)
            save_data(data)
            st.success("✅ Purchase logged!")

st.markdown("### 📅 Purchase Calendar")
if not data.empty:
    for idx, row in data.iterrows():
        color = {"positive": "green", "neutral": "yellow", "negative": "red"}.get(row["feeling"], "gray")
        with st.container():
            st.markdown(
                f"<span style='border-left: 5px solid {color}; padding-left: 10px;'>"
                f"**{row['date']}** — {row['item']} — ${row['amount']} — *{row['feeling']}* "
                f"<a href='?delete={idx}' style='color:red;'>(x)</a></span>",
                unsafe_allow_html=True
            )

    if "delete" in st.experimental_get_query_params():
        delete_idx = int(st.experimental_get_query_params()["delete"][0])
        data = data.drop(index=delete_idx).reset_index(drop=True)
        save_data(data)
        st.experimental_rerun()
else:
    st.info("No purchases logged yet.")

if st.button("💡 What should I cut back on?") and not data.empty:
    spend_summary = data.groupby("category").agg({
        "amount": "sum",
        "feeling": lambda x: (x == "negative").sum()
    }).reset_index()
    spend_summary = spend_summary[spend_summary["category"] != "other"]
    if not spend_summary.empty:
        spend_summary["score"] = spend_summary["amount"] * spend_summary["feeling"]
        top = spend_summary.sort_values(by="score", ascending=False).head(1)
        st.warning(f"📉 You might want to cut back on **{top.iloc[0]['category']}**.")
    else:
        st.info("No clear category to cut back on yet.")
