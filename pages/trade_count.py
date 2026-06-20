# trade_count.py

import streamlit as st
import pandas as pd
import os
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = str(ROOT_DIR)
ICON_DIR = str(ROOT_DIR / "icons")
ITEM_DATA_PATH = str(ROOT_DIR / "data" / "item_ids.json")
TRADE_DATA_PATH = str(ROOT_DIR / "data" / "completed_trades_pc_sc_nl.json")

# Load item data
with open(ITEM_DATA_PATH, "r") as f:
    item_data = json.load(f)

def get_icon_path(item_name):
    icon_name = item_data.get(item_name, {}).get("icon", "")
    if icon_name:
        full_path = os.path.join(ICON_DIR, icon_name)
        return full_path if os.path.isfile(full_path) else None
    return None

# Load and flatten trade data
with open(TRADE_DATA_PATH, "r") as f:
    raw_data = json.load(f)

flat_data = [{"item": item, "trade_count": details["metadata"]["total_trades"]}
             for item, details in raw_data.items()]

trade_df = pd.DataFrame(flat_data)
trade_df = trade_df.sort_values(by="trade_count", ascending=False)

# Display
st.title("Trade Count")
for _, row in trade_df.iterrows():
    item = row["item"]
    count = row["trade_count"]
    st.write(f"**{item}** - traded {count} times")

    icon_path = get_icon_path(item)
    if icon_path:
        st.image(icon_path, width=32)