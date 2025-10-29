import pandas as pd
import json
from datetime import datetime, timedelta
import random

# Load data
df = pd.read_csv('Sales-Opportunity-Data.csv')  # Your full file

# Parse dates
def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%d-%m-%Y')
    except:
        return None

df['engage_date'] = df['deal_engage_date'].apply(parse_date)
df['close_date'] = df['deal_close_date'].apply(parse_date)

# Modular Config Loading from JSON
def load_config(file_name):
    try:
        with open(file_name, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {file_name} not found. Using empty dict.")
        return {}
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON in {file_name}.")
        return {}

# Load all configs
role_options = load_config('roles.json')
goal_options = load_config('goals.json')
mid_activities_options = load_config('mid_activities.json')
won_outcome_options = load_config('won_outcomes.json')
lost_outcome_options = load_config('lost_outcomes.json')

# Sub-functions (unchanged from previous modular version)
def select_role(sector, role_options):
    roles = role_options.get(sector, role_options.get('other', []))
    return random.choice(roles) if roles else 'Stakeholder'

def select_customer_goal(sector, series, product, goal_options):
    sector_goals = goal_options.get(sector, {'default': []})
    series_goals = sector_goals.get(series, sector_goals.get('default', []))
    goal = random.choice(series_goals) if series_goals else f"Discuss high-level goals with {product}."
    return goal.format(product=product) if isinstance(goal, str) and '{product}' in goal else goal

def get_mid_activities(sector, series, product, mid_options):
    sector_mids = mid_options.get(sector, {'default': []})
    series_mids = sector_mids.get(series, sector_mids.get('default', []))
    return [act.format(product=product) if isinstance(act, str) and '{product}' in act else act for act in series_mids]

def get_outcome_reasons(sector, series, product, stage, won_options, lost_options):
    if stage == 'Won':
        sector_out = won_options.get(sector, {'default': []})
        series_out = sector_out.get(series, sector_out.get('default', []))
        reasons = [r.format(product=product) if isinstance(r, str) and '{product}' in r else r for r in series_out]
        return random.choice(reasons) if reasons else "Closed won after successful negotiations."
    else:
        sector_out = lost_options.get(sector, {'default': []})
        series_out = sector_out.get(series, sector_out.get('default', []))
        reasons = [r.format(product=product) if isinstance(r, str) and '{product}' in r else r for r in series_out]
        return random.choice(reasons) if reasons else "Deal lost due to unresolved objections."

def generate_activity_dates(engage, close, num_activities):
    days = (close - engage).days
    return [engage + timedelta(days=(i * days // (num_activities + 1))) for i in range(num_activities)]

def build_notes(row):
    # Extract from row
    sector = row['account_sector'].lower()
    series = row['product_series'].lower()
    product = row['product']
    account = row['account_name']
    stage = row['deal_stage']
    sales_rep = row['sales_rep']
    engage = row['engage_date']
    close = row['close_date']
    
    # Select elements using loaded configs
    selected_role = select_role(sector, role_options)
    customer_goal = select_customer_goal(sector, series, product, goal_options)
    mid_acts = get_mid_activities(sector, series, product, mid_activities_options)
    outcome = get_outcome_reasons(sector, series, product, stage, won_outcome_options, lost_outcome_options)
    
    # Generate dates and notes
    num_activities = random.randint(3, 5)
    dates = generate_activity_dates(engage, close, num_activities)
    
    notes = []
    notes.append(f"{dates[0].strftime('%d-%m-%Y')}: Initial outreach by {sales_rep}. Meeting scheduled with {selected_role} ({account}). Discussed high-level customer's goal: {customer_goal}")
    
    for i in range(1, num_activities - 1):
        act = random.choice(mid_acts) if mid_acts else "Follow-up activity conducted."
        notes.append(f"{dates[i].strftime('%d-%m-%Y')}: {act}")
    
    notes.append(f"{dates[-1].strftime('%d-%m-%Y')}: {outcome}")
    
    return ' | '.join(notes)

# Main execution
df['Notes'] = df.apply(build_notes, axis=1)

# Drop the temporary datetime columns to avoid duplicates in output
df = df.drop(['engage_date', 'close_date'], axis=1)

df.to_csv('Sales-Opportunity-Data-With-Notes.csv', index=False)
print("Updated CSV saved as 'Sales-Opportunity-Data-With-Notes.csv'")