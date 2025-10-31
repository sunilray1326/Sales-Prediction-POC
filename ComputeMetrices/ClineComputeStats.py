import pandas as pd
import numpy as np
from datetime import datetime
import json

# Load data (adjust path if needed)
csv_path = r'Sales-Opportunity-Data-With-Notes.csv'
df = pd.read_csv(csv_path)

# Preprocess: Encode Won=1, Lost=0; Compute cycle time (days)
df['is_won'] = (df['deal_stage'] == 'Won').astype(int)
df['deal_engage_date'] = pd.to_datetime(df['deal_engage_date'], format='%d-%m-%Y')
df['deal_close_date'] = pd.to_datetime(df['deal_close_date'], format='%d-%m-%Y')
df['cycle_days'] = (df['deal_close_date'] - df['deal_engage_date']).dt.days

# Overall baseline
overall_win_rate = df['is_won'].mean()
print(f"Overall Win Rate: {overall_win_rate:.2%}")

# 1. Win Rate by categorical features
categorical_cols = ['product', 'product_series', 'account_sector', 'account_region', 'sales_rep']
stats = {'overall_win_rate': overall_win_rate}

for col in categorical_cols:
    win_rates = df.groupby(col)['is_won'].agg(['mean', 'count']).round(4)
    win_rates['lift'] = win_rates['mean'] / overall_win_rate
    win_rates.columns = ['win_rate', 'sample_size', 'lift']
    stats[col] = win_rates.to_dict()

# 2. Conditional: Example product + sector
df['product_sector'] = df['product'] + '_' + df['account_sector']
cond_win_rates = df.groupby('product_sector')['is_won'].mean()
stats['product_sector_win_rates'] = cond_win_rates.to_dict()

# 3. Average Revenue for Won deals
avg_revenue = df[df['is_won'] == 1].groupby('product')['revenue_from_deal'].mean()
stats['avg_revenue_by_product'] = avg_revenue.to_dict()

# 4. Correlation for numerical (e.g., sales_price vs is_won)
numerical_cols = ['sales_price', 'account_size', 'account_revenue']
correlations = {}
for col in numerical_cols:
    corr = df[col].corr(df['is_won'])
    correlations[col] = round(corr, 4)
stats['correlations'] = correlations

# 5. Cycle time
avg_cycle_won = df[df['is_won'] == 1]['cycle_days'].mean()
avg_cycle_lost = df[df['is_won'] == 0]['cycle_days'].mean()
stats['avg_cycle_days'] = {'won': round(avg_cycle_won, 1), 'lost': round(avg_cycle_lost, 1)}

# Save stats to JSON for LLM
with open('Cline_stats.json', 'w') as f:
    json.dump(stats, f, indent=4)

print("Baseline stats saved to baseline_stats.json")
print(stats)  # For console view
