# filename: app.py
import streamlit as st
import json
from pathlib import Path
from datetime import datetime

# Page config
st.set_page_config(page_title="Diablo II Rune Values", page_icon="🧙‍♂️", layout="wide")

# Paths
BASE_DIR = Path(__file__).resolve().parent
ITEM_DATA_PATH = BASE_DIR / "data" / "item_data.json"
TRADES_PATH = BASE_DIR / "data" / "completed_trades_pc_sc_nl.json"

# JSON loader
def load_json(path):
    try:
        return json.loads(path.read_text())
    except Exception as e:
        st.error(f"Failed to load {path}: {e}")
        return {}

# Load data
item_data = load_json(ITEM_DATA_PATH)
trade_data = load_json(TRADES_PATH)
if not item_data.get("Runes") or not trade_data:
    st.error("Could not load runes or trade data.")
    st.stop()

# Extract runes & icons
runes = list(item_data["Runes"].keys())
icons = {r: details.get("icon", "") for r, details in item_data["Runes"].items()}

# Parse a ratio string like "9:1" into float
def parse_ratio(ratio_str):
    try:
        a, b = ratio_str.split(":")
        return float(a) / float(b)
    except:
        return 0.0

# Build Ist-relative values (supporting reverse ratios)
def calculate_values():
    vals = {r: 0.0 for r in runes}
    for pair, info in trade_data.items():
        recommended = info.get("metadata", {}).get("recommended_ratio", "")
        v = parse_ratio(recommended)
        if v <= 0:
            continue

        if pair.startswith("Ist Rune:"):
            _, rune = pair.split(":", 1)
            if rune in vals:
                vals[rune] = v
        elif pair.endswith(":Ist Rune"):
            rune, _ = pair.split(":", 1)
            if rune in vals:
                vals[rune] = 1 / v
    return vals

values = calculate_values()

# Fraction formatter
def format_fraction(v):
    if v >= 1:
        return f"{v:.2f} Ist"
    if v > 0:
        inv = 1 / v
        return f"1/{inv:.1f} Ist"
    return "Unknown"

# Low-confidence checker
def is_low_conf(r):
    return trade_data.get(f"Ist Rune:{r}", {}).get("metadata", {}).get("low_confidence", False) or \
           trade_data.get(f"{r}:Ist Rune", {}).get("metadata", {}).get("low_confidence", False)

# Title
st.title("Diablo II Rune Values")

# Table heading
st.markdown("### Rune Values (relative to Ist Rune)")

# Table header
header = st.columns([1, 2, 2, 3])
header[0].markdown("**Icon**")
header[1].markdown("**Rune**")
header[2].markdown("**Decimal**")
header[3].markdown("**Fraction**")

# Rune table rows
for r in sorted(runes, key=lambda x: values.get(x, 0.0), reverse=True):
    v = values.get(r, 0.0)
    dec = f"{v:.2f}" if v > 0 else "N/A"
    frac = format_fraction(v)
    if is_low_conf(r):
        dec += "*"
        frac += "*"

    icon_file = BASE_DIR / icons.get(r, "")
    row = st.columns([1, 2, 2, 3])
    if icon_file.exists():
        row[0].image(str(icon_file), width=32)
    else:
        row[0].text("—")
    row[1].markdown(f"**{r}**")
    row[2].text(dec)
    row[3].text(frac)