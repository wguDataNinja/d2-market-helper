# filename: daily_report_html.py

import json
import base64
from datetime import datetime
from collections import Counter
from pytz import timezone
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# === CONFIG ===
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DATASETS = {
    "sc_l": str(DATA_DIR / "completed_trades_pc_sc_l.json"),
    "sc_nl": str(DATA_DIR / "completed_trades_pc_sc_nl.json"),
    "hc_l": str(DATA_DIR / "completed_trades_pc_hc_l.json"),
    "hc_nl": str(DATA_DIR / "completed_trades_pc_hc_nl.json"),
}
eastern = timezone("US/Eastern")
today_et = datetime.now(eastern).date()

# === LOAD ITEMS ===
with open(DATA_DIR / "item_ids.json") as f:
    item_data = json.load(f)

all_items = {}
for group in ["Runes", "Gems", "Misc"]:
    all_items.update(item_data.get(group, {}))

def parse_ratio(r):
    try:
        a, b = map(float, r.split(":"))
        return a / b if b else 0.0
    except:
        return 0.0

def generate_chart(timestamps):
    hours = [dt.hour for dt in timestamps]
    hour_counts = [Counter(hours)[h] for h in range(24)]
    plt.figure(figsize=(10, 4))
    plt.bar(range(24), hour_counts)
    plt.title("Trade Frequency by Hour (Eastern)")
    plt.xlabel("Hour of Day")
    plt.ylabel("Number of Trades")
    plt.xticks(range(24))
    plt.grid(axis="y")
    plt.tight_layout()
    buf = Path("chart.png")
    plt.savefig(buf)
    plt.close()
    with open(buf, "rb") as f:
        img64 = base64.b64encode(f.read()).decode()
    buf.unlink()
    return img64

def process_file(label, path):
    report_dir = ROOT_DIR / "reports" / label
    report_dir.mkdir(parents=True, exist_ok=True)
    with open(path) as f:
        data = json.load(f)

    values = {item: 0.0 for item in all_items}
    counts = {item: 0 for item in all_items}
    timestamps = []
    trade_counts_today = Counter()
    total_trade_counts = Counter()

    for item, info in data.items():
        for r in info.get("ratios", {}).values():
            ts, count = r.get("last_seen"), r.get("count", 0)
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(eastern)
                    timestamps.extend([dt] * count)
                    total_trade_counts[item] += count
                    if dt.date() == today_et:
                        trade_counts_today[item] += count
                except:
                    continue

        rec = info.get("metadata", {}).get("recommended_ratio", "")
        val = parse_ratio(rec)
        if val > 0:
            left, right = item.split(":")
            if left == "Ist Rune" and right in values:
                values[right] = val
                counts[right] = info["metadata"].get("total_trades", 0)
            elif right == "Ist Rune" and left in values:
                values[left] = 1 / val
                counts[left] = info["metadata"].get("total_trades", 0)

    # === HTML OUTPUT ===
    chart64 = generate_chart(timestamps)

    top_today_df = pd.DataFrame(trade_counts_today.most_common(10), columns=["Item", "Trades Today"])
    top_all_df = pd.DataFrame(total_trade_counts.most_common(20), columns=["Item", "Total Trades"])

    price_rows = []
    for item in all_items:
        v = values.get(item, 0)
        if v > 0:
            price_rows.append({
                "Item": item,
                "Ist Value": f"{v:.4f}",
                "Confidence": f"(based on {counts.get(item, 0)} trades)"
            })
    price_df = pd.DataFrame(price_rows)

    html = f"""
    <html>
    <head>
        <title>{label.upper()} Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            h2 {{ margin-top: 40px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            img {{ max-width: 100%; }}
        </style>
    </head>
    <body>
        <h1>{label.upper()} – Daily Trade Report</h1>
        <p>Generated: {datetime.now(eastern).strftime('%Y-%m-%d %H:%M:%S')}</p>
        <img src="data:image/png;base64,{chart64}" alt="Hourly Chart" />
        <h2>Top Traded Items Today</h2>
        {top_today_df.to_html(index=False)}
        <h2>Most Traded Items (All-Time)</h2>
        {top_all_df.to_html(index=False)}
        <h2>Item Prices (Relative to Ist Rune)</h2>
        {price_df.to_html(index=False)}
    </body>
    </html>
    """

    with open(report_dir / "report.html", "w") as f:
        f.write(html)

# === RUN ALL ===
for label, path in DATASETS.items():
    process_file(label, path)

print(f"✅ HTML reports generated in {ROOT_DIR / 'reports'}/{'{sc_l, sc_nl, hc_l, hc_nl}'}/report.html")