📦 Traderie Rune Pipeline – Script & Data Overview
🗓️ Updated: May 21, 2025
🔧 Maintainer: buddy
📍 Purpose: Technical summary of all scripts, file formats, and data transformations for the Diablo II Traderie rune trading pipeline.

⸻

✅ Pipeline Steps Overview

1. 📥 fetch\_completed\_trades.py

Goal:
Fetch completed trades from the Traderiec API and save raw listings for all enabled combos.

Inputs:
• server\_configs.json — defines active combos via "slug" (e.g., pc\_sc\_nl)
• data/item\_data.json — contains item metadata and icon paths

Output:
• data/raw/raw\_trades\_<slug>.json
e.g., data/raw/raw\_trades\_pc\_sc\_nl.json

Output Format:

```json
{
  "Ist Rune": [
    {
      "completed": true,
      "amount": 1,
      "updated_at": "...",
      "price": [
        { "name": "Pul Rune", "quantity": 1 }
      ]
    }
  ]
}
```

⸻

2. 🧪 process\_completed\_trades.py

Goal:
Convert raw trade data into clean ratio statistics, with confidence heuristics and metadata.

Behavior:
• Loads raw listings by combo slug
• Skips multi-item and unknown trades (if configured)
• Aggregates base\:price ratios (e.g., Pul Rune\:Jah Rune)
• Computes trade counts, median, weighted average, and confidence flags
• Merges with existing data

Inputs:
• data/raw/raw\_trades\_<slug>.json — raw listings per combo
• data/item\_data.json — item metadata with IDs

Output:
• data/completed\_trades\_<slug>.json — processed stats

Output Format:

```json
{
  "Pul Rune:Jah Rune": {
    "ratios": {
      "10:1": { "count": 2, "last_seen": "..." }
    },
    "metadata": {
      "total_trades": 10,
      "most_common": "13:1",
      "median_ratio": 12.5,
      "weighted_avg": 12.29,
      "recommended_ratio": "13:1",
      "low_confidence": false,
      "last_updated": "..."
    }
  }
}
```

⸻

📁 Supporting Files
• server\_configs.json — combo definitions (root)
• data/item\_data.json — item metadata and icon paths

⸻

🖥️ 3. app.py — Rune Value Display App

Goal:
Visualize processed rune trade data using Streamlit, including icons and confidence indicators.

Behavior:
• Loads processed trade stats from data/completed\_trades\_<slug>.json
• Displays trade values relative to Ist (including reverse ratio)
• Marks low-confidence entries visually

Assets:
• icons/\*.png — local image assets
• data/item\_data.json — must include "icon": "icons/<name>.png" path for each rune

⸻

⚠️ Note:
Multi-item trades are skipped for FMV calculations unless bundle normalization is implemented and all components are trackable in data/item\_data.json.

⸻

🔄 Recent Updates – May 21, 2025

🆕 Relative Paths Adopted for GitHub Compatibility
• server\_configs.json (root)
• data/item\_data.json
• data/raw/raw\_trades\_<slug>.json
• data/completed\_trades\_<slug>.json

🛠️ Debug Mode: Multi-Item Trade Support (Temporarily Enabled)
• Multi-item trades were temporarily allowed in process\_completed\_trades.py to investigate why no updates appeared for pc\_hc\_nl.
• 🔍 Finding: Multi-item trades were dominant in recent fetches, but valid single-item trades were also present.
• ✅ After confirming the processor was working as expected, multi-item trade support was disabled again for production consistency.

📉 Trade Frequency by Server (Post-Debug Analysis)

Using inspect\_completed\_trade\_files.py, the pipeline now reports average trades per day by combo:

Server	Rune Pairs	Total Trades	Avg Trades/Day
pc\_sc\_l	403	5,047	168.23
pc\_sc\_nl	368	5,652	161.49
pc\_hc\_l	386	3,383	3.88
pc\_hc\_nl	125	849	1.17

