# app.py

import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parent

st.set_page_config(page_title="D2R Trade Viewer", page_icon="🏺", layout="wide")

def load_trade_data(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        st.error(f"Invalid JSON in file: {file_path}")
        return None

def filter_trades(data, rune1=None, rune2=None, hours_back=24, limit=100, and_trades_only=False):
    if not data:
        return []

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours_back)
    trades = []

    rune1 = rune1.lower().strip() if rune1 else None
    rune2 = rune2.lower().strip() if rune2 else None

    for offer_rune, entries in data.get("Runes", {}).items():
        for entry in entries:
            try:
                updated = datetime.fromisoformat(entry["updated_at"].replace("Z", "+00:00"))
            except:
                continue

            if updated < cutoff:
                continue

            price_items = entry.get("price", [])
            ask_names = [p["name"].lower() for p in price_items]
            ask_text = ", ".join([f"{p['quantity']}x {p['name']}" for p in price_items])

            if and_trades_only and len(price_items) <= 1:
                continue

            offer_lower = offer_rune.lower()

            if rune1:
                if rune1 not in offer_lower and rune1 not in ask_names:
                    continue

            if rune2:
                if rune2 not in offer_lower and rune2 not in ask_names:
                    continue

            trades.append({
                "Time": updated.strftime("%m/%d %H:%M"),
                "Seller": entry["seller"],
                "Offering": f"{entry['quantity']}x {offer_rune}",
                "Asking": ask_text,
                "Type": "AND" if len(price_items) > 1 else "Single",
                "Raw_Time": updated
            })

    trades.sort(key=lambda x: x["Raw_Time"], reverse=True)
    return trades[:limit]

def main():
    st.title("🏺 D2R Trade Viewer")
    st.markdown("---")

    # Mode selection
    col1, col2 = st.columns(2)
    with col1:
        mode = st.radio("Mode", ["Softcore", "Hardcore"], index=0, horizontal=True)
    with col2:
        ladder = st.radio("Ladder", ["Non-Ladder", "Ladder"], index=0, horizontal=True)

    mode_str = "sc" if mode == "Softcore" else "hc"
    ladder_str = "nl" if ladder == "Non-Ladder" else "l"
    filename = f"raw_trades_pc_{mode_str}_{ladder_str}.json"
    file_path = str(ROOT_DIR / "data/raw" / filename)

    st.caption(f"Using JSON file: `{file_path}`")

    # Filters
    st.markdown("### Filters")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        rune1 = st.text_input("Rune #1 (required)", placeholder="e.g., Ber")
    with col2:
        rune2 = st.text_input("Rune #2 (optional, AND)", placeholder="e.g., Jah")
    with col3:
        hours_back = st.selectbox("Time Range:", [6, 12, 24, 48, 72, 168], index=2)
    with col4:
        and_only = st.checkbox("AND Trades Only")

    limit = st.slider("Max Results", 20, 2000, 100, step=10)

    if os.path.exists(file_path):
        data = load_trade_data(file_path)
        if data:
            trades = filter_trades(data, rune1, rune2, hours_back, limit, and_only)

            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Trades Found", len(trades))
            with col2:
                and_count = sum(1 for t in trades if t["Type"] == "AND")
                st.metric("AND Trades", and_count)
            with col3:
                if trades:
                    latest = max(trades, key=lambda x: x["Raw_Time"])
                    st.metric("Latest Trade", latest["Time"])

            if trades:
                display_trades = [{k: v for k, v in trade.items() if k != "Raw_Time"} for trade in trades]
                df = pd.DataFrame(display_trades)

                st.markdown("### Recent Trades")
                st.dataframe(df, use_container_width=True, hide_index=True)

                if st.button("📥 Export to CSV"):
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"d2r_trades_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )
            else:
                st.warning("No trades found matching your criteria.")
                st.markdown(f"**Filters used:**  \n"
                            f"• Rune #1: `{rune1 or '-'}`  \n"
                            f"• Rune #2: `{rune2 or '-'}`  \n"
                            f"• Time range: Last {hours_back}h  \n"
                            f"• AND Trades Only: `{and_only}`  \n"
                            f"• Limit: `{limit}`")

                # Show all trades (unfiltered) for debugging
                st.markdown("---")
                st.info("Showing all trades (unfiltered) for debugging:")
                all_trades = filter_trades(data, None, None, hours_back=168, limit=2000, and_trades_only=False)
                display_all = [{k: v for k, v in trade.items() if k != "Raw_Time"} for trade in all_trades]
                df_all = pd.DataFrame(display_all)
                st.dataframe(df_all, use_container_width=True, hide_index=True)
    else:
        st.warning("Data file not found. Please check your server selection.")

if __name__ == "__main__":
    main()