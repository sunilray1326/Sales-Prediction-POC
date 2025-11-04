import pandas as pd
import json
import re
from collections import defaultdict, Counter
from pathlib import Path

# Optional: Integrate Azure OpenAI for advanced extraction
# from openai import AzureOpenAI  # Assuming your setup
# openai_client = AzureOpenAI(...)  # Your config

# Load CSV
csv_path = Path("Sales-Opportunity-Data-With-Notes.csv")
df = pd.read_csv(csv_path)

# Keyword mapper for simple extraction (extend as needed)
keyword_categories = {
    "win_drivers": {
        "demo_success": ["demo", "workshop", "pilot approval", "benchmark report", "success stories"],
        "bundling_support": ["bundled", "support package", "training package", "multi-year"],
        "roi_evidence": ["ROI", "reduced stockouts", "cost ROI", "workflow automation"],
        "competitive_edge": ["competitive edge", "superior", "expanded to include"]
    },
    "loss_risks": {
        "pricing_high": ["pricing too high", "budget cut", "pilot conversion low"],
        "competitor": ["competitor", "opted for", "undercut", "free tool", "free tier"],
        "feature_mismatch": ["mismatched", "priorities shifted", "new director favored", "abandoned post"],
        "delays_stalls": ["delays", "stalled", "awaiting", "scheduling conflicts"]
    }
}

def extract_reason(note_entry, categories=keyword_categories):
    """Extract category if keywords match (case-insensitive). Returns dict or None."""
    note_lower = note_entry.lower()
    for cat_type, cat_dict in categories.items():
        for cat, keywords in cat_dict.items():
            if any(re.search(rf'\b{re.escape(kw)}\b', note_lower) for kw in keywords):
                return {"type": cat_type, "category": cat, "snippet": note_entry.strip()}
    return None

# Parse and extract
qual_stats = {
    "win_drivers": defaultdict(lambda: Counter()),
    "loss_risks": defaultdict(lambda: Counter()),
    "overall": {"total_won": 0, "total_lost": 0, "total_notes": 0},
    "segmented": {}  # By product/sector
}

for _, row in df.iterrows():
    stage = row["deal_stage"]
    notes = row["Notes"]
    if pd.isna(notes):
        continue
    
    entries = [e.strip() for e in notes.split("|") if e.strip()]
    stage_counter = qual_stats["win_drivers"] if stage == "Won" else qual_stats["loss_risks"]
    qual_stats["overall"]["total_notes"] += len(entries)
    qual_stats["overall"][f"total_{stage.lower()}"] += 1
    
    # Extract per entry
    for entry in entries:
        reason = extract_reason(entry)
        if reason:
            cat_type = reason["type"]
            category = reason["category"]
            stage_counter[category][reason["snippet"]] += 1  # Count unique snippets for examples
            
            # Segment by product/sector
            product = row["product"]
            sector = row["account_sector"]
            for seg in [product, sector]:
                if seg not in qual_stats["segmented"]:
                    qual_stats["segmented"][seg] = {"win_drivers": Counter(), "loss_risks": Counter()}
                qual_stats["segmented"][seg][cat_type][category] += 1

# Normalize to frequencies (e.g., % of deals mentioning category)
for cat_type in ["win_drivers", "loss_risks"]:
    denom_key = "total_won" if cat_type == "win_drivers" else "total_lost"
    denom = qual_stats["overall"][denom_key]
    for category, counter in qual_stats[cat_type].items():
        total_mentions = sum(counter.values())
        freq = total_mentions / denom if denom > 0 else 0
        qual_stats[cat_type][category] = {
            "frequency": freq,  # % of deals (approx, since mentions per deal)
            "count": total_mentions,
            "examples": list(counter.keys())[:3]  # Top 3 snippets
        }

# Save JSON
with open("qualitative_stats.json", "w") as f:
    json.dump(qual_stats, f, indent=2, default=str)

print("Generated qualitative_stats.json")
print(json.dumps(qual_stats, indent=2)[:500] + "...")  # Preview