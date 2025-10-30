import pandas as pd
import json

df = pd.read_csv('Sales-Opportunity-Data.csv')

categorical_fields = ['sales_rep','product','product_series','account_sector','account_region']
numeric_fields = ['sales_price','account_size','account_revenue','revenue_from_deal']

overall_win_rate = (df['deal_stage'] == 'Won').mean()

all_metrics = {
    "overall_win_rate": overall_win_rate,
    "categorical": {},
    "numeric": {}
}

# Categorical field metrics
for field in categorical_fields:
    s = df.groupby(field)['deal_stage'].value_counts(normalize=True).unstack().fillna(0)
    s['count'] = df.groupby(field).size()
    if 'Won' in s:
        s['uplift'] = s['Won'] - overall_win_rate
    s = s.reset_index()
    records = s.to_dict(orient='records')
    all_metrics['categorical'][field] = records

# Numeric field metrics
for field in numeric_fields:
    stats = df.groupby('deal_stage')[field].agg(['count','mean','median','min','max','std']).reset_index()
    all_metrics['numeric'][field] = stats.to_dict(orient='records')

# Save all metrics to a single JSON file
with open('perplexity_metrics.json', 'w') as f:
    json.dump(all_metrics, f, indent=2)
